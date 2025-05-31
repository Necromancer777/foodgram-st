from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.response import Response
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    AvatarAddSerializer,
    RecipeShortSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
    SubscribedUserSerializer,
)
from django.shortcuts import get_object_or_404
from .models import Recipe, Ingredient, Favorite, ShoppingCart, User
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly
from django.http import FileResponse
from django.utils.timezone import now
from django.urls import reverse


class UserViewSet(DjoserUserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)

    def get_permissions(self):
        if self.action in ["me", "subscriptions", "subscribe", "avatar_update"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    serializer_action_classes = {
        "create": CustomUserCreateSerializer,
        "me": CustomUserSerializer,
        "subscriptions": SubscribedUserSerializer,
        "subscribe": SubscribedUserSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(
            self.action, super().get_serializer_class()
        )

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[permissions.IsAuthenticated],
    )
    def avatar_update(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = AvatarAddSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(
            {"status": "Аватар успешно удален"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        subscribed_authors = User.objects.filter(
            subscribers__follower=user
        ).prefetch_related("recipes")

        page = self.paginate_queryset(subscribed_authors)
        serializer = SubscribedUserSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="subscribe",
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            _, created = Subscription.objects.get_or_create(
                follower=user, author=author
            )
            if not created:
                return Response(
                    {
                        "errors": f"Вы уже подписаны на автора "
                                  f"{author.get_full_name()}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(author,
                                             context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(follower=user,
                                                   author=author).first()
        if not subscription:
            return Response(
                {
                    "errors": (
                        f"Вы не подписаны на пользователя "
                        f"{author.get_full_name()}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        return self._handle_toggle(request, Favorite)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_toggle(request, ShoppingCart)

    def _handle_toggle(self, request, model):
        recipe = self.get_object()
        user = request.user
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)

        if request.method == "POST":
            if not created:
                return Response(
                    {
                        "errors": (
                            f"{model._meta.verbose_name.capitalize()} "
                            "уже добавлен"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeShortSerializer(recipe,
                                               context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if created:
            return Response(
                {
                    "errors": (
                        f"{model._meta.verbose_name.capitalize()} "
                        "не найден"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def get_link(self, request, pk):
        url_path = reverse("recipes:short-link", args=[pk])
        full_url = request.build_absolute_uri(url_path)
        return Response(data={"short-link": full_url})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipes = {item.recipe for item in user.shoppingcart_relations.all()}
        ingredients = {}
        recipe_list = []

        for recipe in recipes:
            author_name = recipe.author.get_full_name()
            recipe_list.append(f"{recipe.name} — {author_name}")
            for item in recipe.recipe_ingredients.all():
                name = item.ingredient.name.capitalize()
                unit = item.ingredient.measurement_unit
                key = f"{name} ({unit})"
                ingredients[key] = ingredients.get(key, 0) + item.amount

        sorted_ingredients = dict(sorted(ingredients.items()))
        date = now().strftime("%d.%m.%Y")
        content = f"Список покупок (сформирован {date}):\n\n"

        for idx, (name, amount) in enumerate(sorted_ingredients.items(), 1):
            content += f"{idx}. {name}: {amount}\n"

        content += "\nРецепты:\n"
        for recipe in recipe_list:
            content += f"- {recipe}\n"

        from io import BytesIO
        file_like = BytesIO(content.encode("utf-8"))

        return FileResponse(
            file_like,
            as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain; charset=utf-8",
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None

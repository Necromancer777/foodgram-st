from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from djoser.views import UserViewSet
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
from io import BytesIO


class UserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in [
            "me",
            "avatar_update",
            "avatar_delete",
            "set_password",
            "subscriptions",
            "subscribe",
            "download_shopping_cart",
        ]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        elif self.action == "me":
            return CustomUserSerializer
        elif self.action in ["subscriptions", "subscribe"]:
            return SubscribedUserSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar_update(self, request):
        if request.method == "PUT":
            user = request.user
            avatar = request.data
            serializer = AvatarAddSerializer(user, data=avatar)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            user = request.user
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(
                {"status": "Аватар успешно удален"},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=["get"], url_path="subscriptions")
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

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created = Subscription.objects.get_or_create(follower=user,
                                                         author=author)[
                1
            ]
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны на данного автора"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(author,
                                             context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            subscription = Subscription.objects.filter(
                follower=user, author=author
            ).first()
            if not subscription:
                return Response(
                    {"errors": "Вы не подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(permissions.IsAuthenticated,),
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        return self._handle_toggle(
            request=request,
            model=Favorite,
            error_message="Рецепт уже в избранном",
            not_found_message="Рецепта нет в избранном",
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(permissions.IsAuthenticated,),
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_toggle(
            request=request,
            model=ShoppingCart,
            error_message="Рецепт уже в списке покупок",
            not_found_message="Рецепта нет в списке покупок",
        )

    def _handle_toggle(self, request, model, error_message, not_found_message):
        recipe = self.get_object()
        user = request.user
        obj = model.objects.filter(user=user, recipe=recipe)

        if request.method == "POST":
            if obj.exists():
                return Response(
                    {"errors": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not obj.exists():
                return Response(
                    {"errors": not_found_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
        url_path="get-link",
    )
    def get_link(self, request, pk):
        instance = self.get_object()
        url_path = reverse("recipes:short-link", args=[instance.id])
        full_url = request.build_absolute_uri(url_path)
        return Response(data={"short-link": full_url})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(permissions.IsAuthenticated,),
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user

        shopping_cart_qs = ShoppingCart.objects.filter(user=user)
        shopping_cart_items = shopping_cart_qs.select_related('recipe')
        recipes = [item.recipe for item in shopping_cart_items]

        ingredients = {}
        recipe_list = []

        for recipe in recipes:
            author_name = recipe.author.get_full_name()
            recipe_list.append(f'{recipe.name} — {author_name}')

            for item in recipe.recipe_ingredients.all():
                ingredient = item.ingredient
                name = ingredient.name.capitalize()
                unit = ingredient.measurement_unit
                key = f"{name} ({unit})"
                ingredients[key] = ingredients.get(key, 0) + item.amount

        date = now().strftime("%d.%m.%Y")
        content = f"Список покупок (сформирован {date}):\n\n"

        for idx, (name, amount) in enumerate(ingredients.items(), start=1):
            content += f"{idx}. {name}: {amount}\n"

        content += "\nРецепты:\n"
        for recipe in recipe_list:
            content += f"- {recipe}\n"

        file = BytesIO()
        file.write(content.encode("utf-8"))
        file.seek(0)

        return FileResponse(file, as_attachment=True,
                            filename="shopping_list.txt")


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None

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
    SubscriptionSerializer,
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Recipe, Ingredient, Favorite, ShoppingCart, User
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly


class CustomsUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return User.objects.all()

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
            return SubscriptionSerializer
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

        elif request.method == "DELETE":
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
            subscriber__follower=user
        ).prefetch_related("recipe_set")

        context = {"request": request}
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit and recipes_limit.isdigit():
            context["recipes_limit"] = int(recipes_limit)

        page = self.paginate_queryset(subscribed_authors)
        serializer = SubscriptionSerializer(page, many=True, context=context)
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

            if Subscription.objects.filter(follower=user,
                                           author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(follower=user, author=author)

            context = {"request": request}
            recipes_limit = request.query_params.get("recipes_limit")
            if recipes_limit and recipes_limit.isdigit():
                context["recipes_limit"] = int(recipes_limit)

            serializer = self.get_serializer(author, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
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
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly)
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
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe,
                                               context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"errors": "Рецепта нет в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(permissions.IsAuthenticated,),
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe,
                                               context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart_item.exists():
                return Response(
                    {"errors": "Рецепта нет в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
        url_path="get-link",
    )
    def get_link(self, request, pk):
        instance = self.get_object()

        url = f"{request.get_host()}/s/{instance.id}"

        return Response(data={"short-link": url})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(permissions.IsAuthenticated,),
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        recipes = [item.recipe for item in shopping_cart]

        ingredients = {}
        for recipe in recipes:
            for item in recipe.ingredientrecipe_set.all():
                ingredient = item.ingredient
                key = f"{ingredient.name} ({ingredient.measurement_unit})"
                if key in ingredients:
                    ingredients[key] += item.amount
                else:
                    ingredients[key] = item.amount

        content = "Список покупок:\n\n"
        for name, amount in ingredients.items():
            content += f"- {name}: {amount}\n"

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None

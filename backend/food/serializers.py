from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer
from .models import (
    User,
    Recipe,
    IngredientRecipe,
    Favorite,
    ShoppingCart,
    Ingredient)
import base64
from django.core.files.base import ContentFile
from users.models import Subscription
from django.core.validators import RegexValidator


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class AvatarAddSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')],
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    username = serializers.CharField(required=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return Subscription.objects.filter(follower=request.user,
                                           author=obj).exists()


class UserShortSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class RecipeListSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredientrecipe_set',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj).exists()


class CreateShortIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = CreateShortIngredientsSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'name', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Ингредиенты должны быть списком')
        if len(value) == 0:
            raise serializers.ValidationError(
                'Требуется хотя бы один ингредиент')

        ingredient_ids = [item.get('id') for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Найдены дубликаты ингредиентов')

        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True
            )
        )

        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f'Ингредиенты с id {missing_ids} не найдены'
            )

        for item in value:
            if (
                'amount' not in item
                or not isinstance(item['amount'], (int, float))
                or item['amount'] <= 0
            ):
                raise serializers.ValidationError(
                    'Каждый ингридиент должен быть в количестве не меньше нуля'
                )

        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )

        ingredient_instances = []
        for ingredient_data in ingredients_data:
            ingredient_instances.append(
                IngredientRecipe(
                    recipe=recipe,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount'],
                )
            )

        IngredientRecipe.objects.bulk_create(ingredient_instances)

        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                {'ingredients':
                 ['This field is required when updating a recipe']},
                code='required',
            )

        ingredients_data = validated_data.pop('ingredients')

        instance.ingredients.clear()
        ingredient_instances = []
        for ingredient_data in ingredients_data:
            ingredient_instances.append(
                IngredientRecipe(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount'],
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_instances)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipe_set.all()
        recipes_limit = self.context.get('recipes_limit')

        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]

        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.count()

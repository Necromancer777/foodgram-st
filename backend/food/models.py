from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Еденица измерения', max_length=64)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Картинка', upload_to='')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в минутах',
        validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField('Количество')

    class Meta:
        verbose_name = 'ингредиент и рецепт'
        verbose_name_plural = 'Ингредиенты и рецепты'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'Корзины'

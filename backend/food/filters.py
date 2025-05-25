import django_filters
from django_filters import rest_framework
from django_filters.rest_framework import FilterSet

from .models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = rest_framework.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, recipes_queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            filter_value = bool(int(value))
            if filter_value:
                return recipes_queryset.filter(favorite_relations__user=user)
            else:
                return recipes_queryset.exclude(favorite_relations__user=user)
        return recipes_queryset

    def filter_is_in_shopping_cart(self, recipes_queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            filter_value = bool(int(value))
            if filter_value:
                return recipes_queryset.filter(shoppingcart_relations__user=user)
            else:
                return recipes_queryset.exclude(shoppingcart_relations__user=user)
        return recipes_queryset

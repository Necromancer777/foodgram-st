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

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            filter_value = bool(int(value))
            if filter_value:
                return queryset.filter(favorite__user=user)
            else:
                return queryset.exclude(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            filter_value = bool(int(value))
            if filter_value:
                return queryset.filter(shoppingcart__user=user)
            else:
                return queryset.exclude(shoppingcart__user=user)
        return queryset

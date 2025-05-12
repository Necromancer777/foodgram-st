from django.contrib import admin
from django.db.models import Count
from .models import (
    User, Ingredient,
    Recipe, IngredientRecipe, Favorite, ShoppingCart
)
from users.models import Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name',
                                      'email', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'author')
    search_fields = ('follower__username', 'author__username')
    list_filter = ('follower', 'author')


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author',)
    inlines = (IngredientRecipeInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _favorites_count=Count('favorite')
        )

    def favorites_count(self, obj):
        return obj._favorites_count
    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = '_favorites_count'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')

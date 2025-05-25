from django.contrib import admin
from django.db.models import Count
from .models import (
    User, Ingredient, Recipe, IngredientRecipe,
    Favorite, ShoppingCart)
from users.models import Subscription
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe


class HasRecipesFilter(admin.SimpleListFilter):
    title = "наличие рецептов"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть рецепты"),
            ("no", "Нет рецептов"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "наличие подписок"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписки"),
            ("no", "Нет подписок"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscriber__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscriber__isnull=True)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "наличие подписчиков"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписчики"),
            ("no", "Нет подписчиков"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(followers__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(followers__isnull=True)
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "get_full_name",
        "email",
        "get_avatar_preview",
        "recipes_count",
        "subscriptions_count",
        "subscribers_count",
    )
    list_display_links = ("username", "email")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )
    readonly_fields = ("get_avatar_preview",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "avatar",
                    "get_avatar_preview",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                recipes_count=Count("recipes", distinct=True),
                subscriptions_count=Count("subscriber", distinct=True),
                followers_count=Count("followers", distinct=True),
            )
        )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    get_full_name.short_description = "ФИО"

    @mark_safe
    def get_avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="50" height="50" />'
        return "Нет аватара"

    get_avatar_preview.short_description = "Аватар"

    def recipes_count(self, obj):
        return obj.recipes_count

    recipes_count.admin_order_field = "recipes_count"
    recipes_count.short_description = "Рецепты"

    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    subscriptions_count.admin_order_field = "subscriptions_count"
    subscriptions_count.short_description = "Подписки"

    def subscribers_count(self, obj):
        return obj.followers_count

    subscribers_count.admin_order_field = "followers_count"
    subscribers_count.short_description = "Подписчики"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("follower", "author")
    search_fields = ("follower__username", "author__username")
    list_filter = ("follower", "author")


class CookingTimeFilter(admin.SimpleListFilter):
    title = "время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        cooking_times = Recipe.objects.values_list("cooking_time",
                                                   flat=True).order_by(
            "cooking_time"
        )

        if not cooking_times:
            return (
                ("<30", "быстрее 30 мин (0)"),
                ("30-60", "30-60 мин (0)"),
                (">60", "дольше 60 мин (0)"),
            )

        times = sorted(cooking_times)
        n = len(times)
        low = times[n // 3] if n > 0 else 30
        high = times[2 * n // 3] if n > 0 else 60

        fast = Recipe.objects.filter(cooking_time__lt=low).count()
        medium = Recipe.objects.filter(
            cooking_time__gte=low, cooking_time__lte=high
        ).count()
        slow = Recipe.objects.filter(cooking_time__gt=high).count()

        return (
            (f"<{low}", f"быстрее {low} мин ({fast})"),
            (f"{low}-{high}", f"{low}-{high} мин ({medium})"),
            (f">{high}", f"дольше {high} мин ({slow})"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if value.startswith("<"):
                time = int(value[1:])
                return queryset.filter(cooking_time__lt=time)
            elif value.startswith(">"):
                time = int(value[1:])
                return queryset.filter(cooking_time__gt=time)
            elif "-" in value:
                low, high = map(int, value.split("-"))
                return queryset.filter(cooking_time__gte=low,
                                       cooking_time__lte=high)
        return queryset


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cooking_time",
        "author",
        "favorites_count",
        "ingredients_list",
        "get_image_preview",
    )
    search_fields = ("name", "author__username")
    list_filter = (CookingTimeFilter, "author")
    inlines = (IngredientRecipeInline,)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _favorites_count=Count("favorite_relations"),
                _ingredients_count=Count("ingredients"),
            )
        )

    @mark_safe
    def ingredients_list(self, recipe):
        ingredients = recipe.ingredients.all()
        return "<br>".join(
            f"{ing.name} - {ing.measurement_unit}" for ing in ingredients[:5]
        ) + ("<br>..." if recipe._ingredients_count > 5 else "")

    ingredients_list.short_description = "Ингредиенты"

    @mark_safe
    def get_image_preview(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="50" height="50" />'
        return "Нет изображения"

    get_image_preview.short_description = "Изображение"

    @admin.display(description="В избранном", ordering="_favorites_count")
    def favorites_count(self, recipe):
        return recipe._favorites_count


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'наличие в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть в рецептах'),
            ('no', 'Нет в рецептах'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(ingredient_recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(ingredient_recipes__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', HasRecipesFilter)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _recipes_count=Count('ingredient_recipes', distinct=True)
        )

    @admin.display(
        description='Кол-во рецептов',
        ordering='_recipes_count'
    )
    def recipes_count(self, ingredient):
        return ingredient._recipes_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")
    list_filter = ("recipe", "ingredient")

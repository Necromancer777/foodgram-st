from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe
from .models import (User, Ingredient, Recipe, IngredientRecipe,
                     Favorite, ShoppingCart)
from users.models import Subscription
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class BooleanRelationFilter(admin.SimpleListFilter):
    title = ""
    parameter_name = ""
    relation_name = ""

    YES = "yes"
    NO = "no"
    LOOKUP_CHOICES = (
        (YES, "Да"),
        (NO, "Нет"),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        if value == self.YES:
            return queryset.filter(
                **{f"{self.relation_name}__isnull": False}
            ).distinct()
        if value == self.NO:
            return queryset.filter(**{f"{self.relation_name}__isnull": True})
        return queryset


class HasRecipesFilter(BooleanRelationFilter):
    title = "наличие рецептов"
    parameter_name = "has_recipes"
    relation_name = "recipes"


class HasSubscriptionsFilter(BooleanRelationFilter):
    title = "наличие подписок"
    parameter_name = "has_subscriptions"
    relation_name = "subscribers"


class HasSubscribersFilter(BooleanRelationFilter):
    title = "наличие подписчиков"
    parameter_name = "has_subscribers"
    relation_name = "followers"


class HasIngredientRecipesFilter(BooleanRelationFilter):
    title = "наличие в рецептах"
    parameter_name = "has_recipes"
    relation_name = "ingredient_recipes"


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
                subscriptions_count=Count("subscribers", distinct=True),
                followers_count=Count("subscribers", distinct=True),
            )
        )

    @admin.display(description="ФИО")
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="Аватар")
    def get_avatar_preview(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="50" height="50" />')
        return "Нет аватара"

    @admin.display(description="Рецепты", ordering="recipes_count")
    def recipes_count(self, obj):
        return obj.recipes_count

    @admin.display(description="Подписки", ordering="subscriptions_count")
    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    @admin.display(description="Подписчики", ordering="followers_count")
    def subscribers_count(self, obj):
        return obj.followers_count


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("follower", "author")
    search_fields = ("follower__username", "author__username")
    list_filter = ("follower", "author")


class CookingTimeFilter(admin.SimpleListFilter):
    title = "время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        times = list(
            Recipe.objects.values_list("cooking_time", flat=True).order_by(
                "cooking_time"
            )
        )

        if len(set(times)) < 3:
            return []

        n = len(times)
        low = times[n // 3]
        high = times[2 * n // 3]

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
                return queryset.filter(cooking_time__lt=int(value[1:]))
            elif value.startswith(">"):
                return queryset.filter(cooking_time__gt=int(value[1:]))
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
            )
        )

    @admin.display(description="Ингредиенты")
    def ingredients_list(self, recipe):
        ingredients = recipe.ingredients.all()
        return mark_safe(
            "<br>".join(f"{ing.name} - {ing.measurement_unit}" for ing in ingredients)
        )

    @admin.display(description="Изображение")
    def get_image_preview(self, recipe):
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="50" height="50" />')
        return "Нет изображения"

    @admin.display(description="В избранном", ordering="_favorites_count")
    def favorites_count(self, recipe):
        return recipe._favorites_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit", "recipes_count")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit", HasIngredientRecipesFilter)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(_recipes_count=Count("ingredient_recipes", distinct=True))
        )

    @admin.display(description="Кол-во рецептов", ordering="_recipes_count")
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

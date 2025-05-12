from django.urls import include, path
from rest_framework import routers
from .views import CustomsUserViewSet, RecipeViewSet, IngredientViewSet


router = routers.DefaultRouter()
router.register(r'users', CustomsUserViewSet, basename='user')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='recipe')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

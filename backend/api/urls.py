from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet, TagViewSet, IngredientViewSet, CustomUserViewSet

app_name = 'api'

router = SimpleRouter()
router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

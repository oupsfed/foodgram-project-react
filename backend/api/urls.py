from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet, TagViewSet

app_name = 'api'

router = SimpleRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
# router.register(
#     r'recipes/(?P<recipe_id>\d+)/favorite', FavoriteViewSet,
#     basename='reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

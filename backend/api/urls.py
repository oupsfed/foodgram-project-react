from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet

app_name = 'api'

router = SimpleRouter()
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

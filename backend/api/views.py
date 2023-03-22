import io

from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import viewsets, mixins, status

from recipes.serializers import RecipeSerializer, TagSerializer, RecipeCreateSerializer, IngredientCreateSerializer, \
    FavoriteRecipeSerializer
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.initial_data['author'] = request.user.pk
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='favorite',
    )
    def favorite(self, request, pk):
        recipe = Recipe.objects.get(pk=pk)
        is_exists = Favorite.objects.filter(
            recipe=recipe,
            user=request.user
        ).exists()
        if request.method == 'POST' and not is_exists:
            Favorite.objects.create(
                recipe=recipe,
                user=request.user
            )
            serializer = FavoriteRecipeSerializer(recipe, many=False)
            return Response(serializer.data, status.HTTP_201_CREATED)
        if request.method == 'DELETE' and is_exists:
            Favorite.objects.filter(
                recipe=recipe,
                user=request.user
            ).delete()
            return Response(
                'Рецепт успешно удален из избранного', status.HTTP_204_NO_CONTENT)
        return Response('Действие невозможно', status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        recipe = Recipe.objects.get(pk=pk)
        is_exists = ShoppingCart.objects.filter(
            recipe=recipe,
            user=request.user
        ).exists()
        if request.method == 'POST' and not is_exists:
            ShoppingCart.objects.create(
                recipe=recipe,
                user=request.user
            )
            serializer = FavoriteRecipeSerializer(recipe, many=False)
            return Response(serializer.data, status.HTTP_201_CREATED)
        if request.method == 'DELETE' and is_exists:
            ShoppingCart.objects.filter(
                recipe=recipe,
                user=request.user
            ).delete()
            return Response(
                'Рецепт успешно удален из избранного', status.HTTP_204_NO_CONTENT)
        return Response('Действие невозможно', status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        shopping_carts = ShoppingCart.objects.filter(user=request.user)
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Times', 'times.ttf', 'UTF-8'))
        p.setFont(psfontname='Times', size=24)
        p.drawString(220, 800, 'Список покупок')
        loc_y = 750
        for recipe in shopping_carts:
            ingredients = recipe.recipe.ingredients.values(
                "name",
                "measurement_unit",
                "ingredientrecipe__amount")
            p.setFont(psfontname='Times', size=18)
            p.drawString(100, loc_y,
                         f'Рецепт: {recipe.recipe.name}')
            loc_y -= 20
            num_of_ingredient = 1
            p.setFont(psfontname='Times', size=14)
            for ingredient in ingredients:
                p.drawString(100, loc_y,
                             f'{num_of_ingredient}.')
                p.drawString(120, loc_y,
                             f'{ingredient["name"]} ('
                             f'{ingredient["ingredientrecipe__amount"]} '
                             f'{ingredient["measurement_unit"]})')
                loc_y -= 20
                num_of_ingredient += 1
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='shopping_cart.pdf')

class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientCreateSerializer

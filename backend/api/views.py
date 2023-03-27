import csv
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import UserSubscription

from .paginators import RecipePagination
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeCreateSerializer, TagSerializer,
                          UserSubscribeSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет Пользователя с дополнительными URL:

    subscribe -- подписаться/отменить подписку на пользователя
    subscription -- посмотреть свои подписки.
    """
    pagination_class = RecipePagination

    @action(
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        following = User.objects.get(pk=id)
        user = request.user
        is_exists = UserSubscription.objects.filter(
            user=user,
            following=following
        ).exists()
        if request.method == 'POST' and not is_exists:
            UserSubscription.objects.create(
                user=user,
                following=following
            )
            serializer = UserSubscribeSerializer(
                following,
                many=False,
                context=self.request)
            return Response(serializer.data, status.HTTP_201_CREATED)
        if request.method == 'DELETE' and is_exists:
            UserSubscription.objects.filter(
                user=user,
                following=User.objects.get(pk=id)
            ).delete()
            return Response(
                'Пользователь успешно удален из подписок',
                status.HTTP_204_NO_CONTENT)
        return Response('Действие невозможно', status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(follower__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscribeSerializer(
                page,
                many=True,
                context=self.request
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscribeSerializer(
            page,
            many=True,
            context=self.request
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """
    Вьюсет рецептов.
    Разрешенные методы: GET, POST, PATCH, DELETE
    дополнительные URL:
    favorite -- Добавить/удалить рецепт из избранного.
    shopping_cart -- Добавить/удалить рецепт из списка покупок
    download_shopping_cart -- Скачать файл списка покупок.
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        tags = self.request.query_params.getlist('tags')
        author = self.request.query_params.get('author')
        if is_favorited == '1':
            self.queryset = self.queryset.filter(
                favorite__user=self.request.user
            )
        if is_in_shopping_cart == '1':
            self.queryset = self.queryset.filter(
                is_in_shopping_cart__user=self.request.user
            )

        if author:
            self.queryset = self.queryset.filter(
                author=author
            )
        if tags:
            self.queryset = self.queryset.filter(
                tags__slug__in=tags).distinct()
        return self.queryset

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
                'Рецепт успешно удален из избранного',
                status.HTTP_204_NO_CONTENT
            )
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
                'Рецепт успешно удален из избранного',
                status.HTTP_204_NO_CONTENT
            )
        return Response('Действие невозможно', status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        shopping_carts = ShoppingCart.objects.filter(user=request.user)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        response['Content-Type'] = 'charset=utf-8'
        writer = csv.writer(response)
        file_data = {}
        for recipe in shopping_carts:
            ingredients = recipe.recipe.ingredients.values(
                "name",
                "measurement_unit",
                "ingredientrecipe__amount")
            for ingredient in ingredients:
                name = ingredient['name']
                amount = ingredient['ingredientrecipe__amount']
                measurement_unit = ingredient['measurement_unit']
                if name in file_data:
                    file_data[name]['amount'] += amount
                else:
                    file_data[name] = {
                        'name': name,
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }
        for ingredient in file_data.values():
            writer.writerow([f'· '
                             f'{ingredient["name"]} '
                             f'({ingredient["measurement_unit"]}) - '
                             f'{ingredient["amount"]}'])
        return response


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny, ]


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [AllowAny, ]

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name is not None:
            name = unquote(name, 'cp1251')
            self.queryset = self.queryset.filter(name__startswith=name)
        return self.queryset

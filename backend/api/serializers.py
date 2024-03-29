import base64
import re

from django.core.files.base import ContentFile
from django.db.models import F
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag, TagRecipe)
from users.models import User, UserSubscription


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователей с дополнительными строками

    first_name: Имя пользователя
    last_name: Фамилия пользователя
    is_subscribed: Подписан ли request.user на пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return UserSubscription.objects.filter(
            user=self.context['request'].user,
            following=obj.id
        ).exists()


class UserRegistrationSerializer(UserCreateSerializer):
    """
    Сериализатор для регистрации пользователя

    убрано поле is_subscribed.
    """
    email = serializers.EmailField(max_length=254,
                                   required=True)
    username = serializers.RegexField(max_length=150,
                                      regex=r'^[\w.@+-]',
                                      required=True)
    first_name = serializers.CharField(max_length=150,
                                       required=True)
    last_name = serializers.CharField(max_length=150,
                                      required=True)

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
        )
        read_only_fields = (
            'id',
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError(
                'Данный email занят!')
        return value


class UserSubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователя с информацией по его рецептам

    recipes: краткая информация по рецептам
    recipes_count: количество созданных рецептом.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = ('id',
                            'recipe_count',
                            'recipes',
                            'is_subscribed')

    def get_is_subscribed(self, obj):
        return UserSubscription.objects.filter(
            user=self.context.userr,
            following=obj.id
        ).exists()

    def get_recipes(self, obj):
        recipes_limit = self.context.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.id).all()
        if recipes_limit is not None:
            recipes = recipes[:int(recipes_limit)]
        serializer = FavoriteRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=self.context.user).count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов для рецептов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для рецептов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецептов.
    Поля:
    author -- автор рецепта
    tags -- тэги рецепта
    ingredients -- ингредиенты рецепта
    is_favorited -- добавлен ли рецепт в избранное у request.user
    is_in_shopping_cart -- добавлен ли рецепт в список покупок у request.user
    name -- название рецепта
    image - логотип рецепта
    text -- описание рецепта
    cooking_time -- время приготовление рецепта.
    """
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author',
                            'is_favorited',
                            'is_in_shopping_cart',
                            'id')

    def get_is_favorited(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientrecipe__amount')
        )


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class TagCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления тэгов в рецепт."""

    class Meta:
        model = Tag
        fields = ('id',)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта."""
    tags = serializers.ListField(child=serializers.IntegerField())
    ingredients = serializers.ListField(child=IngredientCreateSerializer())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate_name(self, value):
        if not re.search('[a-zA-Zа-я-А-Я]+', value):
            raise ValidationError(
                'Название не может быть только из символов или цифр!')
        return value

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance,
                                      context=self.context)
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        tag_data = []
        ingredient_data = []
        for tag in tags:
            current_tag = Tag.objects.get(
                pk=tag
            )
            tag_data.append(
                TagRecipe(tag=current_tag, recipe=recipe)
            )
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id']
            )
            ingredient_data.append(IngredientRecipe(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount']
            ))
        TagRecipe.objects.bulk_create(tag_data)
        IngredientRecipe.objects.bulk_create(ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags = validated_data.pop('tags')
        tag_data = []
        ingredient_data = []
        for tag in tags:
            current_tag = Tag.objects.get(
                pk=tag
            )
            tag_data.append(
                TagRecipe(tag=current_tag, recipe=instance)
            )
        ingredients = validated_data.pop('ingredients')
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id']
            )
            ingredient_data.append(IngredientRecipe(
                ingredient=current_ingredient,
                recipe=instance,
                amount=ingredient['amount']
            ))
        TagRecipe.objects.bulk_create(tag_data)
        IngredientRecipe.objects.bulk_create(ingredient_data)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.save()
        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор с основной информацией по рецепту."""

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')

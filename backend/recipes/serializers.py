import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Tag, Recipe, Ingredient, IngredientRecipe, TagRecipe, Favorite, ShoppingCart
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault
from rest_framework.relations import SlugRelatedField

from users.serializers import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
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
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        is_favorite = Favorite.objects.filter(user=user, recipe=obj.id).exists()
        return is_favorite

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        is_shopping_cart = ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()
        return is_shopping_cart

    def get_ingredients(self, obj):
        return obj.ingredients.values('id',
                                      'name',
                                      'measurement_unit',
                                      amount=F('ingredientrecipe__amount'))


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id',)


class RecipeCreateSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance,
                                      context=self.context)
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            current_tag = Tag.objects.get(
                pk=tag
            )
            TagRecipe.objects.create(
                tag=current_tag, recipe=recipe
            )
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id']
            )
            IngredientRecipe.objects.create(
                ingredient=current_ingredient, recipe=recipe, amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags = validated_data.pop('tags')
        for tag in tags:
            current_tag = Tag.objects.get(
                pk=tag
            )
            TagRecipe.objects.create(
                tag=current_tag, recipe=instance
            )
        ingredients = validated_data.pop('ingredients')
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id']
            )
            IngredientRecipe.objects.create(
                ingredient=current_ingredient, recipe=instance, amount=ingredient['amount']
            )
        instance.name = instance.title = validated_data.get("name", instance.name)
        instance.save()
        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')

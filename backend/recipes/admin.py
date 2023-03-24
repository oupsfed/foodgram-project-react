from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe, Tag,
                     TagRecipe)

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(TagRecipe)
admin.site.register(IngredientRecipe)
admin.site.register(Favorite)

from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, Tag


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'user'
    )


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class RecipeTagInline(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'text',
        'author',
    )
    list_display_links = ('name',)
    list_filter = ('name', 'author', 'tags')
    inlines = (RecipeIngredientInline, RecipeTagInline)
    readonly_fields = ('in_favorite',)
    empty_value_display = '-пусто-'

    def in_favorite(self, recipe):
        return recipe.favorite.count()


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)

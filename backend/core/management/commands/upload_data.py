import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = 'Заполняет базу данных записями'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )
        with open('data/tags.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                Tag.objects.get_or_create(
                    name=row[0],
                    color=row[1],
                    slug=row[2]
                )

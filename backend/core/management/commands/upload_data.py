import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Заполняет базу данных записями'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                data = Ingredient(
                    name=row[0],
                    measurement_unit=row[1]
                )
                data.save()

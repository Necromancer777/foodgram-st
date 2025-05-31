import json
from django.core.management.base import BaseCommand
from food.models import Ingredient
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Load ingredients data from JSON file'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ingredients = [Ingredient(**item) for item in data]

                before_count = Ingredient.objects.count()
                Ingredient.objects.bulk_create(ingredients,
                                               ignore_conflicts=True)
                after_count = Ingredient.objects.count()
                created_count = after_count - before_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded {created_count} new ingredients'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading data from {file_path}: {e}')
            )

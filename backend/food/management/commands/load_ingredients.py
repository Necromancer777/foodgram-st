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
                ingredients = [
                    Ingredient(**item)
                    for item in json.load(f)
                ]
                Ingredient.objects.bulk_create(ingredients,
                                               ignore_conflicts=True)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded {len(ingredients)} ingredients from {file_path}'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading data from {file_path}: {e}')
            )

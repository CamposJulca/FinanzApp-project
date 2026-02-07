# backend/core/management/commands/seed_classification_tree.py

from django.core.management.base import BaseCommand
from core.models import (
    TransactionType,
    TransactionCategory,
    TransactionSubCategory,
)


CLASSIFICATION_TREE = {
    "Ingreso fijo": {
        "Salarios": [
            "Salario Daniel",
            "Salario Karla",
        ],
    },
    "Ingreso variable": {
        "Ingresos ocasionales": [
            "Bonificaciones",
            "Freelance",
            "Otros ingresos",
        ],
    },
    "Egreso fijo": {
        "Vivienda": [
            "Arriendo",
            "Administración",
        ],
        "Servicios públicos": [
            "Energía",
            "Agua",
            "Gas",
            "Internet",
        ],
    },
    "Egreso variable": {
        "Alimentación": [
            "Mercado",
            "Restaurantes",
        ],
        "Transporte": [
            "Gasolina",
            "Transporte público",
        ],
        "Ocio": [
            "Entretenimiento",
            "Suscripciones",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed inicial del árbol de clasificación financiera (TransactionType → Category → SubCategory)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Iniciando seed del árbol de clasificación...\n"))

        for type_name, categories in CLASSIFICATION_TREE.items():
            t_type, created = TransactionType.objects.get_or_create(
                name=type_name
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Tipo creado: {type_name}"))

            for category_name, subcategories in categories.items():
                category, cat_created = TransactionCategory.objects.get_or_create(
                    type=t_type,
                    name=category_name,
                )
                if cat_created:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✔ Categoría creada: {category_name}")
                    )

                for subcat_name in subcategories:
                    subcat, sub_created = TransactionSubCategory.objects.get_or_create(
                        category=category,
                        name=subcat_name,
                    )
                    if sub_created:
                        self.stdout.write(
                            self.style.SUCCESS(f"    ✔ Subcategoría creada: {subcat_name}")
                        )

        self.stdout.write(self.style.SUCCESS("\n✅ Seed del árbol completado correctamente"))


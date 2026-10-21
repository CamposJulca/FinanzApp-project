from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import (
    Household,
    Account,
    Transaction,
    TransactionCategory,
    TransactionSubCategory,
    TransactionType,
)
from datetime import datetime
from django.utils.timezone import make_aware

from decimal import Decimal


class Command(BaseCommand):
    help = "Carga inicial de datos financieros para el usuario camposmarin"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🚀 Iniciando carga de datos CamposMarin"))

        # 1. Crear usuarios
        user, created = User.objects.get_or_create(
            username="camposmarin",
            defaults={"email": "camposmarin@finanzapp.local"}
        )
        if created:
            user.set_password("camposmarin2026")
            user.save()
            self.stdout.write(self.style.SUCCESS("✔ Usuario camposmarin creado"))
        else:
            self.stdout.write("ℹ Usuario camposmarin ya existe")

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@finanzapp.local", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("admin2026")
            admin.save()
            self.stdout.write(self.style.SUCCESS("✔ Usuario admin creado"))
        else:
            self.stdout.write("ℹ Usuario admin ya existe")

        # 2. Household
        household, _ = Household.objects.get_or_create(name="Campos Marin")
        household.members.add(user)
        self.stdout.write(self.style.SUCCESS("✔ Household Campos Marin listo"))

        # 3. Cuenta base
        account, _ = Account.objects.get_or_create(
            user=user,
            name="Caja General",
            defaults={"saldo_real": Decimal("0")}
        )

        # 4. Categorías base
        categories = {}
        for code, label in [("IN", "Ingreso"), ("EX", "Egreso")]:
            tx_type, _ = TransactionType.objects.get_or_create(
                name=label,
                defaults={"description": label}
            )
            category, _ = TransactionCategory.objects.get_or_create(
                type=tx_type,
                name=label
            )
            categories[code] = category

        # 5. Dataset (normalizado)
        raw_data = [
            ("Efectivo", "IN", 65000000, "2026-01-23", ""),
            ("Plan Complementario", "EX", 9501435, "2026-01-24", ""),
            ("Gafas Saldo", "EX", 665881, "2026-01-24", ""),
            ("Ingreso", "IN", 12424000, "2026-01-26", ""),
            ("Pago hipoteca", "EX", 3675344, "2026-01-25", ""),
            ("Carnes", "EX", 50000, "2026-02-05", ""),
        ]

        # 6. Inserción de transacciones
        created_count = 0
        for item, tipo, valor, fecha, descripcion in raw_data:
            created_at = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
            subcategory, _ = TransactionSubCategory.objects.get_or_create(
                category=categories[tipo],
                name=item
            )
            Transaction.objects.create(
                user=user,
                account=account,
                subcategory=subcategory,
                amount=Decimal(valor),
                description=descripcion,
                created_at=created_at,
                fecha_efectiva=created_at.date(),

            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"✔ {created_count} transacciones cargadas"))
        self.stdout.write(self.style.SUCCESS("✅ Carga inicial completada"))

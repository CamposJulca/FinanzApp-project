import csv
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.models import Transaction, Account


class Command(BaseCommand):
    help = "Carga transacciones históricas desde un CSV"

    def handle(self, *args, **options):
        self.stdout.write("📥 Iniciando carga de transacciones desde CSV...")

        csv_path = Path("backend/data/camposmarin_historico.csv")

        if not csv_path.exists():
            self.stderr.write(f"❌ No se encontró el archivo CSV en {csv_path}")
            return

        # ⚠️ Ajusta el username si luego cambias de usuario
        user = User.objects.first()
        if not user:
            self.stderr.write("❌ No existe ningún usuario en el sistema")
            return

        account, _ = Account.objects.get_or_create(
            user=user,
            name="Cuenta Principal",
            defaults={"balance": Decimal("0")}
        )

        created = 0
        skipped = 0

        with csv_path.open(encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for idx, row in enumerate(reader, start=1):
                try:
                    descripcion = row["descripcion"].strip() if row["descripcion"] else row["item"].strip()
                    tipo = row["tipo"].strip()
                    valor = Decimal(row["valor"])
                    fecha_raw = row["fecha"].strip()

                    fecha = (
                        datetime.strptime(fecha_raw, "%d/%m/%Y")
                        if fecha_raw
                        else datetime.now()
                    )

                    # Idempotencia básica
                    exists = Transaction.objects.filter(
                        user=user,
                        account=account,
                        amount=valor,
                        description=descripcion,
                        created_at=fecha
                    ).exists()

                    if exists:
                        skipped += 1
                        continue

                    Transaction.objects.create(
                        user=user,
                        account=account,
                        amount=valor if tipo == "I" else -valor,
                        description=descripcion,
                        created_at=fecha
                    )

                    created += 1

                except Exception as e:
                    self.stderr.write(f"⚠️ Error en fila {idx}: {e}")

        self.stdout.write("✅ Carga finalizada")
        self.stdout.write(f"   ✔ Registros creados: {created}")
        self.stdout.write(f"   ⏭ Registros omitidos: {skipped}")


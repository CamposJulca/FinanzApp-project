import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path
from django.utils import timezone


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

from core.models import Transaction, Account


class Command(BaseCommand):
    help = "Carga transacciones históricas desde un CSV (idempotente)"

    def handle(self, *args, **options):
        self.stdout.write("📥 Iniciando carga de transacciones desde CSV...")

        # =========================
        # Ruta correcta en Docker
        # =========================
        csv_path = Path(settings.BASE_DIR) / "data" / "camposmarin_historico.csv"

        if not csv_path.exists():
            self.stderr.write(f"❌ No se encontró el archivo CSV en: {csv_path}")
            return

        # =========================
        # Usuario base
        # =========================
        user = User.objects.first()
        if not user:
            self.stderr.write("❌ No existe ningún usuario en el sistema")
            return

        # =========================
        # Cuenta base
        # =========================
        account, _ = Account.objects.get_or_create(
            user=user,
            name="Cuenta Principal",
            defaults={"balance": Decimal("0")}
        )

        created = 0
        skipped = 0
        errors = 0

        # =========================
        # Lectura CSV
        # =========================
        with csv_path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            required_fields = {
                "item", "tipo", "valor", "fecha", "descripcion"
            }

            if not required_fields.issubset(reader.fieldnames):
                self.stderr.write(
                    f"❌ El CSV no tiene las columnas requeridas: {required_fields}"
                )
                return

            for idx, row in enumerate(reader, start=2):  # 2 = header + 1
                try:
                    # -------------------------
                    # Descripción
                    # -------------------------
                    descripcion = (
                        row.get("descripcion", "").strip()
                        or row.get("item", "").strip()
                    )

                    if not descripcion:
                        raise ValueError("Descripción vacía")

                    # -------------------------
                    # Tipo
                    # -------------------------
                    tipo = row.get("tipo", "").strip().upper()
                    if tipo not in {"I", "E"}:
                        raise ValueError(f"Tipo inválido: {tipo}")

                    # -------------------------
                    # Valor
                    # -------------------------
                    try:
                        valor = Decimal(row.get("valor", "0"))
                    except InvalidOperation:
                        raise ValueError(f"Valor inválido: {row.get('valor')}")

                    if valor <= 0:
                        raise ValueError("Valor debe ser mayor a 0")

                    monto = valor if tipo == "I" else -valor

                    # -------------------------
                    # Fecha
                    # -------------------------
                    fecha_raw = row.get("fecha", "").strip()
                    if fecha_raw:
                        naive_date = datetime.strptime(fecha_raw, "%d/%m/%Y")
                        fecha = timezone.make_aware(naive_date)
                    else:
                        fecha = timezone.now()

                    # -------------------------
                    # Idempotencia
                    # -------------------------
                    exists = Transaction.objects.filter(
                        user=user,
                        account=account,
                        amount=monto,
                        description=descripcion,
                        created_at=fecha
                    ).exists()

                    if exists:
                        skipped += 1
                        continue

                    # -------------------------
                    # Creación
                    # -------------------------
                    Transaction.objects.create(
                        user=user,
                        account=account,
                        amount=monto,
                        description=descripcion,
                        created_at=fecha
                    )

                    created += 1

                except Exception as e:
                    errors += 1
                    self.stderr.write(
                        f"⚠️ Fila {idx} ignorada → {e}"
                    )

        # =========================
        # Resumen
        # =========================
        self.stdout.write("✅ Carga finalizada")
        self.stdout.write(f"   ✔ Registros creados : {created}")
        self.stdout.write(f"   ⏭ Registros omitidos: {skipped}")
        self.stdout.write(f"   ⚠️ Errores          : {errors}")

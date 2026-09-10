from django.db import migrations, models


def map_existing(apps, schema_editor):
    """Reinterpreta las filas antiguas (name) como (tipo, subtipo)."""
    TransactionType = apps.get_model("core", "TransactionType")
    for t in TransactionType.objects.all():
        old = (getattr(t, "name", "") or "").strip().lower()
        t.tipo = "EGRESO" if old.startswith("egreso") else "INGRESO"
        # No existía subtipo antes: se asume VARIABLE (el usuario reorganiza luego).
        if not getattr(t, "subtipo", ""):
            t.subtipo = "VARIABLE"
        t.save(update_fields=["tipo", "subtipo"])


def seed_pairs(apps, schema_editor):
    """Garantiza que existan exactamente las 4 parejas del dominio."""
    TransactionType = apps.get_model("core", "TransactionType")
    parejas = [
        ("INGRESO", "FIJO"),
        ("INGRESO", "VARIABLE"),
        ("EGRESO", "FIJO"),
        ("EGRESO", "VARIABLE"),
    ]
    for tipo, subtipo in parejas:
        if not TransactionType.objects.filter(tipo=tipo, subtipo=subtipo).exists():
            TransactionType.objects.create(tipo=tipo, subtipo=subtipo, description="")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_transaction_registered_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactiontype",
            name="tipo",
            field=models.CharField(
                choices=[("INGRESO", "INGRESO"), ("EGRESO", "EGRESO")],
                default="INGRESO",
                max_length=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="transactiontype",
            name="subtipo",
            field=models.CharField(
                choices=[("FIJO", "FIJO"), ("VARIABLE", "VARIABLE")],
                default="VARIABLE",
                max_length=10,
            ),
            preserve_default=False,
        ),
        # 1) Mapear filas existentes ANTES de tocar la constraint de `name`.
        migrations.RunPython(map_existing, noop),
        # 2) Quitar `name` (y con él su UNIQUE) para poder sembrar sin colisión.
        migrations.RemoveField(
            model_name="transactiontype",
            name="name",
        ),
        # 3) Sembrar las parejas faltantes ya sin la constraint de `name`.
        migrations.RunPython(seed_pairs, noop),
        migrations.AlterModelOptions(
            name="transactiontype",
            options={"ordering": ("tipo", "subtipo")},
        ),
        migrations.AlterUniqueTogether(
            name="transactiontype",
            unique_together={("tipo", "subtipo")},
        ),
    ]

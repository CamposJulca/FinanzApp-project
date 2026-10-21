from django.db import migrations


def rename_fixed_house(apps, schema_editor):
    TransactionCategory = apps.get_model("core", "TransactionCategory")
    TransactionCategory.objects.filter(
        type__tipo="EGRESO",
        type__subtipo="FIJO",
        name="CASA",
    ).update(name="VIVIENDA")


def restore_fixed_house(apps, schema_editor):
    TransactionCategory = apps.get_model("core", "TransactionCategory")
    TransactionCategory.objects.filter(
        type__tipo="EGRESO",
        type__subtipo="FIJO",
        name="VIVIENDA",
    ).update(name="CASA")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_transaction_fecha_efectiva_not_null_and_indexes"),
    ]

    operations = [
        migrations.RunPython(rename_fixed_house, restore_fixed_house),
    ]

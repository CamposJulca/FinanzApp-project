from django.db import migrations, models
import django.db.models.deletion


def assign_household(apps, schema_editor):
    Household = apps.get_model("core", "Household")
    Transaction = apps.get_model("core", "Transaction")
    if not Transaction.objects.exists():
        return
    households = list(Household.objects.values_list("pk", flat=True))
    if len(households) != 1:
        raise RuntimeError("El backfill de Transaction.household exige exactamente un Household.")
    Transaction.objects.filter(household__isnull=True).update(household_id=households[0])


class Migration(migrations.Migration):
    dependencies = [("core", "0013_transaction_household_nullable")]
    operations = [
        migrations.RunPython(assign_household, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaction",
            name="household",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                to="core.household",
            ),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["household", "fecha_efectiva"], name="core_transa_househo_451047_idx"),
        ),
    ]

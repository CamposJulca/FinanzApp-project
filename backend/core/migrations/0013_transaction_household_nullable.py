from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0012_transaction_metadata_fields")]
    operations = [
        migrations.AddField(
            model_name="transaction",
            name="household",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                to="core.household",
            ),
        ),
    ]

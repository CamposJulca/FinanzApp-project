import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_transactiontype_tipo_subtipo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="currency",
            field=models.CharField(default="COP", max_length=3),
        ),
        migrations.CreateModel(
            name="Transfer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("fecha", models.DateField()),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfers_created", to=settings.AUTH_USER_MODEL)),
                ("from_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfers_out", to="core.account")),
                ("household", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.household")),
                ("to_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfers_in", to="core.account")),
            ],
        ),
        migrations.AddField(
            model_name="transaction",
            name="fecha_efectiva",
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name="transaction",
            name="transfer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="legs", to="core.transfer"),
        ),
    ]

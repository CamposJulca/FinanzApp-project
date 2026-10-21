from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_rename_fixed_house_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactionsubcategory",
            name="frecuencia",
            field=models.CharField(
                choices=[
                    ("MENSUAL", "MENSUAL"),
                    ("ANUAL", "ANUAL"),
                    ("ESPORADICO", "ESPORADICO"),
                ],
                default="ESPORADICO",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="cubre_desde",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transaction",
            name="cubre_hasta",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transaction",
            name="inserted_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="inserted_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(cubre_desde__isnull=True, cubre_hasta__isnull=True)
                    | models.Q(cubre_desde__isnull=False, cubre_hasta__isnull=False)
                ),
                name="transaction_coverage_dates_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(cubre_desde__isnull=True)
                    | models.Q(cubre_hasta__gte=models.F("cubre_desde"))
                ),
                name="transaction_coverage_dates_order",
            ),
        ),
    ]

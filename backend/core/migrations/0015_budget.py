import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models
from django.db.models import F, Func, Value
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0014_backfill_transaction_household")]
    operations = [
        BtreeGistExtension(),
        migrations.CreateModel(
            name="Budget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("currency", models.CharField(default="COP", max_length=3)),
                ("valid_from", models.DateField()),
                ("valid_to", models.DateField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.transactioncategory")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="auth.user")),
                ("household", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="budgets", to="core.household")),
            ],
            options={"ordering": ("category__name", "-valid_from")},
        ),
        migrations.AddConstraint(model_name="budget", constraint=models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="budget_amount_positive")),
        migrations.AddConstraint(model_name="budget", constraint=models.CheckConstraint(condition=models.Q(("valid_to__isnull", True), ("valid_to__gte", F("valid_from")), _connector="OR"), name="budget_validity_order")),
        migrations.AddConstraint(
            model_name="budget",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                name="budget_no_overlapping_validity",
                expressions=[
                    (F("household"), django.contrib.postgres.fields.ranges.RangeOperators.EQUAL),
                    (F("category"), django.contrib.postgres.fields.ranges.RangeOperators.EQUAL),
                    (Func(F("valid_from"), F("valid_to"), Value("[]"), function="DATERANGE"), django.contrib.postgres.fields.ranges.RangeOperators.OVERLAPS),
                ],
            ),
        ),
    ]

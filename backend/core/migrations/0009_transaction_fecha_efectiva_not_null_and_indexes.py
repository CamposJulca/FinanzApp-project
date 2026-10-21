from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0008_populate_fecha_efectiva")]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="fecha_efectiva",
            field=models.DateField(),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["user", "fecha_efectiva"], name="core_transa_user_id_55575f_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["subcategory", "fecha_efectiva"], name="core_transa_subcate_489cb8_idx"),
        ),
    ]

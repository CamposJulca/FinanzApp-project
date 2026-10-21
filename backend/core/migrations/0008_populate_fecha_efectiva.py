from django.db import migrations
from django.utils import timezone
from zoneinfo import ZoneInfo


BOGOTA = ZoneInfo("America/Bogota")


def populate_fecha_efectiva(apps, schema_editor):
    Transaction = apps.get_model("core", "Transaction")
    for movement in Transaction.objects.filter(fecha_efectiva__isnull=True).iterator():
        movement.fecha_efectiva = timezone.localdate(movement.created_at, BOGOTA)
        movement.save(update_fields=["fecha_efectiva"])


class Migration(migrations.Migration):
    dependencies = [("core", "0010_normalize_historical_created_at")]

    operations = [
        migrations.RunPython(populate_fecha_efectiva, migrations.RunPython.noop),
    ]

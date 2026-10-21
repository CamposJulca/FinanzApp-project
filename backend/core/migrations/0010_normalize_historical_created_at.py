from datetime import datetime, time, timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.db import migrations


BOGOTA = ZoneInfo("America/Bogota")
UTC = datetime_timezone.utc


def normalize_historical_midnights(apps, schema_editor):
    Transaction = apps.get_model("core", "Transaction")
    for movement in Transaction.objects.all().iterator():
        stored_utc = movement.created_at.astimezone(UTC)
        if stored_utc.timetz().replace(tzinfo=None) != time.min:
            continue
        movement.created_at = datetime.combine(stored_utc.date(), time.min, BOGOTA)
        movement.save(update_fields=["created_at"])


def restore_utc_midnights(apps, schema_editor):
    Transaction = apps.get_model("core", "Transaction")
    normalized_utc_time = time(5, 0)
    for movement in Transaction.objects.all().iterator():
        stored_utc = movement.created_at.astimezone(UTC)
        if stored_utc.timetz().replace(tzinfo=None) != normalized_utc_time:
            continue
        movement.created_at = datetime.combine(stored_utc.date(), time.min, UTC)
        movement.save(update_fields=["created_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_account_currency_transfer_and_transaction_fields"),
    ]

    operations = [
        migrations.RunPython(
            normalize_historical_midnights,
            restore_utc_midnights,
        ),
    ]

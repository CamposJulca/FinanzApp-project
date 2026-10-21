from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.utils import timezone

from .models import (
    Account,
    Household,
    Transaction,
    Transfer,
)


class TransferModelTests(TestCase):
    def setUp(self):
        self.owner_from = User.objects.create_user("owner-from")
        self.owner_to = User.objects.create_user("owner-to")
        self.household = Household.objects.create(name="Casa")
        self.household.members.add(self.owner_from, self.owner_to)
        self.from_account = Account.objects.create(user=self.owner_from, name="Origen")
        self.to_account = Account.objects.create(user=self.owner_to, name="Destino")

    def transfer(self, **overrides):
        values = {
            "household": self.household,
            "from_account": self.from_account,
            "to_account": self.to_account,
            "amount": Decimal("250.00"),
            "fecha": datetime(2026, 10, 20).date(),
            "created_by": self.owner_from,
        }
        values.update(overrides)
        return Transfer(**values)

    def test_save_rejects_same_account_on_both_sides(self):
        with self.assertRaises(ValidationError):
            self.transfer(to_account=self.from_account).save()

    def test_save_rejects_non_positive_amount(self):
        with self.assertRaises(ValidationError):
            self.transfer(amount=Decimal("0")).save()

    def test_save_rejects_account_owner_outside_household(self):
        outsider = User.objects.create_user("outsider")
        outsider_account = Account.objects.create(user=outsider, name="Externa")

        with self.assertRaises(ValidationError):
            self.transfer(to_account=outsider_account).save()

    def test_account_referenced_by_transfer_is_protected(self):
        self.transfer().save()

        with self.assertRaises(ProtectedError):
            self.from_account.delete()

    def test_admin_does_not_allow_adding_or_changing_transfers(self):
        transfer = self.transfer()
        transfer.save()
        request = RequestFactory().get("/admin/")
        request.user = User.objects.create_superuser("admin", "admin@example.com", "pw")
        model_admin = admin.site._registry[Transfer]

        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, transfer))

    def test_admin_does_not_allow_changing_or_deleting_a_transfer_leg(self):
        transfer = self.transfer()
        transfer.save()
        leg = Transaction.objects.create(
            user=self.owner_from,
            account=self.from_account,
            transfer=transfer,
            amount=Decimal("-250.00"),
            description="Leg",
            created_at=timezone.now(),
            fecha_efectiva=transfer.fecha,
        )
        request = RequestFactory().get("/admin/")
        request.user = User.objects.create_superuser("admin", "admin@example.com", "pw")
        model_admin = admin.site._registry[Transaction]

        self.assertFalse(model_admin.has_change_permission(request, leg))
        self.assertFalse(model_admin.has_delete_permission(request, leg))


class FechaEfectivaMigrationTests(TransactionTestCase):
    migrate_from = [("core", "0007_account_currency_transfer_and_transaction_fields")]
    migrate_to = [("core", "0008_populate_fecha_efectiva")]

    @property
    def executor(self):
        return MigrationExecutor(connection)

    def setUp(self):
        super().setUp()
        executor = self.executor
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        UserModel = old_apps.get_model("auth", "User")
        AccountModel = old_apps.get_model("core", "Account")
        TransactionModel = old_apps.get_model("core", "Transaction")

        user = UserModel.objects.create(username="historico")
        account = AccountModel.objects.create(user=user, name="Histórica")
        TransactionModel.objects.create(
            user=user,
            account=account,
            amount=Decimal("10.00"),
            description="Anterior",
            created_at=timezone.make_aware(datetime(2026, 8, 4, 17, 35)),
        )
        for transaction_id in (128, 130, 135, 136, 137):
            TransactionModel.objects.create(
                id=transaction_id,
                user=user,
                account=account,
                amount=Decimal("-1.00"),
                description=f"Límite {transaction_id}",
                created_at=datetime(
                    2026, 9, 1, 0, 0, tzinfo=datetime_timezone.utc
                ),
            )

        executor = self.executor
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_populates_date_from_created_at(self):
        TransactionModel = self.apps.get_model("core", "Transaction")
        transaction = TransactionModel.objects.get(description="Anterior")

        self.assertEqual(transaction.fecha_efectiva.isoformat(), "2026-08-04")

    def test_midnight_utc_history_keeps_calendar_date_after_normalization(self):
        TransactionModel = self.apps.get_model("core", "Transaction")
        transactions = TransactionModel.objects.filter(
            pk__in=(128, 130, 135, 136, 137)
        ).order_by("pk")

        self.assertEqual(list(transactions.values_list("pk", flat=True)), [128, 130, 135, 136, 137])
        for transaction in transactions:
            self.assertEqual(transaction.created_at.hour, 5)
            self.assertEqual(transaction.fecha_efectiva.isoformat(), "2026-09-01")

    def test_historical_midnight_normalization_is_reversible(self):
        executor = self.executor
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        TransactionModel = old_apps.get_model("core", "Transaction")

        transaction = TransactionModel.objects.get(pk=128)

        self.assertEqual(transaction.created_at.hour, 0)
        self.assertEqual(transaction.created_at.date().isoformat(), "2026-09-01")

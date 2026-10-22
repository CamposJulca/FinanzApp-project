from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import IntegrityError, transaction as db_transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.utils import timezone

from .models import (
    Account,
    Budget,
    Household,
    Transaction,
    TransactionCategory,
    TransactionSubCategory,
    TransactionType,
    Transfer,
)


class BudgetModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("budget-owner")
        self.household = Household.objects.create(name="Hogar presupuesto")
        self.household.members.add(self.user)
        expense_type = TransactionType.objects.get(tipo="EGRESO", subtipo="FIJO")
        income_type = TransactionType.objects.get(tipo="INGRESO", subtipo="FIJO")
        self.expense = TransactionCategory.objects.create(type=expense_type, name="Tope")
        self.income = TransactionCategory.objects.create(type=income_type, name="No tope")

    def budget(self, **overrides):
        values = {
            "household": self.household,
            "category": self.expense,
            "amount": Decimal("1000.00"),
            "valid_from": datetime(2026, 10, 1).date(),
            "created_by": self.user,
        }
        values.update(overrides)
        return Budget(**values)

    def test_rejects_income_category(self):
        with self.assertRaises(ValidationError):
            self.budget(category=self.income).save()

    def test_rejects_non_positive_amount_and_reversed_dates(self):
        with self.assertRaises(ValidationError):
            self.budget(amount=Decimal("0")).save()
        with self.assertRaises(ValidationError):
            self.budget(valid_to=datetime(2026, 9, 30).date()).save()

    def test_database_rejects_overlapping_validity(self):
        self.budget().save()
        with self.assertRaises(IntegrityError), db_transaction.atomic():
            Budget.objects.bulk_create([
                self.budget(valid_from=datetime(2026, 10, 31).date())
            ])


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
            household=self.household,
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
        HouseholdModel = old_apps.get_model("core", "Household")
        TransactionModel = old_apps.get_model("core", "Transaction")

        user = UserModel.objects.create(username="historico")
        HouseholdModel.objects.create(name="Hogar histórico")
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


class PresupuestoFase1MigrationTests(TransactionTestCase):
    migrate_from = [("core", "0009_transaction_fecha_efectiva_not_null_and_indexes")]
    migrate_to = [("core", "0012_transaction_metadata_fields")]

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
        HouseholdModel = old_apps.get_model("core", "Household")
        TypeModel = old_apps.get_model("core", "TransactionType")
        CategoryModel = old_apps.get_model("core", "TransactionCategory")
        TransactionModel = old_apps.get_model("core", "Transaction")

        user = UserModel.objects.create(username="historico-fase1")
        HouseholdModel.objects.create(name="Hogar histórico fase 1")
        account = AccountModel.objects.create(user=user, name="Histórica")
        TransactionModel.objects.create(
            user=user,
            account=account,
            amount=Decimal("10.00"),
            description="Antes de inserted_at",
            created_at=timezone.now(),
            fecha_efectiva=datetime(2026, 10, 20).date(),
        )

        fixed_expense, _ = TypeModel.objects.get_or_create(
            tipo="EGRESO", subtipo="FIJO", defaults={"description": ""}
        )
        variable_expense, _ = TypeModel.objects.get_or_create(
            tipo="EGRESO", subtipo="VARIABLE", defaults={"description": ""}
        )
        CategoryModel.objects.filter(type=fixed_expense, name="VIVIENDA").delete()
        CategoryModel.objects.update_or_create(type=fixed_expense, name="CASA")
        CategoryModel.objects.update_or_create(type=variable_expense, name="CASA")
        for number in range(1, 19):
            CategoryModel.objects.update_or_create(
                type=variable_expense,
                name=f"CATEGORIA {number:02d}",
            )

        executor = self.executor
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_rename_makes_category_names_unique(self):
        CategoryModel = self.apps.get_model("core", "TransactionCategory")
        TypeModel = self.apps.get_model("core", "TransactionType")
        fixed_expense = TypeModel.objects.get(tipo="EGRESO", subtipo="FIJO")

        self.assertTrue(
            CategoryModel.objects.filter(type=fixed_expense, name="VIVIENDA").exists()
        )
        names = list(CategoryModel.objects.values_list("name", flat=True))
        self.assertEqual(len(names), 20)
        self.assertEqual(len(names), len(set(names)))

    def test_preexisting_transactions_keep_inserted_at_null(self):
        TransactionModel = self.apps.get_model("core", "Transaction")

        transaction = TransactionModel.objects.get(description="Antes de inserted_at")

        self.assertIsNone(transaction.inserted_at)

    def test_rename_is_reversible(self):
        executor = self.executor
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        CategoryModel = old_apps.get_model("core", "TransactionCategory")
        TypeModel = old_apps.get_model("core", "TransactionType")
        fixed_expense = TypeModel.objects.get(tipo="EGRESO", subtipo="FIJO")

        self.assertTrue(
            CategoryModel.objects.filter(type=fixed_expense, name="CASA").exists()
        )
        self.assertFalse(
            CategoryModel.objects.filter(type=fixed_expense, name="VIVIENDA").exists()
        )


class PresupuestoFase1ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("fase1-model")
        self.account = Account.objects.create(user=self.user, name="Cuenta")
        self.household = Household.objects.create(name="Hogar fase 1")
        self.household.members.add(self.user)
        self.type = TransactionType.objects.get(tipo="EGRESO", subtipo="FIJO")
        self.category = TransactionCategory.objects.create(type=self.type, name="VIVIENDA")

    def transaction(self, **overrides):
        values = {
            "user": self.user,
            "account": self.account,
            "household": self.household,
            "amount": Decimal("-100.00"),
            "description": "Pago",
            "created_at": timezone.now(),
            "fecha_efectiva": datetime(2026, 10, 20).date(),
        }
        values.update(overrides)
        return Transaction(**values)

    def test_subcategory_frequency_defaults_to_esporadico(self):
        subcategory = TransactionSubCategory.objects.create(
            category=self.category,
            name="Reparación",
        )

        self.assertEqual(subcategory.frecuencia, "ESPORADICO")

    def test_new_transaction_populates_inserted_at(self):
        transaction = self.transaction()
        transaction.save()

        self.assertIsNotNone(transaction.inserted_at)

    def test_coverage_dates_must_both_be_present(self):
        transaction = self.transaction(cubre_desde=datetime(2026, 10, 1).date())

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_coverage_end_must_not_precede_start(self):
        transaction = self.transaction(
            cubre_desde=datetime(2026, 10, 31).date(),
            cubre_hasta=datetime(2026, 10, 1).date(),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()


class TransactionHouseholdMigrationTests(TransactionTestCase):
    migrate_from = [("core", "0013_transaction_household_nullable")]
    migrate_to = [("core", "0014_backfill_transaction_household")]

    @property
    def executor(self):
        return MigrationExecutor(connection)

    def setUp(self):
        super().setUp()
        executor = self.executor
        executor.migrate(self.migrate_from)
        apps = executor.loader.project_state(self.migrate_from).apps
        UserModel = apps.get_model("auth", "User")
        HouseholdModel = apps.get_model("core", "Household")
        AccountModel = apps.get_model("core", "Account")
        TransactionModel = apps.get_model("core", "Transaction")
        user = UserModel.objects.create(username="backfill-264")
        household = HouseholdModel.objects.create(name="Único")
        account = AccountModel.objects.create(user=user, name="Histórica")
        TransactionModel.objects.bulk_create([
            TransactionModel(
                user=user, account=account, amount=Decimal("-1.00"),
                description=f"Histórico {number}", created_at=timezone.now(),
                fecha_efectiva=datetime(2026, 10, 1).date(),
            ) for number in range(264)
        ])
        executor = self.executor
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps
        self.household_id = household.pk

    def tearDown(self):
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_all_264_transactions_receive_the_only_household(self):
        TransactionModel = self.apps.get_model("core", "Transaction")
        self.assertEqual(TransactionModel.objects.count(), 264)
        self.assertEqual(TransactionModel.objects.filter(household_id=self.household_id).count(), 264)
        self.assertFalse(TransactionModel.objects.filter(household__isnull=True).exists())

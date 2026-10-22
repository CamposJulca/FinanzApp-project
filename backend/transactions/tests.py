from datetime import date, datetime, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

from core.models import (
    Account,
    Household,
    Transaction,
    TransactionCategory,
    TransactionSubCategory,
    TransactionType,
    Transfer,
)
from transactions.services import get_account_balances
from transactions.views import _resolve_transactions, STRATEGY_UNCLASSIFY


class LegacyTransactionPayloadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("legacy")
        self.household = Household.objects.create(name="Hogar legacy")
        self.household.members.add(self.user)
        self.account = Account.objects.create(user=self.user, name="Cuenta")
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_create_without_fecha_efectiva_derives_it_from_created_at(self):
        created_at = timezone.make_aware(datetime(2026, 9, 12, 14, 30))

        response = self.client.post(
            "/api/transactions/",
            {
                "account": self.account.id,
                "amount": "125.00",
                "type": "ingreso",
                "description": "Payload anterior",
                "created_at": created_at.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        transaction = Transaction.objects.get(description="Payload anterior")
        self.assertEqual(transaction.fecha_efectiva.isoformat(), "2026-09-12")

    def test_create_without_any_date_uses_current_local_date(self):
        response = self.client.post(
            "/api/transactions/",
            {
                "account": self.account.id,
                "amount": "50.00",
                "type": "ingreso",
                "description": "Sin fechas",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        transaction = Transaction.objects.get(description="Sin fechas")
        self.assertEqual(transaction.fecha_efectiva, timezone.localdate())
        self.assertIsNotNone(transaction.created_at)

    def test_create_accepts_valid_coverage_period(self):
        response = self.client.post(
            "/api/transactions/",
            {
                "account": self.account.id,
                "amount": "125.00",
                "type": "egreso",
                "description": "Seguro anual",
                "fecha_efectiva": "2026-10-20",
                "cubre_desde": "2026-10-01",
                "cubre_hasta": "2027-09-30",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        transaction = Transaction.objects.get(description="Seguro anual")
        self.assertEqual(transaction.cubre_desde, date(2026, 10, 1))
        self.assertEqual(transaction.cubre_hasta, date(2027, 9, 30))
        self.assertIsNotNone(transaction.inserted_at)
        self.assertIn("inserted_at", response.data)

    def test_create_rejects_incomplete_coverage_period(self):
        response = self.client.post(
            "/api/transactions/",
            {
                "account": self.account.id,
                "amount": "125.00",
                "type": "egreso",
                "description": "Periodo incompleto",
                "fecha_efectiva": "2026-10-20",
                "cubre_desde": "2026-10-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("cubre_hasta", response.data)

    def test_inserted_at_is_read_only(self):
        response = self.client.post(
            "/api/transactions/",
            {
                "account": self.account.id,
                "amount": "50.00",
                "type": "ingreso",
                "description": "Auditoría",
                "inserted_at": "2000-01-01T00:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        transaction = Transaction.objects.get(description="Auditoría")
        self.assertNotEqual(transaction.inserted_at.year, 2000)


class AccountCurrencyApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("accounts-user")
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_create_uses_cop_and_currency_can_be_updated(self):
        created = self.client.post(
            "/api/transactions/accounts/",
            {"name": "Banco", "saldo_real": "0"},
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["currency"], "COP")
        updated = self.client.patch(
            f"/api/transactions/accounts/{created.data['id']}/",
            {"currency": "PEN"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["currency"], "PEN")


class SubcategoryFrequencyApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("frequency-user")
        self.client = APIClient()
        self.client.force_login(self.user)
        self.type = TransactionType.objects.get(tipo="EGRESO", subtipo="FIJO")
        self.category = TransactionCategory.objects.create(
            type=self.type,
            name="VIVIENDA API",
        )

    def test_frequency_is_exposed_and_can_be_updated(self):
        created = self.client.post(
            "/api/transactions/subcategories/",
            {
                "name": "Administración",
                "category": self.category.id,
                "frecuencia": "MENSUAL",
            },
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["frecuencia"], "MENSUAL")
        updated = self.client.patch(
            f"/api/transactions/subcategories/{created.data['id']}/",
            {"frecuencia": "ANUAL"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["frecuencia"], "ANUAL")


class TransferApiTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user("creator")
        self.recipient = User.objects.create_user("recipient")
        self.household = Household.objects.create(name="Hogar")
        self.household.members.add(self.creator, self.recipient)
        self.from_account = Account.objects.create(user=self.creator, name="Origen")
        self.to_account = Account.objects.create(user=self.recipient, name="Destino")
        self.client = APIClient()
        self.client.force_login(self.creator)
        self.payload = {
            "household": self.household.id,
            "from_account": self.from_account.id,
            "to_account": self.to_account.id,
            "amount": "350.25",
            "fecha": "2026-10-20",
            "description": "Entre cuentas",
        }

    def test_create_transfer_generates_two_legs_with_account_owners_and_signs(self):
        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 201, response.data)
        transfer = Transfer.objects.get()
        self.assertEqual(transfer.created_by, self.creator)
        self.assertEqual(transfer.legs.count(), 2)
        outgoing = transfer.legs.get(account=self.from_account)
        incoming = transfer.legs.get(account=self.to_account)
        self.assertEqual(outgoing.user, self.creator)
        self.assertEqual(incoming.user, self.recipient)
        self.assertEqual(outgoing.household, self.household)
        self.assertEqual(incoming.household, self.household)
        self.assertEqual(outgoing.amount, Decimal("-350.25"))
        self.assertEqual(incoming.amount, Decimal("350.25"))
        self.assertIsNone(outgoing.subcategory)
        self.assertIsNone(incoming.subcategory)
        self.assertEqual(outgoing.fecha_efectiva, date(2026, 10, 20))
        expected_midnight = timezone.make_aware(
            datetime.combine(date(2026, 10, 20), time.min),
            timezone.get_current_timezone(),
        )
        self.assertEqual(outgoing.created_at, expected_midnight)
        self.assertEqual(incoming.created_at, expected_midnight)

    def test_delete_transfer_deletes_both_legs(self):
        created = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )
        transfer_id = created.data["id"]

        response = self.client.delete(f"/api/transactions/transfers/{transfer_id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Transfer.objects.filter(pk=transfer_id).exists())
        self.assertEqual(Transaction.objects.filter(transfer_id=transfer_id).count(), 0)

    def test_force_delete_account_referenced_by_transfer_is_blocked(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")

        response = self.client.delete(
            f"/api/transactions/accounts/{self.from_account.id}/?force=true"
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Account.objects.filter(pk=self.from_account.id).exists())
        self.assertEqual(Transfer.objects.count(), 1)

    def test_create_rejects_user_outside_household(self):
        outsider = User.objects.create_user("outsider")
        self.client.force_login(outsider)

        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transfer.objects.count(), 0)

    def test_create_rejects_account_owner_outside_household(self):
        outsider = User.objects.create_user("external-owner")
        outside_account = Account.objects.create(user=outsider, name="Externa")
        self.payload["to_account"] = outside_account.id

        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transfer.objects.count(), 0)

    def test_create_rejects_same_account(self):
        self.payload["to_account"] = self.from_account.id

        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_create_rejects_non_positive_amount(self):
        self.payload["amount"] = "0"

        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_transaction_patch_cannot_mutate_a_transfer_leg(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")
        leg = Transaction.objects.get(transfer__isnull=False, amount__lt=0)

        response = self.client.patch(
            f"/api/transactions/{leg.id}/",
            {"amount": "1.00", "account": self.to_account.id},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("/transfers/", response.data["error"])
        leg.refresh_from_db()
        self.assertEqual(leg.amount, Decimal("-350.25"))
        self.assertEqual(leg.account, self.from_account)

    def test_transaction_put_cannot_mutate_a_transfer_leg(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")
        leg = Transaction.objects.get(transfer__isnull=False, amount__lt=0)

        response = self.client.put(
            f"/api/transactions/{leg.id}/",
            {
                "amount": "1.00",
                "account": self.from_account.id,
                "description": "Alterada",
                "created_at": "2026-10-20T00:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_transaction_delete_cannot_remove_one_transfer_leg(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")
        leg = Transaction.objects.get(transfer__isnull=False, amount__lt=0)

        response = self.client.delete(f"/api/transactions/{leg.id}/")

        self.assertEqual(response.status_code, 409)
        self.assertIn("/transfers/", response.data["error"])
        self.assertEqual(leg.transfer.legs.count(), 2)

    def test_transfer_endpoint_does_not_allow_editing(self):
        created = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        patch_response = self.client.patch(
            f"/api/transactions/transfers/{created.data['id']}/",
            {"amount": "1.00"},
            format="json",
        )
        put_response = self.client.put(
            f"/api/transactions/transfers/{created.data['id']}/",
            self.payload,
            format="json",
        )

        self.assertEqual(patch_response.status_code, 405)
        self.assertEqual(put_response.status_code, 405)

    def test_transfer_leg_with_no_subcategory_does_not_run_branch_sign_validation(self):
        response = self.client.post(
            "/api/transactions/transfers/", self.payload, format="json"
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(
            Transaction.objects.filter(transfer__isnull=False, subcategory__isnull=True).count(),
            2,
        )

    def test_summary_excludes_transfer_legs_from_income_and_expense(self):
        Transaction.objects.create(
            user=self.creator,
            household=self.household,
            account=self.from_account,
            amount=Decimal("1000.00"),
            description="Ingreso real",
            created_at=timezone.now(),
            fecha_efectiva=date(2026, 10, 20),
        )
        Transaction.objects.create(
            user=self.creator,
            household=self.household,
            account=self.from_account,
            amount=Decimal("-100.00"),
            description="Gasto real",
            created_at=timezone.now(),
            fecha_efectiva=date(2026, 10, 20),
        )
        self.client.post("/api/transactions/transfers/", self.payload, format="json")

        response = self.client.get("/api/transactions/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ingresos"], 1000.0)
        self.assertEqual(response.data["egresos"], 100.0)
        self.assertEqual(response.data["neto_transferencias"], -350.25)
        self.assertEqual(response.data["saldo_contable"], 549.75)
        self.assertEqual(
            response.data["saldo_contable"],
            response.data["ingresos"]
            - response.data["egresos"]
            + response.data["neto_transferencias"],
        )

    def test_account_balance_keeps_transfer_legs(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")

        balances = {row["account_id"]: row["balance"] for row in get_account_balances(self.creator)}

        self.assertEqual(balances[self.from_account.id], -350.25)

    def test_unclassify_strategy_does_not_mutate_transfer_legs(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")
        movement_type = TransactionType.objects.get(tipo="EGRESO", subtipo="FIJO")
        category = TransactionCategory.objects.create(type=movement_type, name="Casa")
        subcategory = TransactionSubCategory.objects.create(category=category, name="Renta")
        leg = Transaction.objects.get(transfer__isnull=False, amount__lt=0)
        Transaction.objects.filter(pk=leg.pk).update(subcategory=subcategory)
        request = APIRequestFactory().delete(
            "/", {"on_transactions": STRATEGY_UNCLASSIFY}
        )
        request.user = self.creator

        error, result = _resolve_transactions(subcategory, request)

        self.assertIsNone(error)
        self.assertEqual(result["transactions_affected"], 0)
        leg.refresh_from_db()
        self.assertEqual(leg.subcategory, subcategory)

    def test_transaction_list_identifies_transfer_legs(self):
        self.client.post("/api/transactions/transfers/", self.payload, format="json")

        response = self.client.get("/api/transactions/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["transactions"][0]["transfer"])

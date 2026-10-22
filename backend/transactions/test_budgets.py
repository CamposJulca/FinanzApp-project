from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    Account, Budget, Household, Transaction, TransactionCategory,
    TransactionSubCategory, TransactionType,
)
from transactions.budgets import prorated_amount


class ProratedAmountTests(TestCase):
    def test_real_quarterly_payment_is_prorated_by_inclusive_days(self):
        transaction = Transaction(
            amount=Decimal("-2004000.00"),
            cubre_desde=date(2026, 10, 1),
            cubre_hasta=date(2026, 12, 31),
        )
        amount = prorated_amount(transaction, date(2026, 10, 1), date(2026, 10, 31))
        self.assertEqual(amount, Decimal("675260.87"))

    def test_proration_rounds_to_cents_and_returns_zero_without_intersection(self):
        transaction = Transaction(
            amount=Decimal("-100.00"),
            cubre_desde=date(2026, 1, 1),
            cubre_hasta=date(2026, 1, 3),
        )
        self.assertEqual(
            prorated_amount(transaction, date(2026, 1, 1), date(2026, 1, 1)),
            Decimal("33.33"),
        )
        self.assertEqual(
            prorated_amount(transaction, date(2026, 2, 1), date(2026, 2, 28)),
            Decimal("0.00"),
        )


class BudgetApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("budget-api")
        self.household = Household.objects.create(name="Principal")
        self.household.members.add(self.user)
        self.account = Account.objects.create(user=self.user, name="Cuenta")
        fixed = TransactionType.objects.get(tipo="EGRESO", subtipo="FIJO")
        variable = TransactionType.objects.get(tipo="EGRESO", subtipo="VARIABLE")
        income = TransactionType.objects.get(tipo="INGRESO", subtipo="FIJO")
        self.category = TransactionCategory.objects.create(type=fixed, name="VIVIENDA TEST")
        self.unbudgeted = TransactionCategory.objects.create(type=variable, name="MERCADO TEST")
        self.income_category = TransactionCategory.objects.create(type=income, name="SALARIO TEST")
        self.subcategory = TransactionSubCategory.objects.create(
            category=self.category, name="ADMINISTRACION TEST"
        )
        self.client = APIClient()
        self.client.force_login(self.user)

    def post_budget(self, **overrides):
        payload = {
            "household": self.household.id,
            "category": self.category.id,
            "amount": "1000000.00",
            "currency": "COP",
            "valid_from": "2026-10-01",
            "note": "Inicial",
        }
        payload.update(overrides)
        return self.client.post("/api/transactions/budgets/", payload, format="json")

    def test_write_requires_explicit_household_and_rejects_income(self):
        missing = self.post_budget(household=None)
        income = self.post_budget(category=self.income_category.id)
        self.assertEqual(missing.status_code, 400)
        self.assertIn("household", missing.data)
        self.assertEqual(income.status_code, 400)
        self.assertIn("category", income.data)

    def test_future_post_closes_previous_and_preserves_history(self):
        self.assertEqual(self.post_budget().status_code, 201)
        response = self.post_budget(amount="1200000.00", valid_from="2026-11-01")
        self.assertEqual(response.status_code, 201, response.data)
        rows = list(Budget.objects.order_by("valid_from"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].valid_to, date(2026, 10, 31))
        self.assertIsNone(rows[1].valid_to)

    def test_read_with_multiple_households_requires_selection(self):
        other = Household.objects.create(name="Segundo")
        other.members.add(self.user)
        response = self.client.get("/api/transactions/budgets/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data["households"]), 2)

    def create_expense(self, amount, effective, **coverage):
        return Transaction.objects.create(
            user=self.user, household=self.household, account=self.account,
            subcategory=self.subcategory, amount=Decimal(amount),
            description="Gasto", created_at=timezone.make_aware(datetime(2025, 1, 1)),
            fecha_efectiva=effective, **coverage,
        )

    def test_consumption_uses_effective_date_and_lists_unbudgeted_category(self):
        self.post_budget()
        self.create_expense("-310000.00", date(2026, 10, 10))
        response = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-01&hasta=2026-10-31")
        self.assertEqual(response.status_code, 200, response.data)
        rows = {row["categoria_id"]: row for row in response.data["categorias"]}
        self.assertEqual(Decimal(rows[self.category.id]["consumido"]), Decimal("310000.00"))
        self.assertIsNone(rows[self.unbudgeted.id]["tope"])

    def test_consumption_prorates_by_coverage_even_when_effective_date_is_outside(self):
        self.create_expense(
            "-2004000.00", date(2026, 9, 30),
            cubre_desde=date(2026, 10, 1), cubre_hasta=date(2026, 12, 31),
        )
        response = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-01&hasta=2026-10-31")
        row = next(x for x in response.data["categorias"] if x["categoria_id"] == self.category.id)
        self.assertEqual(Decimal(row["consumido"]), Decimal("675260.87"))
        self.assertTrue(row["monto_prorrateado"])

    def test_rejects_cross_month_period(self):
        response = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-31&hasta=2026-11-01")
        self.assertEqual(response.status_code, 400)
        self.assertIn("mismo mes", response.data["error"])

    def test_two_validities_in_period_return_second_limit_and_change_flag(self):
        Budget.objects.create(
            household=self.household, category=self.category, amount=Decimal("800.00"),
            valid_from=date(2026, 10, 1), valid_to=date(2026, 10, 14), created_by=self.user,
        )
        second = Budget.objects.create(
            household=self.household, category=self.category, amount=Decimal("900.00"),
            valid_from=date(2026, 10, 15), created_by=self.user,
        )
        response = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-01&hasta=2026-10-31")
        row = next(x for x in response.data["categorias"] if x["categoria_id"] == self.category.id)
        self.assertEqual(row["budget_id"], second.id)
        self.assertEqual(Decimal(row["tope"]), Decimal("900.00"))
        self.assertTrue(row["tope_cambio_en_periodo"])

    def test_consumption_isolated_by_household(self):
        outsider = User.objects.create_user("other-home")
        other_home = Household.objects.create(name="Otro hogar")
        other_home.members.add(outsider)
        other_account = Account.objects.create(user=outsider, name="Otra")
        Transaction.objects.create(
            user=outsider, household=other_home, account=other_account,
            subcategory=self.subcategory, amount=Decimal("-999.00"), description="Ajeno",
            created_at=timezone.now(), fecha_efectiva=date(2026, 10, 10),
        )
        response = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-01&hasta=2026-10-31")
        row = next(x for x in response.data["categorias"] if x["categoria_id"] == self.category.id)
        self.assertEqual(Decimal(row["consumido"]), Decimal("0.00"))

    def test_transaction_with_multiple_households_requires_explicit_household(self):
        second = Household.objects.create(name="Segundo hogar")
        second.members.add(self.user)
        payload = {
            "account": self.account.id, "subcategory": self.subcategory.id,
            "amount": "10.00", "type": "egreso", "description": "Ambiguo",
            "fecha_efectiva": "2026-10-10",
        }
        missing = self.client.post("/api/transactions/", payload, format="json")
        payload["household"] = self.household.id
        explicit = self.client.post("/api/transactions/", payload, format="json")
        self.assertEqual(missing.status_code, 400)
        self.assertIn("household", missing.data)
        self.assertEqual(explicit.status_code, 201, explicit.data)
        self.assertEqual(Transaction.objects.get(description="Ambiguo").household, self.household)

    @patch("transactions.budgets.timezone.localdate", return_value=date(2026, 10, 21))
    def test_projection_uses_partial_range_base_and_past_range_is_not_projected(self, _today):
        self.create_expense("-210.00", date(2026, 10, 15))
        self.create_expense("-100.00", date(2026, 10, 5))
        current = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-11&hasta=2026-10-21")
        past = self.client.get("/api/transactions/budgets/consumo/?desde=2026-10-01&hasta=2026-10-10")
        current_row = next(x for x in current.data["categorias"] if x["categoria_id"] == self.category.id)
        past_row = next(x for x in past.data["categorias"] if x["categoria_id"] == self.category.id)
        self.assertEqual(Decimal(current_row["proyeccion_cierre"]), Decimal("400.91"))
        self.assertEqual(Decimal(past_row["proyeccion_cierre"]), Decimal("100.00"))

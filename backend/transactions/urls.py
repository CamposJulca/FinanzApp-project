from django.urls import path

from .views import (
    summary,
    me,
    TransactionListView,
    AccountSaldoRealUpdateView,
    AccountListView,
)

urlpatterns = [
    # Resumen + conciliación
    path("summary/", summary, name="transactions-summary"),

    # Usuario
    path("me/", me, name="transactions-me"),

    # Transacciones
    path("", TransactionListView.as_view(), name="transactions-list"),

    # Cuentas (saldo real manual)
    path("accounts/", AccountListView.as_view(), name="accounts-list"),
    path(
        "accounts/<int:account_id>/saldo-real/",
        AccountSaldoRealUpdateView.as_view(),
        name="account-saldo-real-update",
    ),
]

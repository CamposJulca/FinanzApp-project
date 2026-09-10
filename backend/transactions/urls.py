from django.urls import path

from .views import (
    summary,
    me,
    TransactionListCreateView,
    TransactionDetailView,
    AccountListCreateView,
    AccountDetailView,
    AccountSaldoRealUpdateView,
    TransactionTypeListCreateView,
    TransactionTypeDetailView,
    TransactionCategoryListCreateView,
    TransactionCategoryDetailView,
    TransactionSubCategoryListCreateView,
    TransactionSubCategoryDetailView,
    category_impact,
    subcategory_impact,
)

urlpatterns = [
    # Resumen + conciliación
    path("summary/", summary, name="transactions-summary"),

    # Usuario
    path("me/", me, name="transactions-me"),

    # Árbol de clasificación
    path("types/", TransactionTypeListCreateView.as_view(), name="types-list"),
    path("types/<int:pk>/", TransactionTypeDetailView.as_view(), name="type-detail"),
    path("categories/", TransactionCategoryListCreateView.as_view(), name="categories-list"),
    path("categories/<int:pk>/", TransactionCategoryDetailView.as_view(), name="category-detail"),
    path("categories/<int:pk>/impact/", category_impact, name="category-impact"),
    path("subcategories/", TransactionSubCategoryListCreateView.as_view(), name="subcategories-list"),
    path("subcategories/<int:pk>/", TransactionSubCategoryDetailView.as_view(), name="subcategory-detail"),
    path("subcategories/<int:pk>/impact/", subcategory_impact, name="subcategory-impact"),

    # Cuentas
    path("accounts/", AccountListCreateView.as_view(), name="accounts-list"),
    path("accounts/<int:pk>/", AccountDetailView.as_view(), name="account-detail"),
    path(
        "accounts/<int:account_id>/saldo-real/",
        AccountSaldoRealUpdateView.as_view(),
        name="account-saldo-real-update",
    ),

    # Transacciones (rutas genéricas al final para no tapar las anteriores)
    path("", TransactionListCreateView.as_view(), name="transactions-list"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]

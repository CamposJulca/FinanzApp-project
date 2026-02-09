from django.urls import path
from .views import (
    summary,
    me,
    TransactionListView,
)

urlpatterns = [
    # Resumen financiero + conciliación
    path("summary/", summary, name="transactions-summary"),

    # Info del usuario
    path("me/", me, name="transactions-me"),

    # Listado y creación de transacciones
    path("", TransactionListView.as_view(), name="transactions-list"),
]

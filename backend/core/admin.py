from django.contrib import admin
from .models import (
    Household,
    Account,
    Transfer,
    Transaction,
    TransactionType,
    TransactionCategory,
    TransactionSubCategory,
)

# =========================
# Household
# =========================
@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    filter_horizontal = ("members",)


# =========================
# Account
# =========================
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "saldo_real",
        "currency",
        "created_at",
    )
    list_filter = ("user", "currency")
    search_fields = ("name",)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "household",
        "from_account",
        "to_account",
        "amount",
        "fecha",
        "created_by",
    )
    list_filter = ("household", "fecha")

    def has_add_permission(self, request):
        # Crear fuera del endpoint dejaría la transferencia sin sus dos legs.
        return False

    def has_change_permission(self, request, obj=None):
        # Corregir exige borrar el par completo y volver a crearlo.
        return False


# =========================
# Árbol de clasificación
# =========================
@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "subtipo")
    list_filter = ("tipo", "subtipo")


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(TransactionSubCategory)
class TransactionSubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "frecuencia")
    list_filter = ("category", "frecuencia")
    search_fields = ("name",)


# =========================
# Transaction
# =========================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "account",
        "subcategory",
        "amount",
        "created_at",
        "fecha_efectiva",
        "cubre_desde",
        "cubre_hasta",
        "inserted_at",
        "transfer",
    )
    list_filter = ("subcategory__category__type", "account", "user")
    search_fields = ("description",)
    ordering = ("-created_at",)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.transfer_id is not None:
            return tuple(field.name for field in self.model._meta.fields)
        # El vínculo solo lo crea el flujo atómico de transferencias.
        return ("transfer", "inserted_at")

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.transfer_id is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.transfer_id is not None:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

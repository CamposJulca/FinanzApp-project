from django.contrib import admin
from .models import (
    Household,
    Account,
    Transaction,
    TransactionType,
    TransactionCategory,
    TransactionSubCategory,
)

@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    filter_horizontal = ("members",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "balance", "created_at")
    list_filter = ("user",)
    search_fields = ("name",)


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(TransactionSubCategory)
class TransactionSubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "account",
        "subcategory",
        "amount",
        "created_at",
    )
    list_filter = ("subcategory__category__type", "account", "user")
    search_fields = ("description",)
    ordering = ("-created_at",)

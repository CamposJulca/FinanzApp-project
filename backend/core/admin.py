from django.contrib import admin
from .models import Household, Account, Category, Transaction


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    filter_horizontal = ("members",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "balance", "created_at")
    list_filter = ("user",)
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category_type", "user")
    list_filter = ("category_type", "user")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "account", "category", "amount", "created_at")
    list_filter = ("category__category_type", "account", "user")
    search_fields = ("description",)
    ordering = ("-created_at",)

# backend/core/models.py
from django.db import models
from django.contrib.auth.models import User

from django.contrib.auth.models import User
from django.db import models


class Household(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(
        User,
        related_name="households"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Category(models.Model):
    INCOME = "IN"
    EXPENSE = "EX"

    CATEGORY_TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=2,
        choices=CATEGORY_TYPE_CHOICES
    )

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    subcategory = models.CharField(max_length=100, blank=True)  # 👈 NUEVO
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField()


    def __str__(self):
        return f"{self.amount} - {self.category.name}"


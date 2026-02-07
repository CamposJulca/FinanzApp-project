from django.db import models
from django.contrib.auth.models import User


# =========================
# Núcleo organizacional
# =========================

class Household(models.Model):
    """
    Agrupación lógica de usuarios que comparten información financiera
    (ej: pareja, familia).
    """
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(
        User,
        related_name="households"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    """
    Cuenta financiera base (caja, banco, billetera, etc.)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="accounts"
    )
    name = models.CharField(max_length=100)
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# =========================
# Árbol de Clasificación
# =========================

class TransactionType(models.Model):
    """
    Nivel 1 del árbol.
    Ej: ingreso fijo, ingreso variable, egreso fijo, egreso variable
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TransactionCategory(models.Model):
    """
    Nivel 2 del árbol.
    Depende de un TransactionType.
    Ej: salario, arriendo, servicios, alimentación
    """
    type = models.ForeignKey(
        TransactionType,
        on_delete=models.CASCADE,
        related_name="categories"
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("type", "name")

    def __str__(self):
        return f"{self.type.name} → {self.name}"


class TransactionSubCategory(models.Model):
    """
    Nivel 3 del árbol (hojas).
    Es lo que realmente se asigna a una transacción.
    """
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.category} → {self.name}"


# =========================
# Transacciones
# =========================

class Transaction(models.Model):
    """
    Movimiento financiero real.
    Apunta exclusivamente a una subcategoría del árbol.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    subcategory = models.ForeignKey(
        TransactionSubCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True
    )


    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.amount} - {self.subcategory}"

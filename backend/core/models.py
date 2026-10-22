from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db.models import F, Func, Value
from datetime import date


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
    Cuenta financiera real declarada por el usuario.
    Representa una fuente física o digital de dinero
    (ej: efectivo, cuenta bancaria, billetera digital).

    El saldo aquí NO se calcula automáticamente:
    es ingresado manualmente por el usuario y se usa
    para conciliación contra el saldo contable.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="accounts"
    )

    name = models.CharField(
        max_length=100,
        help_text="Nombre de la cuenta (ej: Caja, Bancolombia, Nequi)"
    )

    saldo_real = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Saldo real declarado manualmente por el usuario"
    )

    currency = models.CharField(max_length=3, default="COP")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Transfer(models.Model):
    """Movimiento entre dos cuentas de un hogar; se corrige borrando y recreando."""

    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    from_account = models.ForeignKey(
        Account,
        related_name="transfers_out",
        on_delete=models.PROTECT,
    )
    to_account = models.ForeignKey(
        Account,
        related_name="transfers_in",
        on_delete=models.PROTECT,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    fecha = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        related_name="transfers_created",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        errors = {}
        if self.from_account_id and self.from_account_id == self.to_account_id:
            errors["to_account"] = "La cuenta destino debe ser distinta de la cuenta origen."
        if self.amount is not None and self.amount <= 0:
            errors["amount"] = "El monto debe ser mayor que cero."
        if self.household_id:
            if self.from_account_id and not self.household.members.filter(
                pk=self.from_account.user_id
            ).exists():
                errors["from_account"] = "La cuenta origen no pertenece a este hogar."
            if self.to_account_id and not self.household.members.filter(
                pk=self.to_account.user_id
            ).exists():
                errors["to_account"] = "La cuenta destino no pertenece a este hogar."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_account} → {self.to_account}: {self.amount}"


# =========================
# Árbol de Clasificación
# =========================

class TransactionType(models.Model):
    """
    Nivel 1 del árbol: la pareja (tipo, subtipo).

    `tipo` y `subtipo` son valores fijos del dominio; sus combinaciones
    producen exactamente 4 parejas:
        (INGRESO, FIJO)   (INGRESO, VARIABLE)
        (EGRESO,  FIJO)   (EGRESO,  VARIABLE)
    Estas 4 filas se siembran en la migración y NO las crea el usuario;
    el usuario sólo agrega categorías y subcategorías debajo de cada pareja.
    """

    TIPO_INGRESO = "INGRESO"
    TIPO_EGRESO = "EGRESO"
    TIPO_CHOICES = [
        (TIPO_INGRESO, "INGRESO"),
        (TIPO_EGRESO, "EGRESO"),
    ]

    SUBTIPO_FIJO = "FIJO"
    SUBTIPO_VARIABLE = "VARIABLE"
    SUBTIPO_CHOICES = [
        (SUBTIPO_FIJO, "FIJO"),
        (SUBTIPO_VARIABLE, "VARIABLE"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    subtipo = models.CharField(max_length=10, choices=SUBTIPO_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("tipo", "subtipo")
        ordering = ("tipo", "subtipo")

    @property
    def name(self):
        """Etiqueta legible de la pareja (compatibilidad hacia atrás)."""
        return f"{self.tipo} / {self.subtipo}"

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
    FRECUENCIA_MENSUAL = "MENSUAL"
    FRECUENCIA_ANUAL = "ANUAL"
    FRECUENCIA_ESPORADICO = "ESPORADICO"
    FRECUENCIA_CHOICES = [
        (FRECUENCIA_MENSUAL, "MENSUAL"),
        (FRECUENCIA_ANUAL, "ANUAL"),
        (FRECUENCIA_ESPORADICO, "ESPORADICO"),
    ]

    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )
    name = models.CharField(max_length=100)
    frecuencia = models.CharField(
        max_length=10,
        choices=FRECUENCIA_CHOICES,
        default=FRECUENCIA_ESPORADICO,
    )

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.category} → {self.name}"


class Budget(models.Model):
    """Tope con vigencia histórica; cambiarlo no crea una fila por mes.

    Un cambio futuro cierra la vigencia anterior y abre una nueva, por lo que
    el historial permanece verificable sin duplicar topes mensualmente.
    """

    household = models.ForeignKey(Household, related_name="budgets", on_delete=models.CASCADE)
    category = models.ForeignKey(TransactionCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="COP")
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        errors = {}
        if self.category_id and self.category.type.tipo != TransactionType.TIPO_EGRESO:
            errors["category"] = "Solo se permiten categorías de EGRESO."
        if self.amount is not None and self.amount <= 0:
            errors["amount"] = "El tope debe ser mayor que cero."
        if self.valid_to and self.valid_to < self.valid_from:
            errors["valid_to"] = "La fecha final no puede ser anterior a la inicial."
        if self.household_id and self.category_id and self.valid_from:
            overlap = Budget.objects.filter(
                household_id=self.household_id,
                category_id=self.category_id,
                valid_from__lte=self.valid_to or date.max,
            ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=self.valid_from))
            if self.pk:
                overlap = overlap.exclude(pk=self.pk)
            if overlap.exists():
                errors["valid_from"] = "La vigencia se solapa con otro tope de esta categoría."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ("category__name", "-valid_from")
        constraints = [
            ExclusionConstraint(
                name="budget_no_overlapping_validity",
                expressions=[
                    (F("household"), RangeOperators.EQUAL),
                    (F("category"), RangeOperators.EQUAL),
                    (
                        Func(F("valid_from"), F("valid_to"), Value("[]"), function="DATERANGE"),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="budget_amount_positive"),
            models.CheckConstraint(
                condition=models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=F("valid_from")),
                name="budget_validity_order",
            ),
        ]


# =========================
# Transacciones
# =========================

class Transaction(models.Model):
    """
    Movimiento financiero real.
    Apunta exclusivamente a una subcategoría del árbol.
    """

    REGISTERED_BY_CHOICES = [
        ("diana", "Diana"),
        ("daniel", "Daniel"),
        ("karla", "Karla"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="transactions",
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
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name="legs",
        null=True,
        blank=True,
    )


    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField()
    fecha_efectiva = models.DateField()
    cubre_desde = models.DateField(null=True, blank=True)
    cubre_hasta = models.DateField(null=True, blank=True)
    inserted_at = models.DateTimeField(auto_now_add=True, null=True)
    registered_by = models.CharField(
        max_length=20,
        choices=REGISTERED_BY_CHOICES,
        blank=True,
        default="",
        help_text="Persona del hogar que registró el movimiento (solo Campos Marin)",
    )

    def __str__(self):
        return f"{self.amount} - {self.subcategory}"

    def clean(self):
        super().clean()
        errors = {}
        if (self.cubre_desde is None) != (self.cubre_hasta is None):
            missing = "cubre_hasta" if self.cubre_hasta is None else "cubre_desde"
            errors[missing] = "Debes indicar ambas fechas del periodo cubierto."
        elif (
            self.cubre_desde is not None
            and self.cubre_hasta is not None
            and self.cubre_hasta < self.cubre_desde
        ):
            errors["cubre_hasta"] = "La fecha final no puede ser anterior a la inicial."
        if errors:
            raise ValidationError(errors)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(cubre_desde__isnull=True, cubre_hasta__isnull=True)
                    | models.Q(cubre_desde__isnull=False, cubre_hasta__isnull=False)
                ),
                name="transaction_coverage_dates_pair",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(cubre_desde__isnull=True)
                    | models.Q(cubre_hasta__gte=models.F("cubre_desde"))
                ),
                name="transaction_coverage_dates_order",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "fecha_efectiva"]),
            models.Index(fields=["subcategory", "fecha_efectiva"]),
            models.Index(fields=["household", "fecha_efectiva"]),
        ]

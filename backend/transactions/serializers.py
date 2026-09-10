from rest_framework import serializers

from core.models import (
    Account,
    Transaction,
    TransactionType,
    TransactionCategory,
    TransactionSubCategory,
)


# =========================================================
# ÁRBOL DE CLASIFICACIÓN
# =========================================================
class TransactionTypeSerializer(serializers.ModelSerializer):
    """Pareja fija (tipo, subtipo). Sólo lectura: no se crea ni edita por API."""

    label = serializers.SerializerMethodField()
    categories_count = serializers.IntegerField(
        source="categories.count", read_only=True
    )

    class Meta:
        model = TransactionType
        fields = ("id", "tipo", "subtipo", "label", "description", "categories_count")
        read_only_fields = ("tipo", "subtipo")

    def get_label(self, obj):
        return f"{obj.tipo} / {obj.subtipo}"


class TransactionCategorySerializer(serializers.ModelSerializer):
    tipo = serializers.CharField(source="type.tipo", read_only=True)
    subtipo = serializers.CharField(source="type.subtipo", read_only=True)
    type_name = serializers.SerializerMethodField()
    subcategories_count = serializers.IntegerField(
        source="subcategories.count", read_only=True
    )

    class Meta:
        model = TransactionCategory
        fields = (
            "id", "name", "type", "tipo", "subtipo",
            "type_name", "subcategories_count",
        )

    def get_type_name(self, obj):
        return f"{obj.type.tipo} / {obj.type.subtipo}"


class TransactionSubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    tipo = serializers.CharField(source="category.type.tipo", read_only=True)
    subtipo = serializers.CharField(source="category.type.subtipo", read_only=True)
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = TransactionSubCategory
        fields = (
            "id", "name", "category", "category_name",
            "tipo", "subtipo", "type_name",
        )

    def get_type_name(self, obj):
        return f"{obj.category.type.tipo} / {obj.category.type.subtipo}"


# =========================================================
# CUENTAS
# =========================================================
class AccountSerializer(serializers.ModelSerializer):
    saldo_real = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False
    )
    transactions_count = serializers.IntegerField(
        source="transactions.count", read_only=True
    )

    class Meta:
        model = Account
        fields = ("id", "name", "saldo_real", "transactions_count", "created_at")
        read_only_fields = ("created_at",)

    def validate_name(self, value):
        """El nombre de cuenta debe ser único dentro del usuario."""
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre no puede estar vacío.")

        user = self.context["request"].user
        qs = Account.objects.filter(user=user, name__iexact=name)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una cuenta con ese nombre.")

        return name


# =========================================================
# TRANSACCIONES
# =========================================================
class TransactionSerializer(serializers.ModelSerializer):
    """
    El signo del monto lo determina `type` (ingreso/egreso):
    se guarda positivo para ingresos y negativo para egresos.
    """

    account_name = serializers.CharField(source="account.name", read_only=True)
    subcategory_name = serializers.CharField(
        source="subcategory.name", read_only=True, default=None
    )
    subcategory_path = serializers.SerializerMethodField()
    type = serializers.ChoiceField(
        choices=("ingreso", "egreso"), write_only=True, required=False
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "description",
            "amount",
            "type",
            "created_at",
            "account",
            "account_name",
            "subcategory",
            "subcategory_name",
            "subcategory_path",
            "registered_by",
        )

    def get_subcategory_path(self, obj):
        """Ruta completa TIPO / SUBTIPO -> Categoría -> Subcategoría.

        Los nombres de último nivel se repiten entre ramas (IMPUESTO existe en
        CARRO, MOTO y CASA), así que el nombre suelto no basta para saber qué
        se clasificó.
        """
        sub = obj.subcategory
        if sub is None:
            return None
        category = sub.category
        type_ = category.type
        return f"{type_.tipo} / {type_.subtipo} → {category.name} → {sub.name}"

    def get_fields(self):
        """Las FK sólo pueden apuntar a cuentas del propio usuario."""
        fields = super().get_fields()
        request = self.context.get("request")
        if request is not None:
            fields["account"].queryset = Account.objects.filter(user=request.user)
        return fields

    def validate_registered_by(self, value):
        from .views import CAMPOSMARIN_USERNAME, VALID_REGISTERED_BY

        value = (value or "").strip().lower()
        if not value:
            return ""

        user = self.context["request"].user
        if user.username != CAMPOSMARIN_USERNAME:
            raise serializers.ValidationError(
                "registered_by solo está habilitado para Campos Marin."
            )
        if value not in VALID_REGISTERED_BY:
            raise serializers.ValidationError(
                "registered_by debe ser Diana, Daniel o Karla."
            )
        return value

    def _final_amount(self, attrs):
        """Reproduce el monto con signo que acabará guardando `_apply_sign`.

        Hay que validar contra lo que quedará almacenado, no contra lo que
        llegó: en un PATCH sin monto el signo lo sigue poniendo la instancia.
        """
        amount = attrs.get("amount")
        if amount is None:
            return getattr(self.instance, "amount", None)

        movement_type = attrs.get("type")
        if movement_type is None:
            # Sin `type` explícito se respeta el signo recibido.
            return amount

        return -abs(amount) if movement_type == "egreso" else abs(amount)

    def validate(self, attrs):
        """La subcategoría debe pertenecer a la rama del signo del movimiento.

        El desplegable de Movimientos ya sólo ofrece la rama correcta, pero sin
        esta validación la API sigue aceptando un ingreso clasificado como
        "EGRESO / FIJO -> CARRO -> SOAT".
        """
        subcategory = (
            attrs["subcategory"]
            if "subcategory" in attrs
            else getattr(self.instance, "subcategory", None)
        )
        amount = self._final_amount(attrs)

        if subcategory is None or amount is None:
            return attrs

        esperado = (
            TransactionType.TIPO_INGRESO
            if amount >= 0
            else TransactionType.TIPO_EGRESO
        )
        rama = subcategory.category.type.tipo

        if rama != esperado:
            raise serializers.ValidationError(
                {
                    "subcategory": (
                        f"La subcategoría «{subcategory.name}» pertenece a "
                        f"{rama} y el movimiento es {esperado}. Elige una "
                        "subcategoría de la rama correcta."
                    )
                }
            )

        return attrs

    def _apply_sign(self, validated_data):
        """Convierte (monto, tipo) en un monto con signo."""
        movement_type = validated_data.pop("type", None)
        amount = validated_data.get("amount")

        if amount is None or movement_type is None:
            # Sin `type` explícito se respeta el signo recibido. En una
            # edición parcial que no toca el monto, esto lo deja intacto.
            return validated_data

        amount = abs(amount)
        validated_data["amount"] = -amount if movement_type == "egreso" else amount
        return validated_data

    def create(self, validated_data):
        validated_data = self._apply_sign(validated_data)
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._apply_sign(validated_data)
        return super().update(instance, validated_data)

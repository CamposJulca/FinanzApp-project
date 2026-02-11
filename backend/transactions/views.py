from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from core.models import Transaction, Account


# =========================================================
# RESUMEN + CONCILIACIÓN CONTABLE
# =========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    user = request.user

    # -------------------------------
    # 1. SALDO CONTABLE (AUTOMÁTICO)
    # -------------------------------
    ingresos = (
        Transaction.objects
        .filter(user=user, amount__gt=0)
        .aggregate(total=Sum("amount"))["total"] or Decimal("0")
    )

    egresos = (
        Transaction.objects
        .filter(user=user, amount__lt=0)
        .aggregate(total=Sum("amount"))["total"] or Decimal("0")
    )

    saldo_contable = ingresos + egresos
    total_movimientos = Transaction.objects.filter(user=user).count()

    # --------------------------------
    # 2. SALDO POR CUENTAS (MANUAL)
    # --------------------------------
    saldo_cuentas = (
        Account.objects
        .filter(user=user)
        .aggregate(total=Sum("saldo_real"))["total"] or Decimal("0")
    )

    # --------------------------------
    # 3. CONCILIACIÓN
    # --------------------------------
    diferencia = saldo_cuentas - saldo_contable
    estado = "OK" if diferencia == 0 else "INCONSISTENTE"

    return Response({
        "ingresos": float(ingresos),
        "egresos": abs(float(egresos)),

        "saldo_contable": float(saldo_contable),
        "saldo_cuentas": float(saldo_cuentas),

        "diferencia": float(diferencia),
        "estado": estado,

        "total_movimientos": total_movimientos,
    })


# =========================================================
# INFO USUARIO
# =========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
    })


# =========================================================
# TRANSACCIONES
# =========================================================
class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = (
            Transaction.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .values(
                "id",
                "description",
                "amount",
                "created_at",
                "account_id",
            )
        )
        return Response(
            {"transactions": list(transactions)},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        data = request.data

        transaction = Transaction.objects.create(
            user=request.user,
            account_id=data["account_id"],
            description=data.get("description", ""),
            amount=Decimal(str(data["amount"])),
            created_at=data.get("created_at"),
        )

        return Response(
            {
                "id": transaction.id,
                "description": transaction.description,
                "amount": float(transaction.amount),
                "created_at": transaction.created_at,
            },
            status=status.HTTP_201_CREATED
        )


# =========================================================
# CUENTAS – ACTUALIZACIÓN DE SALDO REAL (MANUAL)
# =========================================================
class AccountSaldoRealUpdateView(APIView):
    """
    El usuario declara explícitamente cuánto dinero REAL hay en la cuenta.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, account_id):
        account = get_object_or_404(
            Account,
            id=account_id,
            user=request.user
        )

        try:
            saldo_real = Decimal(str(request.data.get("saldo_real")))
        except (InvalidOperation, TypeError):
            return Response(
                {"error": "saldo_real inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account.saldo_real = saldo_real
        account.save(update_fields=["saldo_real"])

        return Response(
            {
                "account_id": account.id,
                "name": account.name,
                "saldo_real": float(account.saldo_real),
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# CUENTAS – LISTADO DE SALDOS REALES
# =========================================================
class AccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = (
            Account.objects
            .filter(user=request.user)
            .order_by("created_at")
        )

        return Response(
            {
                "accounts": [
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "saldo_real": float(acc.saldo_real),
                        "created_at": acc.created_at,
                    }
                    for acc in accounts
                ]
            },
            status=status.HTTP_200_OK
        )

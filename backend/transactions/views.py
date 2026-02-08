from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from core.models import Transaction
from .services import get_transactions, create_transaction


# =========================
# RESUMEN FINANCIERO
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    user = request.user

    ingresos = (
        Transaction.objects
        .filter(user=user, amount__gt=0)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    egresos = (
        Transaction.objects
        .filter(user=user, amount__lt=0)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    balance = ingresos + egresos  # egresos ya es negativo

    total_movimientos = Transaction.objects.filter(user=user).count()

    return Response({
        "ingresos": ingresos,
        "egresos": abs(egresos),
        "balance": balance,
        "total_movimientos": total_movimientos,
    })


# =========================
# INFO USUARIO
# =========================
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


# =========================
# TRANSACCIONES
# =========================
class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = get_transactions(request.user)
        return Response(
            {"transactions": transactions},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        transaction = create_transaction(request.data, request.user)
        return Response(
            transaction,
            status=status.HTTP_201_CREATED
        )

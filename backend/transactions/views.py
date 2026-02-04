from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import get_transactions, create_transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

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


class TransactionListView(APIView):

    def get(self, request):
        transactions = get_transactions()
        return Response(
            {"transactions": transactions},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        transaction = create_transaction(request.data)
        return Response(
            transaction,
            status=status.HTTP_201_CREATED
        )


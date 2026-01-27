from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import get_transactions, create_transaction


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


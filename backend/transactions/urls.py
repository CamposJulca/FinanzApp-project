from django.urls import path
from .views import me, summary, TransactionListView

urlpatterns = [
    path("me/", me),
    path("summary/", summary),
    path("", TransactionListView.as_view()),  # /api/transactions/
]

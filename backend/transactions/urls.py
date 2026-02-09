from django.urls import path
from .views import me, summary, account_balances

urlpatterns = [
    path("me/", me),
    path("summary/", summary),
    path("accounts/", account_balances),
]

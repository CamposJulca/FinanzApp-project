from core.models import Transaction


def get_transactions(user):
    qs = (
        Transaction.objects
        .filter(user=user)
        .order_by("-created_at")
    )

    return [
        {
            "id": t.id,
            "description": t.description,
            "amount": float(t.amount),
            "created_at": t.created_at.strftime("%Y-%m-%d"),
        }
        for t in qs
    ]


def create_transaction(data: dict, user):
    amount = float(data["amount"])

    # Si viene marcado como egreso, lo guardamos negativo
    if data.get("type") == "E":
        amount = -abs(amount)

    tx = Transaction.objects.create(
        user=user,
        account=user.accounts.first(),  # cuenta por defecto
        amount=amount,
        description=data.get("description", ""),
        created_at=data.get("created_at"),
    )

    return {
        "id": tx.id,
        "description": tx.description,
        "amount": float(tx.amount),
        "created_at": tx.created_at.strftime("%Y-%m-%d"),
    }

from pymongo import MongoClient
from datetime import datetime
import os


def _get_db():
    client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        port=int(os.getenv("MONGO_PORT")),
    )
    return client[os.getenv("MONGO_DB")]


def get_transactions():
    db = _get_db()
    return list(db.transactions.find({}, {"_id": 0}))


def create_transaction(data: dict):
    db = _get_db()

    transaction = {
        "description": data["description"],
        "type": data["type"],
        "amount": float(data["amount"]),
        "date": data["date"],
        "has_receipt": bool(data.get("has_receipt", False)),
        "source": data.get("source", "manual"),
        "created_at": datetime.utcnow().isoformat()
    }

    db.transactions.insert_one(transaction)
    return transaction

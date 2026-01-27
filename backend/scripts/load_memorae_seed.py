from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://192.168.0.102:27017")
db = client["finanzapp"]

raw_data = [
    ("Lavado de los dos autos", 65000, "2026-01-26", False, "egreso"),
    ("Peajes", 64000, None, False, "egreso"),
    ("Comida paseo", 200000, None, False, "egreso"),
    ("Cadena enero", 500000, "2026-01-25", False, "egreso"),
    ("Pago hipoteca", 3659463, "2026-01-25", False, "egreso"),
    ("Descuento por error crédito Coopebis (reclamar)", 1409633, None, False, "egreso"),
    ("Ahorro cooperativas", 250000, None, False, "egreso"),
    ("Ingreso general", 12424000, None, False, "ingreso"),
    ("Compra de ropa para Perú", 493000, "2026-01-26", True, "egreso"),
    ("Compra de pañitos", 13000, "2026-01-26", True, "egreso"),
    ("Compra de helado", 15000, "2026-01-26", True, "egreso"),
    ("Parqueadero CC Villa del Rio", 15000, "2026-01-26", False, "egreso"),
    ("Juguetes niños", 63000, "2026-01-26", True, "egreso"),
    ("Desayuno Anamilena Sorpresa", 150000, "2026-01-27", False, "egreso"),
    ("Caja Chica para Liz", 50000, "2026-01-26", False, "egreso"),
]

documents = []

for desc, amount, date, receipt, ttype in raw_data:
    documents.append({
        "description": desc,
        "type": ttype,
        "amount": float(amount),
        "date": date,
        "has_receipt": receipt,
        "source": "memorae",
        "created_at": datetime.utcnow().isoformat()
    })

db.transactions.insert_many(documents)

print(f"✔ {len(documents)} transacciones Memorae cargadas.")

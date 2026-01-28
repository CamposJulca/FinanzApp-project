// Endpoint real expuesto por ngrok (Django)
const API_BASE_URL = "https://finanzapp.ngrok.io/api/transactions/";

/**
 * Obtiene todas las transacciones
 * GET /api/transactions/
 */
export async function fetchTransactions() {
  const response = await fetch(API_BASE_URL, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Error obteniendo transacciones");
  }

  return response.json();
}

/**
 * Crea una nueva transacción
 * POST /api/transactions/
 */
export async function createTransaction(payload) {
  const response = await fetch(API_BASE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Error creando transacción");
  }

  return response.json();
}

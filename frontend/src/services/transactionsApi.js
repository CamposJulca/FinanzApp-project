// Base URL del backend (ajústalo si cambia ngrok o dominio)
const API_BASE_URL = "https://finanzapp.ngrok.io/api/transactions/";

/**
 * Obtiene todas las transacciones
 * GET /api/transactions/
 */
export async function fetchTransactions() {
  const response = await fetch(API_BASE_URL, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Error obteniendo transacciones");
  }

  return response.json();
}

/**
 * Obtiene el resumen financiero
 * GET /api/transactions/summary/
 *
 * Espera:
 * {
 *   ingresos: number,
 *   egresos: number,
 *   balance: number,
 *   total_movimientos: number
 * }
 */
export async function fetchSummary() {
  const response = await fetch(`${API_BASE_URL}summary/`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Error obteniendo resumen financiero");
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
    credentials: "include",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Error creando transacción");
  }

  return response.json();
}

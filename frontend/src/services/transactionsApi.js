const API_BASE_URL = "https://finanzapp.ngrok.io/api/transactions/";

// ============================
// TRANSACCIONES
// ============================
export async function fetchTransactions() {
  const response = await fetch(API_BASE_URL, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Error obteniendo transacciones");
  }
  return response.json();
}

export async function createTransaction(payload) {
  const response = await fetch(API_BASE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Error creando transacción");
  }
  return response.json();
}

// ============================
// RESUMEN + CONCILIACIÓN
// ============================
export async function fetchSummary() {
  const response = await fetch(`${API_BASE_URL}summary/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Error obteniendo resumen financiero");
  }
  return response.json();
}

// ============================
// CUENTAS (SALDO REAL)
// ============================
export async function fetchAccounts() {
  const response = await fetch(`${API_BASE_URL}accounts/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Error obteniendo cuentas");
  }
  return response.json();
}

export async function updateAccountBalance(accountId, saldoReal) {
  const response = await fetch(
    `${API_BASE_URL}accounts/${accountId}/balance/`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ balance: saldoReal }),
    }
  );

  if (!response.ok) {
    throw new Error("Error actualizando saldo real");
  }

  return response.json();
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api/transactions/";

export function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

/**
 * Cliente único para toda la API.
 * Centraliza credenciales, CSRF y el formato de error, para que los módulos
 * de la interfaz sólo se ocupen de qué piden, no de cómo.
 */
async function request(path, { method = "GET", body } = {}) {
  const options = {
    method,
    credentials: "include",
    headers: {},
  };

  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  if (method !== "GET") {
    options.headers["X-CSRFToken"] = getCookie("csrftoken") || "";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    // DRF devuelve {campo: ["mensaje"]} en errores de validación.
    const detail =
      data.error ||
      data.detail ||
      Object.entries(data)
        .map(([field, msgs]) =>
          Array.isArray(msgs) ? `${field}: ${msgs.join(" ")}` : `${field}: ${msgs}`
        )
        .join(" · ");
    const error = new Error(detail || `Error ${response.status}`);
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

// ============================
// TRANSACCIONES
// ============================
export async function fetchTransactions(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(qs ? `?${qs}` : "");
}

export const createTransaction = (payload) =>
  request("", { method: "POST", body: payload });

export const updateTransaction = (id, payload) =>
  request(`${id}/`, { method: "PATCH", body: payload });

export const deleteTransaction = (id) => request(`${id}/`, { method: "DELETE" });

// ============================
// USUARIO Y RESUMEN
// ============================
export const fetchMe = () => request("me/");
export const fetchSummary = () => request("summary/");

// ============================
// CUENTAS
// ============================
export const fetchAccounts = () => request("accounts/");

export const createAccount = (payload) =>
  request("accounts/", { method: "POST", body: payload });

export const updateAccount = (id, payload) =>
  request(`accounts/${id}/`, { method: "PATCH", body: payload });

export const deleteAccount = (id, { force = false } = {}) =>
  request(`accounts/${id}/${force ? "?force=true" : ""}`, { method: "DELETE" });

export const updateAccountBalance = (accountId, saldoReal) =>
  request(`accounts/${accountId}/saldo-real/`, {
    method: "PUT",
    body: { saldo_real: saldoReal },
  });

// ============================
// ÁRBOL DE CLASIFICACIÓN
// ============================
export const fetchTypes = () => request("types/");
export const createType = (payload) =>
  request("types/", { method: "POST", body: payload });
export const updateType = (id, payload) =>
  request(`types/${id}/`, { method: "PATCH", body: payload });
export const deleteType = (id) => request(`types/${id}/`, { method: "DELETE" });

export const fetchCategories = () => request("categories/");
export const createCategory = (payload) =>
  request("categories/", { method: "POST", body: payload });
export const updateCategory = (id, payload, { confirm = false } = {}) =>
  request(`categories/${id}/${confirm ? "?confirm=true" : ""}`, {
    method: "PATCH",
    body: payload,
  });

export const fetchSubCategories = () => request("subcategories/");
export const createSubCategory = (payload) =>
  request("subcategories/", { method: "POST", body: payload });
export const updateSubCategory = (id, payload, { confirm = false } = {}) =>
  request(`subcategories/${id}/${confirm ? "?confirm=true" : ""}`, {
    method: "PATCH",
    body: payload,
  });

// ============================
// BORRADO CON IMPACTO DECLARADO
// ============================
// El backend rechaza borrar una rama con movimientos si no se le dice qué hacer
// con ellos. `fetch*Impact` es la consulta previa que alimenta el aviso, y la
// estrategia viaja en la propia petición de borrado, nunca por defecto.

export const fetchCategoryImpact = (id) => request(`categories/${id}/impact/`);
export const fetchSubCategoryImpact = (id) =>
  request(`subcategories/${id}/impact/`);

function deleteWithStrategy(base, id, { strategy, target } = {}) {
  const params = new URLSearchParams();
  if (strategy) params.set("on_transactions", strategy);
  if (target) params.set("to", String(target));
  const qs = params.toString();
  return request(`${base}/${id}/${qs ? `?${qs}` : ""}`, { method: "DELETE" });
}

export const deleteCategory = (id, options) =>
  deleteWithStrategy("categories", id, options);

export const deleteSubCategory = (id, options) =>
  deleteWithStrategy("subcategories", id, options);

import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  fetchTransactions,
  createTransaction,
  updateTransaction,
  deleteTransaction,
  fetchAccounts,
  fetchSubCategories,
} from "../services/transactionsApi";

const today = () => new Date().toISOString().slice(0, 10);

const EMPTY_FORM = {
  description: "",
  amount: "",
  type: "egreso",
  fecha_efectiva: today(),
  account: "",
  subcategory: "",
  registered_by: "",
};

export function MovimientosPage() {
  const { currentUser, refreshSummary } = useOutletContext();

  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [loading, setLoading] = useState(true);

  const isCamposMarin = currentUser?.username === "camposmarin";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [tx, acc, sub] = await Promise.all([
        fetchTransactions(),
        fetchAccounts(),
        fetchSubCategories(),
      ]);
      setTransactions(tx.transactions || []);
      setAccounts(acc.accounts || []);
      setSubcategories(sub.subcategories || []);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const setField = (field) => (event) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }));

  // El tipo del movimiento (ingreso/egreso) manda sobre qué rama del árbol es
  // clasificable: sin este filtro se podía guardar un ingreso como
  // "EGRESO / FIJO → CARRO → SOAT".
  const matchesType = (sub, movementType) =>
    (sub.tipo || "").toUpperCase() === movementType.toUpperCase();

  const setType = (event) => {
    const type = event.target.value;
    setForm((prev) => {
      const selected = subcategories.find(
        (s) => String(s.id) === String(prev.subcategory)
      );
      // Cambiar el tipo invalida una subcategoría de la otra rama.
      const subcategory =
        selected && !matchesType(selected, type) ? "" : prev.subcategory;
      return { ...prev, type, subcategory };
    });
  };

  const visibleSubcategories = subcategories.filter((s) =>
    matchesType(s, form.type)
  );

  // En edición, un movimiento antiguo puede apuntar a la rama contraria. Se
  // conserva visible para no borrarlo en silencio al guardar.
  const selectedSubcategory = subcategories.find(
    (s) => String(s.id) === String(form.subcategory)
  );
  const outOfBranch =
    selectedSubcategory && !matchesType(selectedSubcategory, form.type)
      ? selectedSubcategory
      : null;

  const groupedSubcategories = groupByBranch(visibleSubcategories);

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, fecha_efectiva: today() });
    setEditingId(null);
  };

  const startEdit = (tx) => {
    setEditingId(tx.id);
    setForm({
      description: tx.description || "",
      amount: String(Math.abs(Number(tx.amount))),
      type: Number(tx.amount) >= 0 ? "ingreso" : "egreso",
      fecha_efectiva: tx.fecha_efectiva || "",
      account: tx.account || "",
      subcategory: tx.subcategory || "",
      registered_by: tx.registered_by || "",
    });
    setStatus({ type: "idle", message: "" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.description.trim() || !form.amount || !form.fecha_efectiva) {
      setStatus({
        type: "error",
        message: "Completa monto, fecha y descripción.",
      });
      return;
    }
    if (isCamposMarin && !form.registered_by) {
      setStatus({
        type: "error",
        message: "Selecciona quién registra el movimiento.",
      });
      return;
    }

    const payload = {
      description: form.description.trim(),
      amount: Number(form.amount),
      type: form.type,
      fecha_efectiva: form.fecha_efectiva,
      ...(form.account ? { account: Number(form.account) } : {}),
      subcategory: form.subcategory ? Number(form.subcategory) : null,
      ...(isCamposMarin ? { registered_by: form.registered_by } : {}),
    };

    setStatus({ type: "saving", message: "Guardando..." });
    try {
      if (editingId) {
        await updateTransaction(editingId, payload);
        setStatus({ type: "success", message: "Movimiento actualizado." });
      } else {
        await createTransaction(payload);
        setStatus({ type: "success", message: "Movimiento creado." });
      }
      resetForm();
      await load();
      await refreshSummary();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const handleDelete = async (tx) => {
    const label = tx.description || `movimiento #${tx.id}`;
    if (!window.confirm(`¿Eliminar "${label}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    try {
      await deleteTransaction(tx.id);
      if (editingId === tx.id) resetForm();
      setStatus({ type: "success", message: "Movimiento eliminado." });
      await load();
      await refreshSummary();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  return (
    <>
      <form className="transaction-form" onSubmit={handleSubmit}>
        <div className="form-header">
          <h2>{editingId ? `Editando movimiento #${editingId}` : "Nuevo movimiento"}</h2>
          <span>{editingId ? "Modo edición" : "Registro manual"}</span>
        </div>

        <div className="form-grid">
          <label>
            Monto
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="0.01"
              placeholder="0"
              value={form.amount}
              onChange={setField("amount")}
            />
          </label>

          <label>
            Fecha
            <input
              type="date"
              value={form.fecha_efectiva}
              onChange={setField("fecha_efectiva")}
            />
          </label>

          <label>
            Tipo
            <select value={form.type} onChange={setType}>
              <option value="egreso">Egreso</option>
              <option value="ingreso">Ingreso</option>
            </select>
          </label>

          <label>
            Cuenta
            <select value={form.account} onChange={setField("account")}>
              <option value="">Cuenta por defecto</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Subcategoría
            <select value={form.subcategory} onChange={setField("subcategory")}>
              <option value="">Sin clasificar</option>
              {outOfBranch && (
                <optgroup label="Fuera del tipo actual">
                  <option value={outOfBranch.id}>
                    {outOfBranch.type_name} → {outOfBranch.category_name} →{" "}
                    {outOfBranch.name}
                  </option>
                </optgroup>
              )}
              {groupedSubcategories.map(([branch, items]) => (
                <optgroup key={branch} label={branch}>
                  {items.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          {isCamposMarin && (
            <label>
              Registrado por
              <select
                value={form.registered_by}
                onChange={setField("registered_by")}
              >
                <option value="">Selecciona...</option>
                <option value="diana">Diana</option>
                <option value="daniel">Daniel</option>
                <option value="karla">Karla</option>
              </select>
            </label>
          )}

          <label className="description-field">
            Descripción
            <textarea
              rows="3"
              placeholder="Ej: mercado, pago hipoteca, ingreso nómina..."
              value={form.description}
              onChange={setField("description")}
            />
          </label>

        </div>

        <div className="form-actions">
          <button type="submit" disabled={status.type === "saving"}>
            {status.type === "saving"
              ? "Guardando..."
              : editingId
                ? "Guardar cambios"
                : "Guardar movimiento"}
          </button>
          {editingId && (
            <button type="button" className="ghost-btn" onClick={resetForm}>
              Cancelar edición
            </button>
          )}
          {status.message && (
            <span className={`form-status ${status.type}`}>{status.message}</span>
          )}
        </div>
      </form>

      <section className="data-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Historial</p>
            <h2>Movimientos</h2>
          </div>
          <span className="counter-pill">{transactions.length} registros</span>
        </div>

        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th align="left">Fecha</th>
                <th align="left">Descripción</th>
                <th align="left">Cuenta</th>
                <th align="left">Clasificación</th>
                {isCamposMarin && <th align="left">Registrado por</th>}
                <th align="right">Monto</th>
                <th align="right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.id} className={editingId === t.id ? "row-editing" : ""}>
                  <td>{t.fecha_efectiva || "—"}</td>
                  <td>{t.description}</td>
                  <td>{t.account_name}</td>
                  <td>
                    {t.transfer ? (
                      <span className="chip">Transferencia</span>
                    ) : t.subcategory_name ? (
                      <span className="chip" title={t.subcategory_path || ""}>
                        {t.subcategory_path || t.subcategory_name}
                      </span>
                    ) : (
                      <span className="muted">Sin clasificar</span>
                    )}
                  </td>
                  {isCamposMarin && (
                    <td>
                      {t.registered_by
                        ? t.registered_by.charAt(0).toUpperCase() +
                          t.registered_by.slice(1)
                        : "—"}
                    </td>
                  )}
                  <td
                    className={
                      Number(t.amount) >= 0 ? "amount income" : "amount expense"
                    }
                  >
                    ${Number(t.amount).toLocaleString()}
                  </td>
                  <td className="row-actions">
                    {t.transfer ? (
                      <span className="muted">Gestionar como transferencia</span>
                    ) : (
                      <>
                        <button type="button" onClick={() => startEdit(t)}>
                          Editar
                        </button>
                        <button
                          type="button"
                          className="danger"
                          onClick={() => handleDelete(t)}
                        >
                          Eliminar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && transactions.length === 0 && (
                <tr>
                  <td className="empty-state" colSpan={isCamposMarin ? 7 : 6}>
                    Sin movimientos cargados. El tablero está listo para iniciar
                    desde cero.
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td className="empty-state" colSpan={isCamposMarin ? 7 : 6}>
                    Cargando...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

/**
 * Agrupa por rama "SUBTIPO → Categoría" para que el desplegable sea navegable.
 * El tipo (INGRESO/EGRESO) ya viene fijado por el filtro, así que repetirlo en
 * cada etiqueta sólo añadiría ruido.
 */
function groupByBranch(subcategories) {
  const groups = new Map();
  for (const sub of subcategories) {
    const branch = `${sub.subtipo} → ${sub.category_name}`;
    if (!groups.has(branch)) groups.set(branch, []);
    groups.get(branch).push(sub);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b, "es"));
}

import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  fetchAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
} from "../services/transactionsApi";

const money = (value) => `$${Number(value || 0).toLocaleString()}`;

export function CuentasPage() {
  const { refreshSummary } = useOutletContext();

  const [accounts, setAccounts] = useState([]);
  const [nueva, setNueva] = useState({ name: "", saldo_real: "" });
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ name: "", saldo_real: "" });
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAccounts();
      setAccounts(data.accounts || []);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!nueva.name.trim()) {
      setStatus({ type: "error", message: "El nombre es obligatorio." });
      return;
    }

    setStatus({ type: "saving", message: "Creando cuenta..." });
    try {
      await createAccount({
        name: nueva.name.trim(),
        saldo_real: nueva.saldo_real || "0",
      });
      setNueva({ name: "", saldo_real: "" });
      setStatus({ type: "success", message: "Cuenta creada." });
      await load();
      await refreshSummary();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const startEdit = (account) => {
    setEditingId(account.id);
    setDraft({ name: account.name, saldo_real: String(account.saldo_real) });
    setStatus({ type: "idle", message: "" });
  };

  const handleSave = async (id) => {
    setStatus({ type: "saving", message: "Guardando..." });
    try {
      await updateAccount(id, {
        name: draft.name.trim(),
        saldo_real: draft.saldo_real || "0",
      });
      setEditingId(null);
      setStatus({ type: "success", message: "Cuenta actualizada." });
      await load();
      await refreshSummary();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const handleDelete = async (account) => {
    if (!window.confirm(`¿Eliminar la cuenta "${account.name}"?`)) return;

    try {
      await deleteAccount(account.id);
      setStatus({ type: "success", message: "Cuenta eliminada." });
      await load();
      await refreshSummary();
    } catch (error) {
      // 409 = la cuenta tiene movimientos; el backend exige confirmación
      // explícita porque el borrado arrastra esos movimientos consigo.
      if (error.status === 409) {
        const n = error.payload?.transactions_count ?? "sus";
        const ok = window.confirm(
          `La cuenta "${account.name}" tiene ${n} movimiento(s).\n\n` +
            "Eliminarla borrará también esos movimientos. ¿Continuar?"
        );
        if (!ok) return;
        try {
          await deleteAccount(account.id, { force: true });
          setStatus({
            type: "success",
            message: "Cuenta y movimientos eliminados.",
          });
          await load();
          await refreshSummary();
        } catch (forced) {
          setStatus({ type: "error", message: forced.message });
        }
        return;
      }
      setStatus({ type: "error", message: error.message });
    }
  };

  const total = accounts.reduce((sum, a) => sum + Number(a.saldo_real), 0);

  return (
    <>
      <form className="transaction-form" onSubmit={handleCreate}>
        <div className="form-header">
          <h2>Nueva cuenta</h2>
          <span>Fuente de dinero</span>
        </div>

        <div className="form-grid">
          <label className="description-field">
            Nombre
            <input
              type="text"
              placeholder="Ej: Bancolombia, Nequi, Efectivo..."
              value={nueva.name}
              onChange={(e) => setNueva({ ...nueva, name: e.target.value })}
            />
          </label>

          <label>
            Saldo real inicial
            <input
              type="number"
              inputMode="decimal"
              step="0.01"
              placeholder="0"
              value={nueva.saldo_real}
              onChange={(e) => setNueva({ ...nueva, saldo_real: e.target.value })}
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={status.type === "saving"}>
            Crear cuenta
          </button>
          {status.message && (
            <span className={`form-status ${status.type}`}>{status.message}</span>
          )}
        </div>
      </form>

      <section className="data-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Administración</p>
            <h2>Cuentas</h2>
            <p className="muted">
              El saldo real lo declaras tú; se concilia contra el saldo contable.
            </p>
          </div>
          <span className="counter-pill">{money(total)} en total</span>
        </div>

        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th align="left">Cuenta</th>
                <th align="right">Saldo real</th>
                <th align="right">Movimientos</th>
                <th align="right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => {
                const editing = editingId === account.id;
                return (
                  <tr key={account.id} className={editing ? "row-editing" : ""}>
                    <td>
                      {editing ? (
                        <input
                          type="text"
                          value={draft.name}
                          onChange={(e) =>
                            setDraft({ ...draft, name: e.target.value })
                          }
                        />
                      ) : (
                        account.name
                      )}
                    </td>
                    <td align="right">
                      {editing ? (
                        <input
                          type="number"
                          step="0.01"
                          className="money-input"
                          value={draft.saldo_real}
                          onChange={(e) =>
                            setDraft({ ...draft, saldo_real: e.target.value })
                          }
                        />
                      ) : (
                        money(account.saldo_real)
                      )}
                    </td>
                    <td align="right">{account.transactions_count}</td>
                    <td className="row-actions">
                      {editing ? (
                        <>
                          <button type="button" onClick={() => handleSave(account.id)}>
                            Guardar
                          </button>
                          <button
                            type="button"
                            className="ghost-btn"
                            onClick={() => setEditingId(null)}
                          >
                            Cancelar
                          </button>
                        </>
                      ) : (
                        <>
                          <button type="button" onClick={() => startEdit(account)}>
                            Editar
                          </button>
                          <button
                            type="button"
                            className="danger"
                            onClick={() => handleDelete(account)}
                          >
                            Eliminar
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
              {!loading && accounts.length === 0 && (
                <tr>
                  <td className="empty-state" colSpan={4}>
                    Sin cuentas. Crea la primera arriba.
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td className="empty-state" colSpan={4}>
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

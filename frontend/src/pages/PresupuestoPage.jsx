import { useCallback, useEffect, useState } from "react";
import {
  createBudget,
  fetchBudgetConsumption,
  updateBudget,
} from "../services/transactionsApi";

const money = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

function signal(row) {
  if (row.tope == null) return "neutral";
  if (Number(row.proyeccion_cierre) > Number(row.tope) || Number(row.porcentaje) > 90) return "red";
  if (Number(row.porcentaje) >= 70) return "amber";
  return "green";
}

export function PresupuestoPage() {
  const [report, setReport] = useState(null);
  const [editing, setEditing] = useState(null);
  const [amount, setAmount] = useState("");
  const [validFrom, setValidFrom] = useState(new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setReport(await fetchBudgetConsumption());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchBudgetConsumption()
      .then((data) => {
        if (active) setReport(data);
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => { active = false; };
  }, []);

  const open = (row) => {
    setEditing(row);
    setAmount(row.tope ?? "");
    setValidFrom(row.budget_valid_from ?? new Date().toISOString().slice(0, 10));
    setNote("");
  };

  const save = async (event) => {
    event.preventDefault();
    const payload = { amount, currency: "COP", note };
    try {
      if (editing.budget_id) {
        await updateBudget(editing.budget_id, payload);
      } else {
        await createBudget({
          ...payload,
          household: report.household_id,
          category: editing.categoria_id,
          valid_from: validFrom,
        });
      }
      setEditing(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="budget-page">
      <div className="section-heading">
        <div><p className="eyebrow">Planeación mensual</p><h2>Presupuesto</h2></div>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {!report ? <p>Cargando presupuesto…</p> : <>
        <p className="budget-history">
          Histórico disponible: {report.meses_historico} meses completos; la proyección usa el ritmo del periodo actual
        </p>
        <div className="table-wrap">
          <table className="budget-table">
            <thead><tr><th>Categoría</th><th>Tope</th><th>Consumido</th><th>Restante</th><th>Avance</th><th /></tr></thead>
            <tbody>{report.categorias.map((row) => {
              const level = signal(row);
              const width = Math.min(100, Math.max(0, Number(row.porcentaje) || 0));
              return <tr key={row.categoria_id}>
                <td><strong>{row.categoria_nombre}</strong><small>{row.subtipo}</small>
                  {row.tope_cambio_en_periodo && <span className="budget-notice">El tope cambió en el periodo</span>}
                  {row.monto_prorrateado && <span className="budget-notice">Incluye monto prorrateado</span>}
                </td>
                <td>{row.tope == null ? "Sin tope" : money.format(row.tope)}</td>
                <td>{money.format(row.consumido)}</td>
                <td>{row.restante == null ? "—" : money.format(row.restante)}</td>
                <td><div className="budget-progress" aria-label={`${row.porcentaje ?? 0}%`}><span className={level} style={{ width: `${width}%` }} /></div><small>Proyección {money.format(row.proyeccion_cierre)}</small></td>
                <td><button className="secondary-button" onClick={() => open(row)}>{row.budget_id ? "Corregir" : "Crear tope"}</button></td>
              </tr>;
            })}</tbody>
          </table>
        </div>
      </>}
      {editing && <div className="modal-backdrop" role="presentation">
        <form className="budget-modal" onSubmit={save}>
          <h3>{editing.budget_id ? "Corregir tope" : "Crear tope"}</h3>
          <p>{editing.categoria_nombre}</p>
          <label>Monto<input type="number" min="0.01" step="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
          {!editing.budget_id && <label>Vigente desde<input type="date" required value={validFrom} onChange={(e) => setValidFrom(e.target.value)} /></label>}
          <label>Nota<textarea value={note} onChange={(e) => setNote(e.target.value)} /></label>
          <div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setEditing(null)}>Cancelar</button><button type="submit" className="primary-button">Guardar</button></div>
        </form>
      </div>}
    </section>
  );
}

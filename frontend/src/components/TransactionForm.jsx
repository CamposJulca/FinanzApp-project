import { useState } from "react";
import { createTransaction } from "../services/transactionsApi";

const today = new Date().toISOString().slice(0, 10);

export function TransactionForm({
  onCreated,
  disabled = false,
  reason = "",
  currentUser = null,
}) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [createdAt, setCreatedAt] = useState(today);
  const [type, setType] = useState("egreso");
  const [registeredBy, setRegisteredBy] = useState("");
  const [status, setStatus] = useState({ type: "idle", message: "" });

  const isCamposMarin = currentUser?.username === "camposmarin";

  if (disabled) {
    return (
      <div className="alert alert-danger">
        <strong>Registro de movimientos bloqueado</strong>
        <p>{reason}</p>
      </div>
    );
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!description.trim() || !amount || !createdAt) {
      setStatus({
        type: "error",
        message: "Completa monto, fecha y descripción.",
      });
      return;
    }

    if (isCamposMarin && !registeredBy) {
      setStatus({
        type: "error",
        message: "Selecciona quién registra el movimiento (Diana, Daniel o Karla).",
      });
      return;
    }

    setStatus({ type: "saving", message: "Guardando movimiento..." });

    try {
      await createTransaction({
        description: description.trim(),
        amount: Number(amount),
        created_at: createdAt,
        type,
        source: "manual",
        ...(isCamposMarin ? { registered_by: registeredBy } : {}),
      });

      setDescription("");
      setAmount("");
      setCreatedAt(today);
      setType("egreso");
      setRegisteredBy("");
      setStatus({ type: "success", message: "Movimiento guardado." });
      await onCreated?.();
    } catch (error) {
      setStatus({
        type: "error",
        message: error.message || "No se pudo guardar el movimiento.",
      });
    }
  };

  return (
    <form className="transaction-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h2>Nuevo movimiento</h2>
        <span>Registro manual</span>
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
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </label>

        <label>
          Fecha
          <input
            type="date"
            value={createdAt}
            onChange={(event) => setCreatedAt(event.target.value)}
          />
        </label>

        <label>
          Tipo
          <select value={type} onChange={(event) => setType(event.target.value)}>
            <option value="egreso">Egreso</option>
            <option value="ingreso">Ingreso</option>
          </select>
        </label>

        {isCamposMarin && (
          <label>
            Registrado por
            <select
              value={registeredBy}
              onChange={(event) => setRegisteredBy(event.target.value)}
            >
              <option value="">Selecciona...</option>
              <option value="diana">Diana</option>
              <option value="daniel">Daniel</option>
              <option value="karla">Karla</option>
            </select>
          </label>
        )}

        <label className="disabled-field">
          Subtipo
          <select disabled>
            <option>Por definir</option>
          </select>
        </label>

        <label className="disabled-field">
          Categoría
          <select disabled>
            <option>Se clasificará con patrones</option>
          </select>
        </label>

        <label className="disabled-field">
          Subcategoría
          <select disabled>
            <option>Se clasificará con patrones</option>
          </select>
        </label>

        <label className="description-field">
          Descripción
          <textarea
            rows="3"
            placeholder="Ej: mercado, pago hipoteca, ingreso nómina..."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" disabled={status.type === "saving"}>
          {status.type === "saving" ? "Guardando..." : "Guardar movimiento"}
        </button>
        {status.message && (
          <span className={`form-status ${status.type}`}>{status.message}</span>
        )}
      </div>
    </form>
  );
}

import { useState } from "react";

export function TransactionForm({ onSubmit, disabled = false, reason = "" }) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");

  if (disabled) {
    return (
      <div
        style={{
          padding: "1rem",
          border: "1px solid #e74c3c",
          borderRadius: "8px",
          background: "#1c1c1c",
          color: "#e74c3c",
          marginBottom: "1.5rem",
        }}
      >
        <strong>🚫 Registro de movimientos bloqueado</strong>
        <p style={{ marginTop: "0.5rem", color: "#aaa" }}>
          {reason}
        </p>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!description || !amount) return;

    await onSubmit({
      description,
      amount: Number(amount),
      source: "manual",
    });

    setDescription("");
    setAmount("");
  };

  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h3>➕ Nuevo movimiento</h3>

      <input
        type="text"
        placeholder="Descripción"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        style={{ marginRight: "0.5rem" }}
      />

      <input
        type="number"
        placeholder="Monto"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        style={{ marginRight: "0.5rem" }}
      />

      <button onClick={handleSubmit}>Agregar</button>
    </div>
  );
}

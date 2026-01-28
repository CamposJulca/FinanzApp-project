import { useState } from "react";

export function TransactionForm({ onSubmit }) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");

  const handleSubmit = async () => {
    if (!description || !amount) return;

    await onSubmit({
      description,
      amount: Number(amount),
      type: "egreso",
      has_receipt: false,
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

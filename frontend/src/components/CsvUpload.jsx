import { useState } from "react";
import { createTransaction } from "../services/transactionsApi";

export function CsvUpload({ onCompleted }) {
  const [loading, setLoading] = useState(false);

  const parseCSV = async (file) => {
    const text = await file.text();
    const lines = text.split("\n").slice(1); // quitar header

    const transactions = lines
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [_, description, amount, date, receipt] = line.split(",");

        return {
          description: description.trim(),
          amount: Number(
            amount.replace(/\$/g, "").replace(/,/g, "")
          ),
          type: description.toLowerCase().includes("ingreso")
            ? "ingreso"
            : "egreso",
          date: date.includes("—") ? null : normalizeDate(date),
          has_receipt: receipt.trim().toLowerCase() === "sí",
          source: "memorae_csv",
        };
      });

    return transactions;
  };

  const normalizeDate = (raw) => {
    // Ej: "26 de enero"
    const months = {
      enero: "01",
      febrero: "02",
      marzo: "03",
      abril: "04",
      mayo: "05",
      junio: "06",
      julio: "07",
      agosto: "08",
      septiembre: "09",
      octubre: "10",
      noviembre: "11",
      diciembre: "12",
    };

    const [day, , month] = raw.split(" ");
    return `2026-${months[month]}-${day.padStart(2, "0")}`;
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    const transactions = await parseCSV(file);

    for (const tx of transactions) {
      await createTransaction(tx);
    }

    setLoading(false);
    onCompleted();
  };

  return (
    <div style={{ margin: "1rem 0" }}>
      <label>
        📤 Cargar CSV Memorae
        <input
          type="file"
          accept=".csv"
          onChange={handleUpload}
          disabled={loading}
        />
      </label>
      {loading && <p>Procesando CSV…</p>}
    </div>
  );
}

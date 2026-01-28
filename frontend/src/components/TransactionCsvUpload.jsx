import { createTransaction } from "../services/transactionsApi";

export function TransactionCsvUpload({ onFinished }) {

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    console.log("📂 CSV seleccionado:", file.name);

    const text = await file.text();
    const lines = text.split("\n").slice(1);

    for (const line of lines) {
      if (!line.trim()) continue;

      const [, descripcion, monto, fecha, comprobante] = line.split(",");

      const payload = {
        description: descripcion,
        amount: Number(monto.replace(/\$|\.|,/g, "")),
        type: descripcion.toLowerCase().includes("ingreso")
          ? "ingreso"
          : "egreso",
        date: fecha === "—" ? null : fecha,
        has_receipt: comprobante?.trim() === "Sí",
        source: "memorae_csv",
      };

      console.log("➡️ Insertando:", payload);
      await createTransaction(payload);
    }

    alert("CSV cargado correctamente");
    onFinished();
    e.target.value = "";
  };

  return (
    <div style={{ margin: "1.5rem 0" }}>
      <label
        htmlFor="csv-upload"
        style={{ cursor: "pointer", color: "#f1c40f" }}
      >
        📂 Cargar CSV Memorae
      </label>

      <input
        id="csv-upload"
        type="file"
        accept=".csv"
        style={{ display: "none" }}
        onChange={handleFile}
      />
    </div>
  );
}

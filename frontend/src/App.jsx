import { useEffect, useState } from "react";
import { TransactionForm } from "./components/TransactionForm";
import {
  fetchTransactions,
  fetchSummary,
} from "./services/transactionsApi";

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    ingresos: 0,
    egresos: 0,
    balance: 0,
    total_movimientos: 0,
  });

  // ===============================
  // CARGA DE DATOS
  // ===============================
  const loadData = async () => {
    try {
      const [txData, summaryData] = await Promise.all([
        fetchTransactions(),
        fetchSummary(),
      ]);

      setTransactions(txData.transactions || []);
      setSummary(summaryData);
    } catch (err) {
      console.error("Error cargando datos", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // ===============================
  // RENDER
  // ===============================
  return (
    <div style={{ padding: "2rem", background: "#121212", color: "#fff" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>📊 FinanzApp</h1>

      {/* ================= KPIs ================= */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <KpiCard title="Ingresos" value={summary.ingresos} color="#2ecc71" />
        <KpiCard title="Egresos" value={summary.egresos} color="#e74c3c" />
        <KpiCard title="Balance" value={summary.balance} color="#3498db" />
        <KpiCard
          title="Movimientos"
          value={summary.total_movimientos}
          color="#f1c40f"
          isCurrency={false}
        />
      </div>

      {/* ================= NUEVO MOVIMIENTO ================= */}
      <h3 style={{ marginBottom: "0.5rem" }}>➕ Nuevo movimiento</h3>
      <TransactionForm onCreated={loadData} />

      {/* ================= TABLA ================= */}
      <h2 style={{ marginTop: "3rem" }}>📋 Movimientos</h2>

      <table width="100%" cellPadding="8" style={{ marginTop: "1rem" }}>
        <thead>
          <tr>
            <th align="left">Descripción</th>
            <th align="right">Monto</th>
            <th align="left">Fecha</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t, idx) => (
            <tr key={idx}>
              <td>{t.description}</td>
              <td
                align="right"
                style={{ color: t.amount >= 0 ? "#2ecc71" : "#e74c3c" }}
              >
                ${Number(t.amount).toLocaleString()}
              </td>
              <td>{t.created_at || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ===============================
// COMPONENTES AUXILIARES
// ===============================
function KpiCard({ title, value, color, isCurrency = true }) {
  return (
    <div style={kpiCardStyle(color)}>
      <strong>{title}</strong>
      <div>
        {isCurrency ? `$${Number(value).toLocaleString()}` : value}
      </div>
    </div>
  );
}

const kpiCardStyle = (color) => ({
  flex: 1,
  border: `1px solid ${color}`,
  padding: "1rem",
  borderRadius: "8px",
  color,
  background: "#1c1c1c",
});

export default App;

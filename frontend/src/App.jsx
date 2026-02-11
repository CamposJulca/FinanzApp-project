import { useEffect, useState } from "react";
import { TransactionForm } from "./components/TransactionForm";
import { AccountsPanel } from "./components/AccountsPanel";
import { ConciliationBanner } from "./components/ConciliationBanner";

import {
  fetchTransactions,
  fetchSummary,
  fetchAccounts,
} from "./services/transactionsApi";

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    ingresos: 0,
    egresos: 0,
    saldo_contable: 0,
    saldo_cuentas: 0,
    diferencia: 0,
    estado: "OK",
    total_movimientos: 0,
  });

  const loadData = async () => {
    const [txData, summaryData] = await Promise.all([
      fetchTransactions(),
      fetchSummary(),
    ]);

    setTransactions(txData.transactions || []);
    setSummary(summaryData);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={{ padding: "2rem", background: "#121212", color: "#fff" }}>
      <h1>📊 FinanzApp</h1>

      {/* === C3.2 Conciliación === */}
      <ConciliationBanner summary={summary} />

      {/* === KPIs de FLUJO === */}
      <div style={{ display: "flex", gap: "1rem" }}>
        <KpiCard title="Ingresos del período" value={summary.ingresos} color="#2ecc71" />
        <KpiCard title="Egresos del período" value={summary.egresos} color="#e74c3c" />
        <KpiCard
          title="Resultado del período"
          value={summary.saldo_contable}
          color="#3498db"
        />
      </div>

      {/* === STOCK === */}
      <h2 style={{ marginTop: "2rem" }}>💰 Patrimonio actual</h2>
      <p style={{ color: "#aaa" }}>
        Dinero real disponible hoy (suma de cuentas)
      </p>
      <h1 style={{ color: "#2ecc71" }}>
        ${Number(summary.saldo_cuentas).toLocaleString()}
      </h1>

      {/* === Cuentas === */}
      <AccountsPanel onUpdated={loadData} />

      {/* === Movimientos === */}
      <TransactionForm onCreated={loadData} />

      <h2 style={{ marginTop: "2rem" }}>📋 Movimientos</h2>
      <table width="100%">
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id}>
              <td>{t.description}</td>
              <td
                align="right"
                style={{ color: t.amount >= 0 ? "#2ecc71" : "#e74c3c" }}
              >
                ${Number(t.amount).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function KpiCard({ title, value, color }) {
  return (
    <div
      style={{
        border: `1px solid ${color}`,
        padding: "1rem",
        borderRadius: "8px",
        color,
      }}
    >
      <strong>{title}</strong>
      <div>${Number(value).toLocaleString()}</div>
    </div>
  );
}

export default App;

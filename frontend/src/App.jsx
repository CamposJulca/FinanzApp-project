import { useEffect, useState } from "react";
import { TransactionForm } from "./components/TransactionForm";
import { fetchTransactions } from "./services/transactionsApi";

function App() {
  const [transactions, setTransactions] = useState([]);

  // ===============================
  // CARGA DE DATOS
  // ===============================
  const loadTransactions = async () => {
    try {
      const data = await fetchTransactions();
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error("Error cargando transacciones", err);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  // ===============================
  // KPIs FINANCIEROS
  // ===============================
  const ingresos = transactions
    .filter((t) => t.type === "ingreso")
    .reduce((sum, t) => sum + t.amount, 0);

  const egresos = transactions
    .filter((t) => t.type === "egreso")
    .reduce((sum, t) => sum + t.amount, 0);

  const balance = ingresos - egresos;

  const conComprobante = transactions.filter((t) => t.has_receipt).length;
  const sinComprobante = transactions.length - conComprobante;

  // ===============================
  // SALDOS POR CUENTA (OPCIÓN 1)
  // ===============================
  const saldosPorCuenta = [
    { name: "Efectivo Caja Fuerte", amount: 1200000 },
    { name: "Efectivo Caja Chica", amount: 180000 },
    { name: "Davivienda Ahorros Daniel", amount: 2350000 },
    { name: "Davivienda Ahorros Karla", amount: 4100000 },
    { name: "Ahorros Caja Social", amount: 950000 },
    { name: "Nequi Karla", amount: 320000 },
    { name: "Nequi Daniel", amount: 280000 },
    { name: "Daviplata Karla", amount: 150000 },
    { name: "Tarjeta Nu Daniel", amount: -860000 },
  ];

  const saldoTotalCuentas = saldosPorCuenta.reduce(
    (sum, acc) => sum + acc.amount,
    0
  );

  // ===============================
  // RENDER
  // ===============================
  return (
    <div style={{ padding: "2rem", background: "#121212", color: "#fff" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>📊 FinanzApp</h1>

      {/* ================= KPIs ================= */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <KpiCard title="Ingresos" value={ingresos} color="#2ecc71" />
        <KpiCard title="Egresos" value={egresos} color="#e74c3c" />
        <KpiCard title="Balance" value={balance} color="#3498db" />
        <div style={kpiCardStyle("#f1c40f")}>
          <strong>Comprobantes</strong>
          <div>✔ {conComprobante} | ✖ {sinComprobante}</div>
        </div>
      </div>

      {/* ================= SALDO ACTUAL ================= */}
      <div style={{ marginBottom: "2rem" }}>
        <h3>💰 Saldo actual consolidado</h3>
        <div
          style={{
            fontSize: "1.8rem",
            marginTop: "0.5rem",
            color: saldoTotalCuentas >= 0 ? "#2ecc71" : "#e74c3c",
          }}
        >
          ${saldoTotalCuentas.toLocaleString()}
        </div>
      </div>

      {/* ================= SALDOS POR CUENTA ================= */}
      <div style={{ marginBottom: "3rem" }}>
        <h3 style={{ marginBottom: "1rem" }}>🏦 Saldos por cuenta</h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "1rem",
          }}
        >
          {saldosPorCuenta.map((acc) => (
            <div
              key={acc.name}
              style={{
                border: "1px solid #444",
                padding: "1rem",
                borderRadius: "8px",
                background: "#1c1c1c",
              }}
            >
              <strong>{acc.name}</strong>
              <div
                style={{
                  marginTop: "0.5rem",
                  fontSize: "1.1rem",
                  color: acc.amount >= 0 ? "#2ecc71" : "#e74c3c",
                }}
              >
                ${acc.amount.toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ================= NUEVO MOVIMIENTO ================= */}
      <h3 style={{ marginBottom: "0.5rem" }}>➕ Nuevo movimiento</h3>
      <TransactionForm onCreated={loadTransactions} />

      {/* ================= TABLA ================= */}
      <h2 style={{ marginTop: "3rem" }}>📋 Movimientos</h2>

      <table width="100%" cellPadding="8" style={{ marginTop: "1rem" }}>
        <thead>
          <tr>
            <th align="left">Descripción</th>
            <th align="left">Tipo</th>
            <th align="right">Monto</th>
            <th align="left">Fecha</th>
            <th align="left">Comprobante</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t, idx) => (
            <tr key={idx}>
              <td>{t.description}</td>
              <td style={{ color: t.type === "ingreso" ? "#2ecc71" : "#e74c3c" }}>
                {t.type}
              </td>
              <td align="right">${t.amount.toLocaleString()}</td>
              <td>{t.date || "—"}</td>
              <td>{t.has_receipt ? "Sí" : "No"}</td>
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
function KpiCard({ title, value, color }) {
  return (
    <div style={kpiCardStyle(color)}>
      <strong>{title}</strong>
      <div>${value.toLocaleString()}</div>
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

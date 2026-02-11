export function ConciliationHelp({ summary }) {
  if (summary.estado === "OK") return null;

  return (
    <div
      style={{
        marginTop: "1.5rem",
        padding: "1rem",
        border: "1px dashed #f1c40f",
        borderRadius: "8px",
        background: "#1c1c1c",
      }}
    >
      <h3>🧭 ¿Cómo conciliar tus saldos?</h3>
      <ol style={{ color: "#ccc" }}>
        <li>
          Declara el saldo real de cada cuenta (efectivo, bancos, billeteras).
        </li>
        <li>
          Registra los ingresos y egresos que expliquen ese dinero.
        </li>
        <li>
          Ajusta hasta que el <strong>saldo contable</strong> coincida con el{" "}
          <strong>saldo real</strong>.
        </li>
      </ol>
      <p style={{ color: "#aaa" }}>
        👉 La conciliación garantiza que tu información financiera sea confiable.
      </p>
    </div>
  );
}

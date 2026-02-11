export function ConciliationBanner({ summary }) {
  const {
    saldo_contable,
    saldo_cuentas,
    diferencia,
    estado,
  } = summary;

  const isOk = estado === "OK";

  const bgColor = isOk ? "#0f2e1d" : "#2e0f0f";
  const borderColor = isOk ? "#2ecc71" : "#e74c3c";
  const textColor = isOk ? "#2ecc71" : "#e74c3c";

  return (
    <div
      style={{
        border: `2px solid ${borderColor}`,
        background: bgColor,
        borderRadius: "10px",
        padding: "1rem",
        marginBottom: "2rem",
      }}
    >
      <h2 style={{ color: textColor, marginBottom: "0.5rem" }}>
        {isOk ? "🟢 Conciliación correcta" : "🔴 Conciliación pendiente"}
      </h2>

      <p style={{ margin: 0 }}>
        <strong>Saldo contable:</strong>{" "}
        ${Number(saldo_contable).toLocaleString()}
      </p>
      <p style={{ margin: 0 }}>
        <strong>Saldo real (cuentas):</strong>{" "}
        ${Number(saldo_cuentas).toLocaleString()}
      </p>

      {!isOk && (
        <p style={{ marginTop: "0.5rem", color: "#f1c40f" }}>
          ⚠ Diferencia detectada:{" "}
          <strong>${Number(diferencia).toLocaleString()}</strong>
        </p>
      )}
    </div>
  );
}

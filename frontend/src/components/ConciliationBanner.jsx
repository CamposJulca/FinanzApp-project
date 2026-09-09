export function ConciliationBanner({ summary }) {
  const {
    saldo_contable,
    saldo_cuentas,
    diferencia,
    estado,
  } = summary;

  const isOk = estado === "OK";

  return (
    <div className={`conciliation-banner ${isOk ? "ok" : "pending"}`}>
      <div>
        <p className="eyebrow">Conciliación</p>
        <h2>{isOk ? "Conciliacion correcta" : "Conciliacion pendiente"}</h2>
      </div>

      <div className="conciliation-grid">
        <p>
          <span>Saldo contable</span>
          <strong>${Number(saldo_contable).toLocaleString()}</strong>
        </p>
        <p>
          <span>Saldo real</span>
          <strong>${Number(saldo_cuentas).toLocaleString()}</strong>
        </p>
      </div>

      {!isOk && (
        <p className="difference-alert">
          Diferencia detectada: <strong>${Number(diferencia).toLocaleString()}</strong>
        </p>
      )}
    </div>
  );
}

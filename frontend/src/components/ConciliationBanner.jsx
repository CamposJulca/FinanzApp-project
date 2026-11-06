import { Link } from "react-router-dom";

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

      {/* El saldo real se declara cuenta por cuenta en el módulo Cuentas;
          el contable no se edita: sale de los movimientos. */}
      <Link to="/cuentas" className="conciliation-action">
        Actualizar saldos reales →
      </Link>
    </div>
  );
}

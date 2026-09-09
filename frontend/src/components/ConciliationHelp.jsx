export function ConciliationHelp({ summary }) {
  if (summary.estado === "OK") return null;

  return (
    <div className="alert alert-warning">
      <h3>¿Cómo conciliar tus saldos?</h3>
      <ol>
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
      <p className="muted">
        La conciliación garantiza que tu información financiera sea confiable.
      </p>
    </div>
  );
}

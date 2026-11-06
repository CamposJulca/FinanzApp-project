import { useEffect } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { ConciliationBanner } from "../components/ConciliationBanner";

const money = (value) => `$${Number(value || 0).toLocaleString()}`;

export function DashboardPage() {
  const { summary, refreshSummary } = useOutletContext();

  // Al volver al resumen desde otro módulo, los números se recargan.
  useEffect(() => {
    refreshSummary();
  }, [refreshSummary]);

  return (
    <>
      <ConciliationBanner summary={summary} />

      <div className="kpi-row">
        <KpiCard
          title="Ingresos acumulados"
          value={summary.ingresos}
          tone="income"
          secondary="Histórico, todos los movimientos"
        />
        <KpiCard
          title="Egresos acumulados"
          value={summary.egresos}
          tone="expense"
          secondary="Histórico, todos los movimientos"
        />
        <KpiCard
          title="Saldo contable histórico"
          value={summary.saldo_contable}
          tone="result"
          secondary={`Incluye transferencias netas: ${money(summary.neto_transferencias)}`}
        />
      </div>

      <section className="wealth-panel">
        <div>
          <p className="eyebrow">Resumen</p>
          <h2>Patrimonio actual</h2>
          <p className="muted">
            Suma de las {summary.total_cuentas || 0} cuentas declaradas
          </p>
        </div>
        <strong>{money(summary.saldo_cuentas)}</strong>
      </section>

      <section className="data-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Accesos directos</p>
            <h2>Módulos</h2>
          </div>
          <span className="counter-pill">
            {summary.total_movimientos} movimientos
          </span>
        </div>

        <div className="shortcut-grid">
          <Shortcut
            to="/movimientos"
            title="Movimientos"
            copy="Registrar, editar y eliminar cada ingreso o egreso."
          />
          <Shortcut
            to="/cuentas"
            title="Cuentas"
            copy="Crear cuentas y declarar el saldo real de cada una."
          />
          <Shortcut
            to="/clasificacion"
            title="Clasificación"
            copy="Mantener el árbol de tipos, categorías y subcategorías."
          />
        </div>
      </section>
    </>
  );
}

function Shortcut({ to, title, copy }) {
  return (
    <Link to={to} className="shortcut-card">
      <strong>{title}</strong>
      <span>{copy}</span>
      <em>Abrir →</em>
    </Link>
  );
}

function KpiCard({ title, value, tone, secondary }) {
  return (
    <div className={`kpi-card ${tone}`}>
      <div className="kpi-topline">
        <strong>{title}</strong>
      </div>
      <div className="kpi-value">{money(value)}</div>
      {secondary && <div className="muted">{secondary}</div>}
    </div>
  );
}

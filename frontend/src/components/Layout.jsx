import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { fetchMe, fetchSummary, getCookie } from "../services/transactionsApi";

const MODULES = [
  { to: "/", label: "Resumen", end: true },
  { to: "/movimientos", label: "Movimientos" },
  { to: "/cuentas", label: "Cuentas" },
  { to: "/clasificacion", label: "Clasificación" },
  { to: "/presupuesto", label: "Presupuesto" },
];

const EMPTY_SUMMARY = {
  ingresos: 0,
  egresos: 0,
  neto_transferencias: 0,
  saldo_contable: 0,
  saldo_cuentas: 0,
  diferencia: 0,
  estado: "OK",
  total_movimientos: 0,
  total_cuentas: 0,
};

/**
 * Cascarón común: cabecera, navegación entre módulos y estado compartido
 * (usuario y resumen). Cada módulo recibe `refresh` para recargar el resumen
 * tras escribir, de modo que la cabecera nunca queda desfasada.
 */
export function Layout() {
  const [currentUser, setCurrentUser] = useState(null);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);

  const refreshSummary = useCallback(async () => {
    try {
      setSummary(await fetchSummary());
    } catch {
      // El resumen es informativo: si falla no bloqueamos el módulo activo.
    }
  }, []);

  useEffect(() => {
    let active = true;

    Promise.all([fetchMe(), fetchSummary()])
      .then(([user, resumen]) => {
        if (!active) return;
        setCurrentUser(user);
        setSummary(resumen);
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, []);

  const conciliado = summary.estado === "OK";

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Panel de control</p>
          <h1>FinanzApp</h1>
          <p className="header-copy">
            Panel financiero para vigilar saldos y registrar cada movimiento con
            precisión.
          </p>
        </div>

        <div className="header-side">
          <div className={`status-chip ${conciliado ? "" : "warn"}`}>
            <span className="status-dot" />
            <span>{conciliado ? "Sistema conciliado" : "Revisar conciliación"}</span>
          </div>
          {currentUser && (
            <p className="session-line">
              Sesión: <strong>{currentUser.username}</strong>
              {" · "}
              <form method="post" action="/logout/" className="logout-form">
                <input
                  type="hidden"
                  name="csrfmiddlewaretoken"
                  value={getCookie("csrftoken") || ""}
                />
                <button type="submit" className="logout-link">
                  Salir
                </button>
              </form>
            </p>
          )}
        </div>
      </header>

      <nav className="module-nav" aria-label="Módulos">
        {MODULES.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `module-link${isActive ? " active" : ""}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <main className="module-body">
        <Outlet context={{ currentUser, summary, refreshSummary }} />
      </main>
    </div>
  );
}

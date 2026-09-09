import { useEffect, useState } from "react";
import {
  fetchAccounts,
  updateAccountBalance,
} from "../services/transactionsApi";

export function AccountsPanel({ onUpdated }) {
  const [accounts, setAccounts] = useState([]);
  const [editing, setEditing] = useState({});

  const loadAccounts = async () => {
    const data = await fetchAccounts();
    setAccounts(data.accounts);
  };

  useEffect(() => {
    let isMounted = true;

    fetchAccounts().then((data) => {
      if (!isMounted) return;
      setAccounts(data.accounts);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSave = async (accountId) => {
    const value = editing[accountId];
    await updateAccountBalance(accountId, value);
    setEditing({});
    await loadAccounts();
    onUpdated(); // refresca summary
  };

  return (
    <section className="data-panel accounts-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Cuentas</p>
          <h2>Fuentes de dinero</h2>
        </div>
        <span className="counter-pill">{accounts.length} cuentas</span>
      </div>

      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th align="left">Fuente</th>
              <th align="right">Saldo actual</th>
              <th align="right">Accion</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((acc) => (
              <tr key={acc.id}>
                <td className="source-cell">{acc.name}</td>
                <td align="right">
                  <input
                    className="money-input"
                    type="number"
                    value={
                      editing[acc.id] !== undefined
                        ? editing[acc.id]
                        : acc.saldo_real
                    }
                    onChange={(e) =>
                      setEditing({
                        ...editing,
                        [acc.id]: e.target.value,
                      })
                    }
                  />
                </td>
                <td align="right">
                  <button type="button" onClick={() => handleSave(acc.id)}>
                    Guardar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="panel-note">
        El saldo del aplicativo es la suma de estas fuentes. Cada casilla
        queda editable para declarar el dinero disponible.
      </p>
    </section>
  );
}

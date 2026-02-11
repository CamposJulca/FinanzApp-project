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
    loadAccounts();
  }, []);

  const handleSave = async (accountId) => {
    const value = editing[accountId];
    await updateAccountBalance(accountId, value);
    setEditing({});
    await loadAccounts();
    onUpdated(); // refresca summary
  };

  return (
    <div style={{ marginTop: "2rem" }}>
      <h2>🏦 Cuentas (saldo real)</h2>

      <table width="100%" cellPadding="8">
        <thead>
          <tr>
            <th align="left">Cuenta</th>
            <th align="right">Saldo real</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((acc) => (
            <tr key={acc.id}>
              <td>{acc.name}</td>
              <td align="right">
                <input
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
                  style={{ width: "140px" }}
                />
              </td>
              <td>
                <button onClick={() => handleSave(acc.id)}>
                  Guardar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p style={{ marginTop: "0.5rem", color: "#aaa" }}>
        👉 Este saldo se declara manualmente y representa el dinero real
        disponible en cada fuente.
      </p>
    </div>
  );
}

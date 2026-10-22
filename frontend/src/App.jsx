import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { MovimientosPage } from "./pages/MovimientosPage";
import { CuentasPage } from "./pages/CuentasPage";
import { ClasificacionPage } from "./pages/ClasificacionPage";
import { PresupuestoPage } from "./pages/PresupuestoPage";
import "./App.css";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="movimientos" element={<MovimientosPage />} />
        <Route path="cuentas" element={<CuentasPage />} />
        <Route path="clasificacion" element={<ClasificacionPage />} />
        <Route path="presupuesto" element={<PresupuestoPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;

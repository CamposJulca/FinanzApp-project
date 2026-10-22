# Presupuesto fase 1B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir topes históricos por hogar y un reporte/UI mensual de consumo y proyección.

**Architecture:** `core` conserva el modelo y las garantías PostgreSQL; `transactions` resuelve hogares, CRUD y cálculos; React consume el contrato sin recalcular histórico. El prorrateo queda aislado en una función pura y no altera reportes anteriores.

**Tech Stack:** Django 6, Django REST Framework, PostgreSQL, React/Vite.

**Spec:** `docs/superpowers/specs/2026-10-22-presupuesto-fase1b-design.md`

## Global Constraints

- Trabajar en `feat/presupuesto-fase1b`; commits locales, sin push.
- No aplicar migraciones a producción.
- Probar exclusión en PostgreSQL mediante `test_finanzapp_prod`.
- No modificar `Account`, `summary()` ni la lista de movimientos para prorratear.
- Un solo mes calendario por consulta de consumo.

## Review Focus

- Vigencias abiertas/cerradas en sus bordes inclusivos.
- Hogares múltiples, membresía y acceso cruzado.
- Coberturas cuya fecha efectiva cae fuera del periodo.
- Proyección en rangos parciales presentes y pasados.
- Rutas `budgets/` antes de la ruta genérica `<int:pk>/`.

---

### Task 1: Esquema y migraciones

**Files:** `backend/core/models.py`, `backend/core/migrations/0013_*.py`, `0014_*.py`, `0015_*.py`, `backend/core/tests.py`

- [ ] Escribir pruebas fallidas de Budget, validaciones, solapamiento y backfill.
- [ ] Agregar `Transaction.household`, migrar exactamente 264 filas, crear índice, Budget, `btree_gist` y exclusión.
- [ ] Ejecutar pruebas focalizadas sobre PostgreSQL hasta verde.

### Task 2: Hogar en movimientos y CRUD de Budget

**Files:** `backend/transactions/serializers.py`, `backend/transactions/views.py`, `backend/transactions/urls.py`, `backend/transactions/tests.py`

- [ ] Escribir pruebas fallidas de derivación/ambigüedad, legs, membresía y CRUD/vigencias.
- [ ] Implementar resolución de hogar, escrituras explícitas y POST futuro atómico.
- [ ] Ejecutar pruebas focalizadas hasta verde.

### Task 3: Servicio y endpoint de consumo

**Files:** `backend/transactions/budgets.py`, `backend/transactions/views.py`, `backend/transactions/urls.py`, `backend/transactions/tests.py`

- [ ] Escribir pruebas fallidas de prorrateo, aislamiento, topes, periodos y proyección.
- [ ] Implementar `prorated_amount` y el reporte mensual.
- [ ] Ejecutar pruebas focalizadas hasta verde.

### Task 4: UI de presupuesto

**Files:** `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx`, `frontend/src/services/transactionsApi.js`, `frontend/src/pages/PresupuestoPage.jsx`, CSS.

- [ ] Implementar ruta, tabla, estados, avisos y modal según el contrato aprobado.
- [ ] Ejecutar lint y build hasta verde.

### Task 5: Verificación integral

- [ ] Ejecutar `makemigrations --check`, suite backend PostgreSQL, lint y build.
- [ ] Revisar diff y el contrato requisito por requisito.
- [ ] Crear commits locales y confirmar que no hubo push ni migraciones en producción.

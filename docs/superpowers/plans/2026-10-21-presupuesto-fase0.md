# Presupuesto fase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporar moneda, transferencias explícitas y fecha efectiva sin alterar la clasificación existente.

**Architecture:** Los modelos viven en `core`; DRF crea y borra transferencias atómicamente en `transactions`. Los legs siguen siendo transacciones para afectar cuentas, pero quedan protegidos de mutación individual y excluidos de métricas de ingreso/gasto y pendientes.

**Tech Stack:** Django 6, Django REST Framework, PostgreSQL, React/Vite.

**Spec:** `docs/superpowers/specs/2026-10-21-presupuesto-fase0-design.md`

## Global Constraints

- No commit ni push.
- No aplicar migraciones a la base configurada.
- No modificar la lógica de clasificación de movimientos normales.
- `currency="COP"` es provisional; no inferir `PEN` todavía.
- No ofrecer edición de transferencias.

## Review Focus

- Usuario autenticado fuera del hogar: rechazar creación.
- Cuenta cuyo propietario no pertenece al hogar: rechazar creación.
- Edición o borrado individual de un leg: rechazar sin mutar el par.
- Cuenta referenciada por transferencia: `PROTECT` incluso con borrado forzado.
- Payload histórico sin fecha efectiva: derivarla sin romper creación.

---

### Task 1: Esquema, moneda y migraciones

**Files:**
- Modify: `backend/core/models.py`
- Modify: `backend/core/admin.py`
- Modify: `backend/transactions/serializers.py`
- Create: `backend/core/migrations/0007_*.py`
- Create: `backend/core/migrations/0008_*.py`
- Create: `backend/core/migrations/0009_*.py`
- Test: `backend/core/tests.py`
- Test: `backend/transactions/tests.py`

**Interfaces:**
- Produces: `Transfer`, `Account.currency`, `Transaction.transfer`, `Transaction.fecha_efectiva` y compatibilidad con payloads sin fecha efectiva.

- [ ] Escribir en `core/tests.py` pruebas de invariantes y migración histórica, y en `transactions/tests.py` la prueba del payload histórico sin `fecha_efectiva`.
- [ ] Ejecutarlas y verificar que fallan por ausencia del esquema.
- [ ] Implementar modelos, derivar `fecha_efectiva` desde `created_at` o la fecha local actual y generar las migraciones nullable y de datos.
- [ ] Verificar que las pruebas pasan antes de generar la migración final `NOT NULL` con índices.
- [ ] Generar `0009` sin aplicarla y repetir las pruebas focalizadas.
- [ ] Ejecutar las pruebas focalizadas hasta que pasen.

### Task 2: Serializer y API de transferencias

**Files:**
- Modify: `backend/transactions/serializers.py`
- Modify: `backend/transactions/views.py`
- Modify: `backend/transactions/urls.py`
- Test: `backend/transactions/tests.py`

**Interfaces:**
- Consumes: `Transfer` y campos de Task 1.
- Produces: `TransferSerializer`, creación atómica y endpoint de borrado sin edición.

- [ ] Escribir pruebas de creación, autorización, signos, metadatos y borrado.
- [ ] Verificar fallos esperados.
- [ ] Implementar serializer, vistas y rutas mínimas.
- [ ] Ejecutar pruebas focalizadas hasta verde.

### Task 3: Blindaje de legs y coherencia de clasificación

**Files:**
- Modify: `backend/transactions/serializers.py`
- Modify: `backend/transactions/views.py`
- Test: `backend/transactions/tests.py`

**Interfaces:**
- Consumes: derivación de `fecha_efectiva` de Task 1.
- Produces: rechazo de update/delete de legs y regresión cubierta para legs sin subcategoría.

- [ ] Escribir pruebas para PATCH/PUT/DELETE de legs y para confirmar que un leg con `subcategory=NULL` no dispara la validación de signo/rama.
- [ ] Verificar que fallan por la conducta actual.
- [ ] Implementar el guard; mantener intacta la validación de signo para movimientos normales y documentar su retorno temprano para legs.
- [ ] Ejecutar pruebas focalizadas hasta verde.

### Task 4: Agregados y pendientes

**Files:**
- Modify: `backend/transactions/views.py`
- Modify si corresponde: otros archivos hallados mediante búsqueda global.
- Test: `backend/transactions/tests.py`

**Interfaces:**
- Produces: ingreso/gasto sin transferencias y operaciones de clasificación que ignoran legs.

- [ ] Escribir pruebas de agregados, impacto, desclasificación y reasignación.
- [ ] Verificar los fallos esperados.
- [ ] Añadir filtros `transfer__isnull=True` solo donde la semántica lo exige.
- [ ] Conservar legs en saldos por cuenta y documentar ese punto.
- [ ] Ejecutar pruebas focalizadas hasta verde.

### Task 5: Moneda en API y UI

**Files:**
- Modify: `backend/transactions/serializers.py`
- Modify: `frontend/src/pages/CuentasPage.jsx`
- Test: `backend/transactions/tests.py`

**Interfaces:**
- Produces: lectura/escritura de `currency` en cuentas.

- [ ] Escribir prueba API del default y actualización de moneda.
- [ ] Verificar fallo esperado.
- [ ] Exponer el campo en serializer y formulario/tabla.
- [ ] Ejecutar prueba backend y validación frontend.

### Task 6: Verificación integral

**Files:**
- Inspect: working tree completo.

**Interfaces:**
- Consumes: todas las tareas.

- [ ] Ejecutar comprobación de migraciones pendientes sin aplicarlas.
- [ ] Ejecutar suite backend completa.
- [ ] Ejecutar tests/build disponibles del frontend.
- [ ] Revisar diff y confirmar ausencia de cambios ajenos o migraciones aplicadas.

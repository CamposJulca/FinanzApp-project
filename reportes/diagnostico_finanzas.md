# Diagnóstico técnico y financiero de FinanzApp

**Fecha del diagnóstico:** 2026-10-20 (UTC)  
**Rama inspeccionada:** `feat/clasificacion-guardrails`  
**Alcance:** repositorio, procesos locales y base PostgreSQL productiva, todo en modo de solo lectura.  
**Privacidad:** usuarios anonimizados; no se muestran credenciales, nombres de cuentas, números de cuenta/tarjeta ni movimientos individuales. Importes en pesos colombianos (COP).

## Metodología y cautelas

- El código, Git, procesos y puertos se inspeccionaron sin cambiar rama, archivos existentes ni estado del repositorio.
- Las consultas de datos fueron exclusivamente `SELECT`, con PostgreSQL forzado a `default_transaction_read_only=on`.
- Se trabajó con conteos y sumas agregadas. Los posibles duplicados se cuantifican, pero no se enumeran.
- Solo existen datos entre el 4 de agosto y el 19 de octubre de 2026. Agosto empieza el día 4 y octubre está en curso; septiembre es el único mes calendario completo.
- Los importes positivos se interpretan como ingresos y los negativos como gastos, coherente con el código actual.
- Las cifras de octubre y los promedios están muy afectados por $88.562.000 clasificados en `OTROS GASTOS` y por posibles duplicados. No deben convertirse directamente en presupuesto.

## Parte 1 — Entender la app

### 1. Stack, arranque y estado actual

| Capa | Tecnología / configuración observada |
|---|---|
| Backend | Python 3.12, Django 6.x, Django REST Framework, Gunicorn en ejecución; WhiteNoise para estáticos y `django-cors-headers`. |
| Frontend | React 19, React Router 7 y Vite 7 (paquete `rolldown-vite`); SPA bajo `/transacciones/`. |
| Base de datos | PostgreSQL 16.15; driver `psycopg`. La base consultada es PostgreSQL, aunque queda un `db.sqlite3` histórico y referencias antiguas a MongoDB que no son el almacenamiento activo. |
| Autenticación | Sesiones Django; middleware obliga inicio de sesión; API con `IsAuthenticated`. |
| Empaquetado | `docker-compose.yml` define el backend y espera una red externa `finanzapp-net`; hay un compose separado para PostgreSQL. |

**Cómo se levanta según el repositorio**

- Backend por Docker: `docker compose up --build` desde la raíz, después de disponer de `.env`, red externa y PostgreSQL accesible. El compose publica `8090:8090`.
- La imagen declara `python manage.py runserver 0.0.0.0:8090`. En el entorno observado, producción/local está levantada con Gunicorn y no con el comando del Dockerfile.
- Frontend en desarrollo: `npm install` y `npm run dev` dentro de `frontend`; Vite usa el puerto 8029 y proxy a `127.0.0.1:8090`.
- Frontend integrado: `npm run build`; Django sirve el `dist` mediante WhiteNoise/plantilla SPA.
- No se ejecutó ninguno de esos comandos durante este diagnóstico.

**Estado observado al 2026-10-20**

| Elemento | Estado |
|---|---|
| FinanzApp backend | **Corriendo**: Gunicorn, 3 workers, `0.0.0.0:8090`; una petición a `/` respondió `302` hacia `/login/`. |
| Frontend Vite 8029 | **No corriendo**; no hubo respuesta en ese puerto. La SPA compilada puede estar siendo servida por Django. |
| FinanzApp en Docker | **No aparece** en `docker ps`; el proceso corre directamente desde `backend/.venv`. |
| PostgreSQL | **Corriendo** en `0.0.0.0:5432`; conexión efectiva a PostgreSQL 16.15. |
| Otros contenedores/puertos | Existen varios servicios ajenos al proyecto; no se tocaron. |

### 2. Modelo de datos actual

| Modelo / tabla | Campos clave | Observación funcional |
|---|---|---|
| Usuario / `auth_user` | `id`, `username`, datos de autenticación y perfil | Usuario estándar de Django. Hay 2 usuarios; se anonimizan como Usuario 1 y 2. |
| Hogar / `core_household` | `id`, `name`, `created_at`; M:N con usuarios | Agrupa miembros, pero las transacciones y cuentas siguen perteneciendo directamente a un usuario. |
| Cuenta / `core_account` | `id`, `user_id`, `name`, `saldo_real`, `created_at` | `saldo_real` es manual para conciliación; no es un saldo derivado ni histórico. |
| Tipo / `core_transactiontype` | `id`, `tipo`, `subtipo`, `description` | Cuatro ramas fijas: ingreso/egreso × fijo/variable. |
| Categoría / `core_transactioncategory` | `id`, `type_id`, `name` | Nivel intermedio del árbol; nombre único dentro del tipo. |
| Subcategoría / `core_transactionsubcategory` | `id`, `category_id`, `name` | Hoja asignable al movimiento; nombre único dentro de la categoría. |
| Movimiento / `core_transaction` | `id`, `user_id`, `account_id`, `subcategory_id` nullable, `amount`, `description`, `created_at`, `registered_by` | El signo representa ingreso/gasto. No tiene fuente de ingreso estructurada, recurrencia, comercio, moneda, estado de conciliación ni identificador externo de importación. |

**Volumen estructural:** 1 hogar, 2 usuarios, 9 cuentas, 264 movimientos, 4 tipos, 20 categorías y 82 subcategorías.

No existen modelos/tablas específicos de presupuesto, meta, deuda, crédito, cuota, tasa, calendario de amortización, proyección o fuente contractual de ingreso.

### 3. Rama actual frente a `main`

La rama actual es `feat/clasificacion-guardrails`. Está **1 commit por delante de `main`**:

`a12ac40 feat(clasificacion): coherencia de signo y borrado con impacto declarado`

Resumen del diff `main...HEAD`: **14 archivos, 1.775 inserciones y 156 eliminaciones**.

Cambios principales:

- Migra `TransactionType` desde un nombre libre a las cuatro parejas controladas `tipo`/`subtipo`.
- Añade `registered_by` para identificar quién registró movimientos en el hogar configurado.
- Refuerza que el signo del monto coincida con la rama INGRESO/EGRESO, tanto en API como en la interfaz.
- Convierte transacciones, cuentas y clasificación a serializers/vistas CRUD más completas, siempre filtradas por usuario.
- Añade árbol de clasificación editable, rutas legibles y contadores de uso.
- Antes de borrar categorías/subcategorías, calcula el impacto y exige decidir entre desclasificar o reasignar; usa transacciones atómicas.
- Añade guardas al mover categorías/subcategorías para no cruzar ramas ingreso/egreso con movimientos incompatibles.
- Mejora conciliación, cuentas, SPA, seguridad/configuración y la UX de movimientos/clasificación.

El alcance real es mayor que el título del commit: incluye migraciones, refactor sustancial de API y cambios de interfaz. No se cambió de rama ni se ejecutaron migraciones.

### 4. Capacidades financieras existentes

| Capacidad | Estado | Evidencia / límite |
|---|---|---|
| Presupuestos | **No** | No hay modelo, periodo, límite por categoría ni seguimiento presupuesto-real. |
| Metas de ahorro | **Parcial** | Existe una categoría de gasto `AHORRO`, pero no una meta con monto objetivo, fecha, aportes y saldo. |
| Deudas/créditos | **Parcial** | Hay categoría/subcategorías de créditos y pagos registrados, pero no principal, saldo, tasa, plazo, cuota contractual ni amortización. |
| Amortización | **No** | No hay cronograma, separación capital/interés/seguros ni abonos extraordinarios. |
| Proyecciones | **No** | Solo resumen histórico acumulado; no hay escenarios o flujo futuro. |
| Ingresos por fuente | **Parcial** | La jerarquía permite etiquetas como nómina, efectivo o ingreso genérico, pero no existe entidad `IncomeSource`, contrato, pagador, periodicidad ni vigencia. |
| Conciliación | **Sí, básica** | Compara suma contable de movimientos contra suma manual de `saldo_real`; no conserva cortes históricos. |

## Parte 2 — Diagnóstico de los datos registrados

### 5. Cobertura temporal y registros

**Rango:** 2026-08-04 a 2026-10-19, 264 movimientos en 3 meses.

| Mes | Registros | Días con actividad | Primera fecha | Última fecha | Estado de cobertura |
|---|---:|---:|---|---|---|
| 2026-08 | 67 | 22 | 2026-08-04 | 2026-08-31 | Parcial al inicio (faltan días 1–3). |
| 2026-09 | 142 | 25 | 2026-09-01 | 2026-09-30 | Único mes calendario completo. |
| 2026-10 | 55 | 4 | 2026-10-02 | 2026-10-19 | Mes en curso y captura concentrada en pocos días. |

| Usuario anonimizado | Registros | Desde | Hasta | Ingresos | Gastos |
|---|---:|---|---|---:|---:|
| Usuario 1 | 264 | 2026-08-04 | 2026-10-19 | $340.625.800 | $170.698.100 |
| Usuario 2 | 0 | — | — | $0 | $0 |

Toda la historia financiera está asociada a un solo usuario, aunque el hogar tiene más de uno. `registered_by` está completo en los 264 movimientos y permite autoría operativa, pero no sustituye la propiedad financiera por persona.

### 6. Ingresos por mes y fuente/categoría

| Mes | Fuente / categoría | Registros | Ingresos |
|---|---|---:|---:|
| 2026-08 | Salario — nómina principal | 2 | $17.948.000 |
| 2026-08 | Ingreso — efectivo | 1 | $13.000.000 |
| 2026-09 | Sin categoría/fuente | 2 | $110.000.000 |
| 2026-09 | Ingreso genérico | 1 | $50.000.000 |
| 2026-09 | Salario — nómina principal | 4 | $19.815.000 |
| 2026-09 | Salario — segunda nómina | 1 | $9.967.800 |
| 2026-10 | Sin categoría/fuente | 3 | $100.460.000 |
| 2026-10 | Ingreso genérico | 1 | $10.465.000 |
| 2026-10 | Salario — nómina principal | 2 | $8.970.000 |

**Totales por fuente en todo el rango:**

| Fuente / categoría | Registros | Total | % de ingresos |
|---|---:|---:|---:|
| Sin categoría/fuente | 5 | $210.460.000 | 61,79% |
| Ingreso genérico | 2 | $60.465.000 | 17,75% |
| Salario — nómina principal | 8 | $46.733.000 | 13,72% |
| Ingreso — efectivo | 1 | $13.000.000 | 3,82% |
| Salario — segunda nómina | 1 | $9.967.800 | 2,93% |
| **Total** | **17** | **$340.625.800** | **100,00%** |

La fuente de ingresos no es suficientemente confiable para proyectar: 61,79% carece de clasificación y otro 17,75% es genérico. Antes de diseñar una estrategia, deben distinguirse nómina, contrato con planilla, reintegros, transferencias entre cuentas, venta de activos y préstamos recibidos.

### 7. Gastos mensuales y fijos frente a variables

La separación usa el `subtipo` almacenado, no una reclasificación inferida.

| Mes | Gastos fijos | Gastos variables | Gasto total | % fijo |
|---|---:|---:|---:|---:|
| 2026-08 | $3.461.000 | $16.213.000 | $19.674.000 | 17,59% |
| 2026-09 | $6.241.000 | $18.470.200 | $24.711.200 | 25,26% |
| 2026-10 parcial | $7.954.000 | $118.358.900 | $126.312.900 | 6,30% |
| **Total** | **$17.656.000** | **$153.042.100** | **$170.698.100** | **10,34%** |

**Gastos por mes y categoría**

| Mes | Categoría | Tipo | Total |
|---|---|---|---:|
| 2026-08 | Alimentación | Variable | $3.541.000 |
| 2026-08 | Cuidado personal | Variable | $3.067.000 |
| 2026-08 | Otros gastos | Variable | $2.916.000 |
| 2026-08 | Casa | Fijo + variable | $2.570.000 |
| 2026-08 | Salud | Variable | $1.744.000 |
| 2026-08 | Empresa | Variable | $1.300.000 |
| 2026-08 | Carro | Fijo | $1.061.000 |
| 2026-08 | Tecnología | Variable | $856.000 |
| 2026-08 | Vehículos | Variable | $806.000 |
| 2026-08 | Ahorro | Variable | $500.000 |
| 2026-08 | Moto + recreación + deporte + créditos | Mixto | $1.313.000 |
| 2026-09 | Casa | Fijo + variable | $3.186.000 |
| 2026-09 | Alimentación | Variable | $4.284.300 |
| 2026-09 | Gestión personal | Fijo | $2.839.000 |
| 2026-09 | Vehículos | Variable | $2.327.000 |
| 2026-09 | Otros gastos | Variable | $2.198.000 |
| 2026-09 | Créditos | Variable | $1.695.000 |
| 2026-09 | Cuidado personal | Variable | $1.556.000 |
| 2026-09 | Recreación | Variable | $1.497.000 |
| 2026-09 | Salud | Variable | $1.413.000 |
| 2026-09 | Tecnología | Variable | $1.398.900 |
| 2026-09 | Deporte | Variable | $1.060.000 |
| 2026-09 | Ahorro | Variable | $500.000 |
| 2026-09 | Colegio, carro y mascotas | Mixto | $757.000 |
| 2026-10 | Otros gastos | Variable | $88.562.000 |
| 2026-10 | Casa | Fijo + variable | $19.136.000 |
| 2026-10 | Créditos | Variable | $10.650.000 |
| 2026-10 | Alimentación | Variable | $3.340.000 |
| 2026-10 | Vehículos | Variable | $2.091.000 |
| 2026-10 | Deporte | Variable | $1.184.900 |
| 2026-10 | Cuidado personal | Variable | $510.000 |
| 2026-10 | Salud | Variable | $386.000 |
| 2026-10 | Gestión personal, recreación, moto, tecnología y mascotas | Mixto | $452.000 |

Los fijos identificados incluyen administración, cuidado doméstico, parqueadero, planes celulares, colegio, impuestos y seguros de vehículos. **Los créditos están clasificados como variables**, aunque sus cuotas normalmente deberían modelarse como compromiso fijo o como deuda separada. No se observan categorías explícitas de arriendo, energía, agua, gas o suscripciones; podrían estar ausentes o incluidas bajo `CASA`/`OTROS GASTOS`.

### 8. Promedios mensuales y categorías principales

| Ventana solicitada | Meses con datos | Gasto incluido | Promedio por mes con datos | Promedio diluido en la ventana completa |
|---|---:|---:|---:|---:|
| Últimos 3 meses | 3 | $170.698.100 | $56.899.366,67 | $56.899.366,67 |
| Últimos 6 meses | 3 | $170.698.100 | $56.899.366,67 | $28.449.683,33 |
| Últimos 12 meses | 3 | $170.698.100 | $56.899.366,67 | $14.224.841,67 |

Los promedios de 6 y 12 meses **no son estadísticamente representativos**: faltan 3 y 9 meses, respectivamente. El promedio observado también está distorsionado por octubre. Como referencia operativa:

- Promedio agosto–septiembre: **$22.192.600/mes**; agosto empieza el día 4 y solo septiembre está completo.
- Septiembre, único mes calendario completo: **$24.711.200**.
- Promedio de los 3 meses excluyendo toda la categoría `OTROS GASTOS`: **$25.674.033/mes**. Es una sensibilidad, no una corrección contable.
- Gasto fijo promedio observado: **$5.885.333/mes**; septiembre registró $6.241.000.

**Top 10 categorías de gasto (rango completo)**

| # | Categoría | Tipo | Registros | Total | % del gasto |
|---:|---|---|---:|---:|---:|
| 1 | Otros gastos | Variable | 30 | $93.676.000 | 54,88% |
| 2 | Casa | Fijo | 6 | $12.534.000 | 7,34% |
| 3 | Créditos | Variable | 5 | $12.485.000 | 7,31% |
| 4 | Casa | Variable | 16 | $12.358.000 | 7,24% |
| 5 | Alimentación | Variable | 38 | $11.165.300 | 6,54% |
| 6 | Vehículos | Variable | 51 | $5.224.000 | 3,06% |
| 7 | Cuidado personal | Variable | 22 | $5.133.000 | 3,01% |
| 8 | Salud | Variable | 11 | $3.543.000 | 2,08% |
| 9 | Gestión personal | Fijo | 7 | $2.949.000 | 1,73% |
| 10 | Deporte | Variable | 16 | $2.597.900 | 1,52% |

### 9. Balance mensual y ahorro

| Mes | Ingresos | Gastos | Balance (ingresos − gastos) | Ahorro etiquetado |
|---|---:|---:|---:|---:|
| 2026-08 | $30.948.000 | $19.674.000 | **$11.274.000** | $500.000 |
| 2026-09 | $189.782.800 | $24.711.200 | **$165.071.600** | $500.000 |
| 2026-10 parcial | $119.895.000 | $126.312.900 | **-$6.417.900** | $0 |
| **Acumulado contable** | **$340.625.800** | **$170.698.100** | **$169.927.700** | **$1.000.000** |

El balance acumulado **no equivale a ahorro disponible**: $210.460.000 de ingresos no tienen fuente y pueden incluir transferencias, préstamos o duplicados. Además, la suma de saldos reales declarados de las 9 cuentas es $0, por lo cual la conciliación no respalda el saldo contable. El único ahorro explícito son dos registros por $500.000, total $1.000.000; la app no guarda saldo de una meta o fondo.

### 10. Deudas y créditos registrados

No existe una tabla de deuda; solo se observan pagos bajo `CREDITOS`.

| Mes | Instrumento anonimizado | Pagos | Total pagado |
|---|---|---:|---:|
| 2026-08 | Tarjeta A | 1 | $140.000 |
| 2026-09 | Compra de cartera | 1 | $1.695.000 |
| 2026-10 | Compra de cartera | 1 | $10.000.000 |
| 2026-10 | Tarjeta B | 1 | $420.000 |
| 2026-10 | Tarjeta A | 1 | $230.000 |
| **Total** | — | **5** | **$12.485.000** |

| Dato requerido | Disponibilidad |
|---|---|
| Saldo de capital | No disponible. |
| Cuota contractual | No disponible; los valores observados son pagos, no necesariamente cuotas. |
| Tasa EA/MV | No disponible. |
| Plazo y fecha final | No disponibles. |
| Capital/interés/seguros | No separados. |
| Tabla de amortización | No existe. |

No es posible evaluar endeudamiento, tasa de esfuerzo ni conveniencia de abonos extraordinarios con el modelo actual.

### 11. Calidad de los datos

| Hallazgo | Resultado | Impacto |
|---|---:|---|
| Movimientos sin subcategoría | 5 de 264 (1,89%) | Todos son ingresos y suman $210.460.000: 61,79% de los ingresos queda sin fuente. |
| Incompatibilidad signo vs rama | 0 | La clasificación existente es coherente con ingreso/egreso. |
| Posibles duplicados exactos | 3 grupos / 3 registros excedentes | Impacto bruto potencial: $43.320.000; $43.090.000 en gastos y $230.000 en ingresos. Requieren revisión manual, no borrado automático. |
| Descripciones vacías | 0 | Cobertura completa. |
| `registered_by` vacío | 0 | Cobertura completa. |
| Montos en cero | 0 | Sin registros nulos económicamente. |
| Meses incompletos | Agosto y octubre | Solo septiembre puede tratarse como mes calendario completo. |
| Categoría redundante | `CASA` existe como fija y variable | Puede ser válido, pero complica reportes si no se muestra siempre el subtipo. |
| Subcategorías repetidas | `IMPUESTO` en 3 categorías; `SOAT` y `PARQUEADERO` en 2 | Son válidas por contexto, pero nunca deben analizarse sin la ruta completa. |
| Categoría demasiado amplia | `OTROS GASTOS`: $93.676.000 (54,88% del gasto) | Oculta la finalidad económica y domina el promedio; octubre concentra $88.562.000. |
| Ahorro tratado como gasto variable | $1.000.000 | Mezcla consumo con transferencia patrimonial; debería modelarse como aporte a meta/cuenta. |
| Créditos tratados como variables | $12.485.000 | Oculta obligación fija y no separa amortización de intereses. |
| Conciliación | 9 cuentas con saldo real agregado $0 vs saldo contable $169.927.700 | La capacidad de ahorro no puede confirmarse mediante saldos reales. |

**Prioridades de saneamiento antes de fijar una estrategia:**

1. Revisar los 3 duplicados exactos y documentar si son legítimos, sin eliminarlos hasta confirmación.
2. Clasificar los 5 ingresos por $210.460.000 y marcar transferencias internas para excluirlas de ingreso real.
3. Desglosar `OTROS GASTOS`, sobre todo los $88.562.000 de octubre, entre consumo, transferencias, compra de activos, impuestos o deuda.
4. Actualizar `saldo_real` por cuenta y conciliar contra movimientos de apertura/transferencias.
5. Reclasificar ahorro como transferencia a fondo/meta y créditos como obligaciones con componente de capital e interés.
6. Capturar al menos 3 meses completos adicionales; para estacionalidad y provisión fiscal, idealmente 12 meses.

## Parte 3 — Diseño recomendado del modelo futuro

### Tablas o campos faltantes

| Necesidad | Tabla(s) / campos propuestos | Propósito |
|---|---|---|
| Proyección de ingresos por fuente | `income_source(id, household_id, owner_user_id, name, source_type[NOMINA, CONTRATO_PLANILLA, HONORARIOS, OTRO], payer, gross_amount, net_amount, frequency, start_date, end_date, confidence, active)`; FK opcional `transaction.income_source_id` | Separar nómina estable de contrato, registrar vigencia y proyectar flujo neto por fuente. |
| Contrato con planilla | `contract_income_detail(income_source_id, contract_value, payment_schedule, planilla_base, health_rate, pension_rate, arl_rate, withholding_rate, expected_payment_day)` | Calcular aportes, retenciones y neto esperado sin mezclarlos con nómina. |
| Provisión de renta | `tax_provision(id, household_id, tax_year, income_source_id, taxable_income, deductible_amount, estimated_tax, provision_rate, amount_reserved, due_date, status)` y movimientos/aportes asociados | Reservar mensualmente impuestos y comparar provisión con obligación estimada. |
| Fondo de emergencia | `savings_goal(id, household_id, name, goal_type, target_amount, target_months, target_date, current_amount, linked_account_id, priority, status)`; `goal_contribution(goal_id, transaction_id, amount, date)` | Medir meses de gasto esencial cubiertos y progreso real, sin contar aportes como consumo. |
| Presupuesto | `budget(id, household_id, period_start, period_end, status)`; `budget_line(budget_id, category_id, planned_amount, essential, rollover)` | Comparar plan vs ejecución por categoría y separar gasto esencial/discrecional. |
| Deuda / crédito | `debt(id, household_id, owner_user_id, lender, debt_type, original_principal, current_principal, annual_effective_rate, periodic_rate, term_months, start_date, payment_day, regular_payment, insurance_payment, fees, status)` | Conocer saldo, costo, cuota y esfuerzo mensual. No guardar números completos de producto; solo alias y últimos 4 si fueran imprescindibles. |
| Amortización | `debt_installment(id, debt_id, due_date, opening_balance, scheduled_payment, principal, interest, insurance, fees, extra_payment, closing_balance, status)`; FK desde movimiento | Construir tabla real/esperada y reconciliar pagos. |
| Hipoteca y abonos extraordinarios | `mortgage_detail(debt_id, property_value, down_payment, rate_type, rate_reset_rule)`; `debt_scenario(id, debt_id, name, extra_amount, extra_frequency, start_date, strategy[REDUCE_TERM, REDUCE_PAYMENT])`; `scenario_result(...)` | Simular ahorro de intereses y reducción de plazo/cuota por abonos. |
| Transferencias internas | `transaction.transfer_group_id`, `transaction.kind[INCOME, EXPENSE, TRANSFER, SAVING, DEBT_PAYMENT]` | Evitar inflar simultáneamente ingresos, gastos, ahorro y balances. |
| Recurrencia | `recurring_rule(id, household_id, category_id, amount, frequency, expected_day, start_date, end_date, variability_tolerance)` | Proyectar fijos, detectar pagos faltantes y estimar caja. |
| Calidad/importación | `transaction.external_id`, `import_batch_id`, `fingerprint`, `reconciled_at`, `merchant`, `currency`, `notes`; constraints de unicidad condicionada | Prevenir duplicados, rastrear origen y facilitar conciliación. |
| Saldos históricos | `account_balance_snapshot(account_id, captured_at, balance)` | Conciliar a una fecha y medir patrimonio/caja real a través del tiempo. |

El diseño debe situar presupuesto, metas, fuentes y deudas a nivel de **hogar**, con propietario opcional por persona. También debe separar flujo (`income/expense`) de movimiento patrimonial (`transfer/saving/debt principal`).

## Resumen ejecutivo (10 líneas)

1. Hay 264 movimientos entre 2026-08-04 y 2026-10-19; septiembre es el único mes calendario completo.
2. El gasto promedio observado de 3 meses es $56.899.367, pero está severamente distorsionado por octubre y no representa el costo normal del hogar.
3. La mejor referencia provisional es $22.192.600/mes en agosto–septiembre; septiembre completo fue $24.711.200.
4. Excluyendo `OTROS GASTOS`, la sensibilidad de 3 meses es $25.674.033/mes; debe validarse, no asumirse como presupuesto.
5. Los gastos fijos registrados promedian $5.885.333/mes y suman $17.656.000, pero faltan o están mezclados servicios, arriendo y cuotas.
6. El balance contable acumulado es $169.927.700, pero no prueba ahorro: 61,79% de ingresos carece de fuente y los saldos reales suman $0.
7. El ahorro explícito registrado es $1.000.000; la capacidad de ahorro actual **no puede estimarse con fiabilidad** hasta conciliar y depurar transferencias.
8. `OTROS GASTOS` concentra $93.676.000 (54,88% del gasto) y los créditos $12.485.000; ambos requieren desglose prioritario.
9. Hay 3 posibles duplicados exactos con impacto bruto de $43.320.000 y dos meses incompletos, por lo que las conclusiones son provisionales.
10. La app cubre movimientos, cuentas, clasificación y conciliación básica, pero necesita modelos de presupuesto, fuentes, impuestos, metas y deudas/amortización.


# Presupuesto fase 1B: topes de gasto y proyección mensual

## Objetivo

Incorporar topes de gasto por hogar y categoría, conservar su historial de vigencias y ofrecer un reporte mensual de consumo y proyección. La comparación multimes, la conversión monetaria y el prorrateo en reportes existentes quedan fuera de esta fase.

## Persistencia

`Transaction.household` identifica el hogar contable con `PROTECT` y un índice junto con `fecha_efectiva`. Se deriva del propietario de la cuenta cuando pertenece a un solo hogar; con varios hogares debe venir explícito. Los legs de transferencia heredan `Transfer.household`. La migración histórica exige exactamente un hogar, asigna los 264 movimientos existentes y vuelve el campo obligatorio.

`Budget` guarda `household`, una categoría de tipo `EGRESO`, `amount` positivo, `currency` (por defecto `COP`), `valid_from`, `valid_to`, `note`, `created_by` y `created_at`. Las vigencias inclusivas de una misma pareja hogar/categoría no pueden solaparse. PostgreSQL lo garantiza mediante `ExclusionConstraint` sobre `daterange(valid_from, valid_to, '[]')`, igualdad de hogar/categoría y `BtreeGistExtension`; `clean()` y el serializer producen errores legibles.

Cambiar un tope no crea una fila por mes. Se cierra la vigencia anterior con `valid_to` y se abre una nueva; el historial queda intacto.

## API y resolución de hogar

El CRUD vive bajo `/api/transactions/budgets/`; `/api/transactions/budgets/consumo/` entrega el reporte.

Toda escritura exige `household` explícito y valida la membresía del usuario. Las lecturas aceptan `?household=<id>`; sin parámetro infieren el único hogar del usuario y, si hay varios, responden 400 con su lista. La asimetría es deliberada: una lectura ambigua no deja rastro, una escritura ambigua sí.

`PATCH` corrige el objeto y representa un error de captura. Un `POST` con `valid_from` futuro cierra atómicamente y bajo bloqueo la vigencia anterior el día previo antes de crear la nueva.

## Consumo, topes y proyección

El reporte acepta `desde`, `hasta` y hogar opcional. Por defecto consulta el mes actual completo y rechaza fechas invertidas o que crucen meses. Incluye todas las categorías `EGRESO`, aun sin tope, excluye transferencias, filtra por hogar y usa `fecha_efectiva`.

Una transacción sin cobertura se imputa entera si su fecha efectiva cae en el periodo. Una transacción con `cubre_desde`/`cubre_hasta` se incluye por intersección y se prorratea según días inclusivos de cobertura que caen en el periodo, con redondeo a centavos. Esta imputación deliberadamente difiere de la lista de movimientos y `summary()`, donde el pago permanece entero en su fecha efectiva.

Se selecciona el Budget vigente en `hasta`, o en hoy cuando el periodo incluye días futuros. No se prorratea el tope: hacerlo produciría una cifra que el usuario nunca escribió y no puede verificar de cabeza. Se informa si más de una vigencia intersectó el periodo.

La proyección solo se calcula cuando hoy pertenece al rango: `consumido / días desde desde hasta hoy, inclusivos × días desde desde hasta fin de mes`. En un mes cerrado o rango parcial ya pasado equivale a `consumido`.

`meses_historico` cuenta meses calendario completos anteriores al actual que contienen movimientos del hogar.

## Interfaz

`/presupuesto` muestra por categoría el tope, consumo, restante, porcentaje, proyección y una barra con semáforo: verde bajo 70 %, ámbar entre 70 % y 90 %, rojo sobre 90 % o si la proyección supera el tope. Presenta la nota literal del histórico, avisos de cambio de tope y prorrateo, y un modal para crear o corregir topes. No hay selector de hogar ni siembra automática.

## Verificación

La suite corre sobre PostgreSQL en la base separada `test_finanzapp_prod`. Cubre exclusión, historial de vigencias, selección de tope, semántica temporal, aislamiento de hogares, transferencias, prorrateo inclusivo y ambigüedad de hogar. También se ejecutan la suite completa, lint y build del frontend.

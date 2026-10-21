# Presupuesto fase 0: diseño estructural

## Objetivo

Preparar FinanzApp para presupuestos y proyecciones incorporando moneda por cuenta, transferencias explícitas y una fecha efectiva indexada, sin cambiar la clasificación actual ni implementar conversión monetaria.

## Modelo

- `Account.currency`: código de tres caracteres, default `COP`.
- `Transfer`: hogar explícito, cuentas origen/destino protegidas, monto positivo, fecha, descripción, autor y fecha de creación.
- `Transaction.transfer`: enlace opcional con borrado en cascada desde la transferencia.
- `Transaction.fecha_efectiva`: fecha contable obligatoria tras poblar el histórico.
- Índices por `(user, fecha_efectiva)` y `(subcategory, fecha_efectiva)`.

`Transfer.save()` ejecuta `full_clean()`. Sus invariantes son: cuentas diferentes, monto positivo y propietarios de ambas cuentas miembros del hogar indicado.

## API y atomicidad

`POST /api/transactions/transfers/` recibe el hogar explícito, cuentas, monto, fecha y descripción. Exige que el usuario autenticado y ambos propietarios pertenezcan al hogar. En una transacción atómica crea el `Transfer` con `created_by=request.user` y dos legs:

- egreso: usuario y cuenta de origen, monto negativo;
- ingreso: usuario y cuenta de destino, monto positivo.

Ambos llevan `subcategory=NULL`, `transfer` enlazado, `fecha_efectiva=fecha` y `created_at` a medianoche en la zona configurada.

`DELETE /api/transactions/transfers/<id>/` elimina la transferencia y sus dos legs. No se ofrecen `PATCH` ni `PUT`; corregir exige borrar y recrear.

Los endpoints de transacciones rechazan con conflicto la edición o eliminación individual de un leg y remiten al endpoint de transferencias. La reasignación o desclasificación por borrado de categorías excluye legs.

La validación actual de coherencia entre signo y rama solo se ejecuta cuando existe una subcategoría. Como los legs siempre llevan `subcategory=NULL`, retorna antes y no requiere una excepción adicional por `transfer`; una prueba de regresión fija esta semántica para evitar que una futura refactorización la rompa.

## Semántica de reportes

Los agregados de ingresos y egresos excluyen legs. Las consultas de pendientes de clasificación requieren simultáneamente `subcategory IS NULL` y `transfer IS NULL`.

Los saldos calculados por cuenta conservan legs porque una transferencia sí cambia el saldo de cada cuenta. La conciliación global se revisará por separado: excluir o incluir el par no cambia su suma neta, pero los indicadores separados de ingreso y egreso sí deben excluirlo.

## Compatibilidad temporal

El serializer acepta payloads históricos sin `fecha_efectiva`; deriva la fecha desde `created_at` y, si tampoco se proporciona, usa la fecha local actual. `created_at` conserva su función de marca de registro y el ordenamiento existente no cambia.

La evolución se reparte en tres migraciones: esquema nullable, población desde `created_at.date()` y finalmente `NOT NULL` con índices. Antes de generar la tercera migración, el serializer ya deriva `fecha_efectiva` para los payloads históricos.

## Interfaz

La pantalla de cuentas permite crear y editar el código de moneda. No hay conversiones, tasas ni cambios en reportes multimoneda.

## Pruebas

Se cubren creación y signos de legs, borrado en cascada, bloqueo de mutaciones individuales, autorización e invariantes, exclusión de agregados y pendientes, compatibilidad del payload anterior, protección al borrar cuentas y migración histórica de fecha efectiva.

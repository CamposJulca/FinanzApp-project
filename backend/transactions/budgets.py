import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from core.models import Budget, Transaction, TransactionCategory, TransactionType

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def prorated_amount(transaction, desde, hasta):
    """Imputa cobertura por días inclusivos solo al consumo presupuestal.

    Movimientos y ``summary()`` conservan el pago entero en fecha efectiva;
    ambas cifras son correctas en su contexto y esta divergencia es deliberada.
    """
    if not transaction.cubre_desde or not transaction.cubre_hasta:
        return money(abs(transaction.amount))
    start = max(transaction.cubre_desde, desde)
    end = min(transaction.cubre_hasta, hasta)
    if start > end:
        return Decimal("0.00")
    total_days = (transaction.cubre_hasta - transaction.cubre_desde).days + 1
    used_days = (end - start).days + 1
    return money(abs(transaction.amount) * used_days / total_days)


def monthly_consumption(household, desde, hasta):
    """Calcula un mes; selecciona un tope escrito por el usuario, sin prorratearlo."""
    today = timezone.localdate()
    selection_date = today if hasta > today else hasta
    movements = Transaction.objects.filter(
        household=household, transfer__isnull=True,
        subcategory__category__type__tipo=TransactionType.TIPO_EGRESO,
    ).filter(
        Q(cubre_desde__isnull=True, fecha_efectiva__range=(desde, hasta))
        | Q(cubre_desde__lte=hasta, cubre_hasta__gte=desde)
    ).select_related("subcategory__category")
    totals, prorated = {}, set()
    for movement in movements:
        category_id = movement.subcategory.category_id
        value = prorated_amount(movement, desde, hasta)
        totals[category_id] = totals.get(category_id, Decimal("0.00")) + value
        if movement.cubre_desde is not None and value:
            prorated.add(category_id)

    rows = []
    categories = TransactionCategory.objects.filter(
        type__tipo=TransactionType.TIPO_EGRESO
    ).select_related("type").order_by("type__subtipo", "name")
    for category in categories:
        consumed = money(totals.get(category.id, 0))
        active = Budget.objects.filter(
            household=household, category=category, valid_from__lte=selection_date,
        ).filter(Q(valid_to__isnull=True) | Q(valid_to__gte=selection_date))
        budget = active.order_by("-valid_from").first()
        changes = Budget.objects.filter(
            household=household, category=category, valid_from__lte=hasta,
        ).filter(Q(valid_to__isnull=True) | Q(valid_to__gte=desde)).count()
        limit = budget.amount if budget else None
        remaining = money(limit - consumed) if limit is not None else None
        percentage = money(consumed * 100 / limit) if limit else None
        if desde <= today <= hasta:
            elapsed = (today - desde).days + 1
            month_end = date(desde.year, desde.month, calendar.monthrange(desde.year, desde.month)[1])
            projection = money(consumed / elapsed * ((month_end - desde).days + 1))
        else:
            projection = consumed
        rows.append({
            "categoria_id": category.id, "categoria_nombre": category.name,
            "subtipo": category.type.subtipo, "tope": limit,
            "budget_id": budget.id if budget else None,
            "budget_valid_from": budget.valid_from if budget else None,
            "tope_cambio_en_periodo": changes > 1, "consumido": consumed,
            "restante": remaining, "porcentaje": percentage,
            "proyeccion_cierre": projection,
            "monto_prorrateado": category.id in prorated,
        })
    current_month = today.replace(day=1)
    historical_dates = Transaction.objects.filter(
        household=household, transfer__isnull=True, fecha_efectiva__lt=current_month,
    ).values_list("fecha_efectiva", flat=True)
    return {
        "household_id": household.id, "desde": desde, "hasta": hasta,
        "meses_historico": len({(d.year, d.month) for d in historical_dates}),
        "categorias": rows,
    }

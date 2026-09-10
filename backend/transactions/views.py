from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, is_naive, make_aware

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Account,
    Transaction,
    TransactionType,
    TransactionCategory,
    TransactionSubCategory,
)
from .serializers import (
    AccountSerializer,
    TransactionSerializer,
    TransactionTypeSerializer,
    TransactionCategorySerializer,
    TransactionSubCategorySerializer,
)


# Cuentas con las que se inicializa un usuario que aún no tiene ninguna.
# A partir de ahí el usuario manda: puede crear, renombrar y borrar.
DEFAULT_ACCOUNT_NAMES = [
    "Efectivo Karla",
    "Efectivo Daniel",
    "Davivienda Daniel",
    "Davivienda Karla",
    "Nequi Karla",
    "Nequi Daniel",
    "NU bank",
    "Caja social Daniel",
]

CAMPOSMARIN_USERNAME = "camposmarin"
VALID_REGISTERED_BY = {"diana", "daniel", "karla"}


def _bootstrap_accounts_if_empty(user):
    """
    Siembra las cuentas por defecto SÓLO si el usuario no tiene ninguna.

    Antes esto se ejecutaba en cada lectura y recreaba la lista fija, lo que
    hacía imposible borrar una cuenta: reaparecía en la siguiente petición.
    """
    if user.accounts.exists():
        return

    Account.objects.bulk_create(
        [
            Account(user=user, name=name, saldo_real=Decimal("0"))
            for name in DEFAULT_ACCOUNT_NAMES
        ]
    )


def _parse_transaction_datetime(value):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            return None
        parsed = datetime.combine(parsed_date, datetime.min.time())

    if is_naive(parsed):
        return make_aware(parsed, get_current_timezone())

    return parsed


# =========================================================
# RESUMEN + CONCILIACIÓN CONTABLE
# =========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    user = request.user

    # -------------------------------
    # 1. SALDO CONTABLE (AUTOMÁTICO)
    # -------------------------------
    ingresos = (
        Transaction.objects
        .filter(user=user, amount__gt=0)
        .aggregate(total=Sum("amount"))["total"] or Decimal("0")
    )

    egresos = (
        Transaction.objects
        .filter(user=user, amount__lt=0)
        .aggregate(total=Sum("amount"))["total"] or Decimal("0")
    )

    saldo_contable = ingresos + egresos
    total_movimientos = Transaction.objects.filter(user=user).count()

    # --------------------------------
    # 2. SALDO POR CUENTAS (MANUAL)
    # --------------------------------
    # Suma TODAS las cuentas del usuario, incluidas las que cree a mano.
    _bootstrap_accounts_if_empty(user)
    saldo_cuentas = (
        Account.objects
        .filter(user=user)
        .aggregate(total=Sum("saldo_real"))["total"] or Decimal("0")
    )

    # --------------------------------
    # 3. CONCILIACIÓN
    # --------------------------------
    diferencia = saldo_cuentas - saldo_contable
    estado = "OK" if diferencia == 0 else "INCONSISTENTE"

    return Response({
        "ingresos": float(ingresos),
        "egresos": abs(float(egresos)),

        "saldo_contable": float(saldo_contable),
        "saldo_cuentas": float(saldo_cuentas),

        "diferencia": float(diferencia),
        "estado": estado,

        "total_movimientos": total_movimientos,
        "total_cuentas": Account.objects.filter(user=user).count(),
    })


# =========================================================
# INFO USUARIO
# =========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
    })


# =========================================================
# TRANSACCIONES — CRUD
# =========================================================
class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related(
                "account",
                "subcategory",
                "subcategory__category",
                "subcategory__category__type",
            )
            .order_by("-created_at")
        )

        account_id = self.request.query_params.get("account")
        if account_id:
            qs = qs.filter(account_id=account_id)

        return qs

    def list(self, request, *args, **kwargs):
        # Se mantiene el envoltorio {"transactions": [...]} que consume el front.
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"transactions": serializer.data})

    def create(self, request, *args, **kwargs):
        data = _normalize_transaction_payload(request.data, request.user)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar por usuario aquí es lo que impide editar o borrar
        # movimientos ajenos: un id de otro usuario devuelve 404.
        return Transaction.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        data = _normalize_transaction_payload(
            request.data, request.user, partial=kwargs.get("partial", False)
        )
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def _normalize_transaction_payload(data, user, partial=False):
    """
    Acepta el formato histórico del frontend (`account_id`, fecha suelta)
    y lo traduce al que espera el serializer.
    """
    payload = dict(data)

    if "account_id" in payload and "account" not in payload:
        payload["account"] = payload.pop("account_id")

    if not partial and not payload.get("account"):
        _bootstrap_accounts_if_empty(user)
        first = user.accounts.order_by("created_at").first()
        if first:
            payload["account"] = first.id

    if "created_at" in payload:
        parsed = _parse_transaction_datetime(payload.get("created_at"))
        if parsed is not None:
            payload["created_at"] = parsed

    return payload


# =========================================================
# CUENTAS — CRUD
# =========================================================
class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user).order_by("created_at")

    def list(self, request, *args, **kwargs):
        _bootstrap_accounts_if_empty(request.user)
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"accounts": serializer.data})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        movimientos = account.transactions.count()

        # Account.transactions tiene on_delete=CASCADE: borrar la cuenta se
        # llevaría por delante sus movimientos sin avisar. Se exige confirmar.
        if movimientos and request.query_params.get("force") != "true":
            return Response(
                {
                    "error": (
                        f"La cuenta tiene {movimientos} movimiento(s). "
                        "Repite la petición con ?force=true para borrarla junto "
                        "con ellos."
                    ),
                    "transactions_count": movimientos,
                },
                status=status.HTTP_409_CONFLICT,
            )

        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountSaldoRealUpdateView(generics.UpdateAPIView):
    """
    Endpoint histórico: el usuario declara cuánto dinero REAL hay en la cuenta.
    Se mantiene por compatibilidad; `AccountDetailView` hace lo mismo y más.
    """
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "account_id"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        account = self.get_object()
        serializer = self.get_serializer(
            account, data={"saldo_real": request.data.get("saldo_real")}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "account_id": account.id,
            "name": account.name,
            "saldo_real": float(account.saldo_real),
        })


# =========================================================
# ÁRBOL DE CLASIFICACIÓN — CRUD
# =========================================================
# ---------------------------------------------------------
# Impacto de borrar o mover una rama con movimientos colgando
# ---------------------------------------------------------
# Regla de la casa: ningún movimiento pierde su clasificación en silencio.
# Si la rama tiene movimientos, la API responde 409 con el detalle del impacto
# y exige que el cliente declare qué hacer. Las dos únicas estrategias posibles
# son las que no inventan datos: dejarlos sin clasificar, o moverlos a otra
# subcategoría compatible.
#
# El árbol es compartido entre usuarios, así que el conteo que decide el bloqueo
# es global (PROTECT también lo es). El detalle sólo muestra los movimientos de
# quien pregunta; del resto se informa el número, no el contenido.

STRATEGY_BLOCK = "block"
STRATEGY_UNCLASSIFY = "unclassify"
STRATEGY_REASSIGN = "reassign"
VALID_STRATEGIES = (STRATEGY_BLOCK, STRATEGY_UNCLASSIFY, STRATEGY_REASSIGN)

IMPACT_SAMPLE_SIZE = 5


def _category_path(category):
    return f"{category.type.tipo} / {category.type.subtipo} → {category.name}"


def _subcategory_path(sub):
    return f"{_category_path(sub.category)} → {sub.name}"


def _leaves_of(node):
    """Hojas que desaparecen al borrar `node` (una categoría arrastra las suyas)."""
    if isinstance(node, TransactionCategory):
        return list(node.subcategories.select_related("category__type"))
    return [node]


def _node_tipo(node):
    return (
        node.type.tipo
        if isinstance(node, TransactionCategory)
        else node.category.type.tipo
    )


def _reassign_targets(node):
    """Subcategorías a las que se puede mover sin romper la coherencia de signo.

    Sólo la misma rama (INGRESO/EGRESO) y nunca una hoja que también va a
    desaparecer en esta misma operación.
    """
    excluidas = [leaf.id for leaf in _leaves_of(node)]
    return (
        TransactionSubCategory.objects
        .select_related("category__type")
        .filter(category__type__tipo=_node_tipo(node))
        .exclude(id__in=excluidas)
        .order_by("category__name", "name")
    )


def _impact(node, user):
    """Radiografía de lo que se lleva por delante una operación destructiva."""
    leaves = _leaves_of(node)
    leaf_ids = [leaf.id for leaf in leaves]

    todas = Transaction.objects.filter(subcategory_id__in=leaf_ids)
    propias = todas.filter(user=user)
    total = todas.count()

    es_categoria = isinstance(node, TransactionCategory)

    return {
        "level": "category" if es_categoria else "subcategory",
        "id": node.id,
        "name": node.name,
        "path": _category_path(node) if es_categoria else _subcategory_path(node),
        "tipo": _node_tipo(node),
        "subcategories": [
            {
                "id": leaf.id,
                "name": leaf.name,
                "path": _subcategory_path(leaf),
                "transactions_count": todas.filter(subcategory_id=leaf.id).count(),
            }
            for leaf in leaves
        ],
        "subcategories_count": len(leaves),
        "transactions_count": total,
        "transactions_count_mine": propias.count(),
        "transactions_count_others": total - propias.count(),
        "transactions_total": float(
            todas.aggregate(t=Sum("amount"))["t"] or Decimal("0")
        ),
        "sample": [
            {
                "id": t.id,
                "created_at": t.created_at,
                "description": t.description,
                "amount": float(t.amount),
                "subcategory_path": _subcategory_path(t.subcategory),
            }
            for t in (
                propias
                .select_related("subcategory__category__type")
                .order_by("-created_at")[:IMPACT_SAMPLE_SIZE]
            )
        ],
        "blocking": total > 0,
        "reassign_targets": [
            {"id": s.id, "path": _subcategory_path(s)} for s in _reassign_targets(node)
        ],
    }


def _resolve_transactions(node, request):
    """Aplica la estrategia pedida a los movimientos de la rama.

    Devuelve (respuesta_de_error, resumen). Si `respuesta_de_error` no es None,
    la vista debe devolverla tal cual y no borrar nada.
    """
    impacto = _impact(node, request.user)

    if not impacto["blocking"]:
        return None, {"strategy": None, "transactions_affected": 0}

    strategy = request.query_params.get("on_transactions", STRATEGY_BLOCK)

    if strategy not in VALID_STRATEGIES:
        return (
            Response(
                {
                    "error": (
                        f"Estrategia «{strategy}» desconocida. Usa "
                        f"{', '.join(VALID_STRATEGIES)}."
                    ),
                    "impact": impacto,
                },
                status=status.HTTP_400_BAD_REQUEST,
            ),
            None,
        )

    if strategy == STRATEGY_BLOCK:
        return (
            Response(
                {
                    "error": (
                        f"«{impacto['path']}» tiene {impacto['transactions_count']} "
                        "movimiento(s) clasificados. Decide qué hacer con ellos "
                        "antes de eliminar."
                    ),
                    "transactions_count": impacto["transactions_count"],
                    "impact": impacto,
                },
                status=status.HTTP_409_CONFLICT,
            ),
            None,
        )

    afectados = Transaction.objects.filter(
        subcategory_id__in=[leaf.id for leaf in _leaves_of(node)]
    )

    if strategy == STRATEGY_UNCLASSIFY:
        n = afectados.update(subcategory=None)
        return None, {"strategy": STRATEGY_UNCLASSIFY, "transactions_affected": n}

    destino_id = request.query_params.get("to")
    if not destino_id:
        return (
            Response(
                {
                    "error": "Falta «to»: la subcategoría destino de la reasignación.",
                    "impact": impacto,
                },
                status=status.HTTP_400_BAD_REQUEST,
            ),
            None,
        )

    destino = _reassign_targets(node).filter(id=destino_id).first()
    if destino is None:
        return (
            Response(
                {
                    "error": (
                        "La subcategoría destino no existe, desaparece en esta misma "
                        f"operación, o no pertenece a {impacto['tipo']}. Reasignar "
                        "fuera de la rama dejaría movimientos con el signo cambiado."
                    ),
                    "impact": impacto,
                },
                status=status.HTTP_400_BAD_REQUEST,
            ),
            None,
        )

    n = afectados.update(subcategory=destino)
    return None, {
        "strategy": STRATEGY_REASSIGN,
        "transactions_affected": n,
        "reassigned_to": {"id": destino.id, "path": _subcategory_path(destino)},
    }


def _guard_branch_move(node, request, campo, relacion):
    """Avisa antes de mudar de rama una categoría o subcategoría con movimientos.

    Renombrar es siempre libre: el movimiento guarda el id, no el texto. Mudar
    de padre sí reescribe la historia (los movimientos pasan a contarse en otra
    rama), y saltar de INGRESO a EGRESO además los dejaría con el signo contrario
    al de su clasificación — justo lo que rechaza TransactionSerializer. Ese
    salto no se permite ni con confirmación.
    """
    if campo not in request.data:
        return None

    nuevo_id = request.data.get(campo)
    if nuevo_id in ("", None):
        return None
    try:
        nuevo_id = int(nuevo_id)
    except (TypeError, ValueError):
        return None  # formato inválido: que lo reporte el serializer

    if nuevo_id == relacion(node):
        return None

    impacto = _impact(node, request.user)
    if not impacto["blocking"]:
        return None

    if campo == "type":
        destino = TransactionType.objects.filter(id=nuevo_id).first()
        tipo_destino = destino.tipo if destino else None
    else:
        destino = (
            TransactionCategory.objects
            .select_related("type")
            .filter(id=nuevo_id)
            .first()
        )
        tipo_destino = destino.type.tipo if destino else None

    if tipo_destino is None:
        return None  # FK inexistente: que lo reporte el serializer

    if tipo_destino != impacto["tipo"]:
        return Response(
            {
                "error": (
                    f"«{impacto['path']}» tiene {impacto['transactions_count']} "
                    f"movimiento(s) de {impacto['tipo']}. Moverla a {tipo_destino} "
                    "los dejaría con el signo contrario al de su clasificación. "
                    "Reasigna esos movimientos primero."
                ),
                "impact": impacto,
            },
            status=status.HTTP_409_CONFLICT,
        )

    if request.query_params.get("confirm") != "true":
        return Response(
            {
                "error": (
                    f"«{impacto['path']}» tiene {impacto['transactions_count']} "
                    "movimiento(s) que pasarían a contarse en otra rama. "
                    "Confirma el cambio para aplicarlo."
                ),
                "requires_confirmation": True,
                "impact": impacto,
            },
            status=status.HTTP_409_CONFLICT,
        )

    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def category_impact(request, pk):
    categoria = get_object_or_404(TransactionCategory, pk=pk)
    return Response(_impact(categoria, request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subcategory_impact(request, pk):
    sub = get_object_or_404(TransactionSubCategory, pk=pk)
    return Response(_impact(sub, request.user))


class TransactionTypeListCreateView(generics.ListAPIView):
    """Las 4 parejas (tipo, subtipo) son fijas: sólo se listan, no se crean."""
    queryset = TransactionType.objects.order_by("tipo", "subtipo")
    serializer_class = TransactionTypeSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({"types": self.get_serializer(self.get_queryset(), many=True).data})


class TransactionTypeDetailView(generics.RetrieveAPIView):
    """Pareja fija: sólo lectura (no se edita ni se elimina)."""
    queryset = TransactionType.objects.all()
    serializer_class = TransactionTypeSerializer
    permission_classes = [IsAuthenticated]


class TransactionCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TransactionCategory.objects.select_related("type").order_by("type__tipo", "type__subtipo", "name")
        type_id = self.request.query_params.get("type")
        if type_id:
            qs = qs.filter(type_id=type_id)
        return qs

    def list(self, request, *args, **kwargs):
        return Response({"categories": self.get_serializer(self.get_queryset(), many=True).data})


class TransactionCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransactionCategory.objects.all()
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        error = _guard_branch_move(
            self.get_object(), request, campo="type", relacion=lambda c: c.type_id
        )
        if error is not None:
            return error
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()

        # La categoría arrastra sus subcategorías (CASCADE) y ésas están
        # protegidas por los movimientos (PROTECT): sin resolverlos primero,
        # el borrado revienta con un 500 en vez de explicar el problema.
        with transaction.atomic():
            error, resumen = _resolve_transactions(categoria, request)
            if error is not None:
                return error

            borrada = {"id": categoria.id, "path": _category_path(categoria)}
            categoria.delete()

        return Response({"deleted": borrada, **resumen})


class TransactionSubCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSubCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            TransactionSubCategory.objects
            .select_related("category", "category__type")
            .order_by("category__name", "name")
        )
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def list(self, request, *args, **kwargs):
        return Response(
            {"subcategories": self.get_serializer(self.get_queryset(), many=True).data}
        )


class TransactionSubCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransactionSubCategory.objects.all()
    serializer_class = TransactionSubCategorySerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        error = _guard_branch_move(
            self.get_object(), request, campo="category", relacion=lambda s: s.category_id
        )
        if error is not None:
            return error
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        sub = self.get_object()

        # on_delete=PROTECT: sin resolver los movimientos primero, el borrado
        # revienta con un 500.
        with transaction.atomic():
            error, resumen = _resolve_transactions(sub, request)
            if error is not None:
                return error

            borrada = {"id": sub.id, "path": _subcategory_path(sub)}
            sub.delete()

        return Response({"deleted": borrada, **resumen})

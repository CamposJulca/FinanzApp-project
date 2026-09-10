import { useCallback, useEffect, useState } from "react";
import {
  fetchTypes,
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  fetchCategoryImpact,
  fetchSubCategories,
  createSubCategory,
  updateSubCategory,
  deleteSubCategory,
  fetchSubCategoryImpact,
} from "../services/transactionsApi";

/**
 * Árbol de clasificación en cuatro niveles:
 *
 *   (Tipo, Subtipo)  →  Categoría  →  Subcategoría
 *
 * Tipo y Subtipo son valores fijos del dominio: sus combinaciones dan las
 * 4 parejas (INGRESO/EGRESO × FIJO/VARIABLE), que NO se crean ni se borran.
 * El usuario sólo agrega categorías bajo una pareja y subcategorías bajo una
 * categoría. Los movimientos se asignan a la subcategoría (último nivel).
 */
export function ClasificacionPage() {
  const [types, setTypes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [pending, setPending] = useState(null);
  const [loading, setLoading] = useState(true);

  // `load` reporta su propio fallo en vez de propagarlo. Así el try/catch de
  // quien escribe (`run`, `confirmDelete`) cubre sólo la escritura, y un fallo
  // al recargar el árbol no se confunde con un fallo al guardar.
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, c, s] = await Promise.all([
        fetchTypes(),
        fetchCategories(),
        fetchSubCategories(),
      ]);
      setTypes(t.types || []);
      setCategories(c.categories || []);
      setSubcategories(s.subcategories || []);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (action, successMessage) => {
    setStatus({ type: "saving", message: "Guardando..." });
    try {
      await action();
      setStatus({ type: "success", message: successMessage });
      await load();
      return true;
    } catch (error) {
      setStatus({ type: "error", message: error.message });
      return false;
    }
  };

  /**
   * Borrar nunca es un clic directo cuando hay movimientos colgando: primero se
   * consulta el impacto al backend y se pide una decisión explícita sobre qué
   * pasa con ellos. Si la rama está vacía basta una confirmación simple.
   */
  const requestDelete = async (level, item) => {
    setStatus({ type: "saving", message: "Revisando impacto..." });
    try {
      const impact =
        level === "category"
          ? await fetchCategoryImpact(item.id)
          : await fetchSubCategoryImpact(item.id);
      setStatus({ type: "idle", message: "" });

      if (impact.blocking) {
        setPending({ level, item, impact });
        return;
      }

      const arrastra =
        level === "category" && impact.subcategories_count > 0
          ? ` y sus ${impact.subcategories_count} subcategoría(s)`
          : "";
      if (
        window.confirm(
          `¿Eliminar «${impact.path}»${arrastra}? No tiene movimientos clasificados.`
        )
      ) {
        await confirmDelete(level, item, {});
      }
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const confirmDelete = async (level, item, options) => {
    setStatus({ type: "saving", message: "Eliminando..." });
    try {
      const result =
        level === "category"
          ? await deleteCategory(item.id, options)
          : await deleteSubCategory(item.id, options);

      setPending(null);
      if (level === "category" && selectedCategory === item.id) {
        setSelectedCategory(null);
      }
      setStatus({ type: "success", message: describeDeletion(result) });
      await load();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const visibleCategories = selectedType
    ? categories.filter((c) => c.type === selectedType)
    : categories;

  const visibleSubcategories = selectedCategory
    ? subcategories.filter((s) => s.category === selectedCategory)
    : selectedType
      ? subcategories.filter((s) =>
          visibleCategories.some((c) => c.id === s.category)
        )
      : subcategories;

  const selectedPair = types.find((t) => t.id === selectedType) || null;

  return (
    <section className="data-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Estructura</p>
          <h2>Clasificación</h2>
          <p className="muted">
            (Tipo · Subtipo) → Categoría → Subcategoría. Tipo y subtipo son
            fijos; tú agregas las categorías y subcategorías. Los movimientos se
            asignan al último nivel.
          </p>
        </div>
        {status.message && (
          <span className={`form-status ${status.type}`}>{status.message}</span>
        )}
      </div>

      <div className="tree-grid">
        <TreeColumn
          title="Tipo · Subtipo"
          hint="fijos"
          items={types}
          loading={loading}
          readOnly
          selectedId={selectedType}
          getLabel={(item) => item.tipo}
          subtitle={(item) => item.subtipo}
          countLabel={(item) => `${item.categories_count} cat.`}
          onSelect={(id) => {
            setSelectedType((prev) => (prev === id ? null : id));
            setSelectedCategory(null);
          }}
        />

        <TreeColumn
          title="Categorías"
          hint={selectedPair ? selectedPair.label : "elige una pareja"}
          items={visibleCategories}
          loading={loading}
          selectedId={selectedCategory}
          countLabel={(item) => `${item.subcategories_count} sub.`}
          subtitle={(item) => item.type_name}
          disabled={!selectedType}
          disabledHint="Selecciona una pareja (tipo·subtipo) para crear categorías"
          onSelect={(id) =>
            setSelectedCategory((prev) => (prev === id ? null : id))
          }
          onCreate={(name) =>
            run(
              () => createCategory({ name, type: selectedType }),
              "Categoría creada."
            )
          }
          onUpdate={(id, name) =>
            run(() => updateCategory(id, { name }), "Categoría actualizada.")
          }
          onDelete={(item) => requestDelete("category", item)}
        />

        <TreeColumn
          title="Subcategorías"
          hint={selectedCategory ? "filtradas" : "nivel 3"}
          items={visibleSubcategories}
          loading={loading}
          subtitle={(item) => `${item.type_name} → ${item.category_name}`}
          disabled={!selectedCategory}
          disabledHint="Selecciona una categoría para crear subcategorías"
          onCreate={(name) =>
            run(
              () => createSubCategory({ name, category: selectedCategory }),
              "Subcategoría creada."
            )
          }
          onUpdate={(id, name) =>
            run(() => updateSubCategory(id, { name }), "Subcategoría actualizada.")
          }
          onDelete={(item) => requestDelete("subcategory", item)}
        />
      </div>

      {pending && (
        <ImpactDialog
          pending={pending}
          onCancel={() => setPending(null)}
          onConfirm={(options) =>
            confirmDelete(pending.level, pending.item, options)
          }
        />
      )}
    </section>
  );
}

function TreeColumn({
  title,
  hint,
  items,
  loading = false,
  selectedId = null,
  onSelect,
  subtitle,
  countLabel,
  getLabel = (item) => item.name,
  onCreate,
  onUpdate,
  onDelete,
  disabled = false,
  disabledHint = "",
  readOnly = false,
}) {
  const [nuevo, setNuevo] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState("");

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!nuevo.trim() || !onCreate) return;
    const ok = await onCreate(nuevo.trim());
    if (ok) setNuevo("");
  };

  const handleSave = async (id) => {
    if (!draft.trim() || !onUpdate) return;
    const ok = await onUpdate(id, draft.trim());
    if (ok) setEditingId(null);
  };

  return (
    <div className="tree-column">
      <div className="tree-column-head">
        <strong>{title}</strong>
        <span className="counter-pill">{hint}</span>
      </div>

      {!readOnly && (
        <form className="tree-add" onSubmit={handleCreate}>
          <input
            type="text"
            placeholder={disabled ? disabledHint : `Nueva ${title.toLowerCase()}...`}
            value={nuevo}
            disabled={disabled}
            onChange={(event) => setNuevo(event.target.value)}
          />
          <button type="submit" disabled={disabled}>
            +
          </button>
        </form>
      )}

      <ul className="tree-list">
        {items.map((item) => (
          <li
            key={item.id}
            className={selectedId === item.id ? "selected" : ""}
          >
            {editingId === item.id ? (
              <div className="tree-item-edit">
                <input
                  type="text"
                  value={draft}
                  autoFocus
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") handleSave(item.id);
                    if (event.key === "Escape") setEditingId(null);
                  }}
                />
                <button type="button" onClick={() => handleSave(item.id)}>
                  ✓
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => setEditingId(null)}
                >
                  ✕
                </button>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  className="tree-item-label"
                  onClick={() => onSelect?.(item.id)}
                  disabled={!onSelect}
                >
                  <span>{getLabel(item)}</span>
                  {subtitle && <em>{subtitle(item)}</em>}
                </button>
                <div className="tree-item-actions">
                  {countLabel && (
                    <span className="chip">{countLabel(item)}</span>
                  )}
                  {!readOnly && (
                    <>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(item.id);
                          setDraft(getLabel(item));
                        }}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => onDelete(item)}
                      >
                        Eliminar
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </li>
        ))}
        {items.length === 0 && (
          <li className="empty-state">
            {loading ? "Cargando..." : "Sin elementos."}
          </li>
        )}
      </ul>
    </div>
  );
}

const money = (value) =>
  `$${Number(value).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;

function describeDeletion(result) {
  if (!result) return "Eliminada.";

  const { deleted, strategy, transactions_affected: n, reassigned_to: to } = result;
  const base = `«${deleted?.path ?? ""}» eliminada`;

  if (!strategy || !n) return `${base}.`;
  if (strategy === "unclassify") {
    return `${base}. ${n} movimiento(s) quedaron sin clasificar.`;
  }
  return `${base}. ${n} movimiento(s) reasignados a «${to?.path}».`;
}

/**
 * Aviso previo a un borrado con movimientos colgando.
 *
 * No hay opción "eliminar sin más": el usuario tiene que elegir el destino de
 * esos movimientos, y las dos alternativas son las únicas que no inventan
 * datos. Reasignar sólo ofrece subcategorías de la misma rama (INGRESO o
 * EGRESO), porque mover un egreso a una rama de ingreso lo dejaría con el signo
 * contrario a su clasificación.
 */
function ImpactDialog({ pending, onCancel, onConfirm }) {
  const { impact, level } = pending;
  const [strategy, setStrategy] = useState("unclassify");
  const [target, setTarget] = useState("");
  const [working, setWorking] = useState(false);

  const targets = impact.reassign_targets || [];
  const listo = strategy === "unclassify" || (strategy === "reassign" && target);

  const submit = async () => {
    if (!listo) return;
    setWorking(true);
    try {
      await onConfirm(
        strategy === "reassign" ? { strategy, target } : { strategy }
      );
    } finally {
      setWorking(false);
    }
  };

  return (
    <div
      className="impact-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="impact-title"
    >
      <div className="impact-dialog">
        <div className="impact-head">
          <div>
            <p className="eyebrow">
              Eliminar {level === "category" ? "categoría" : "subcategoría"}
            </p>
            <h3 id="impact-title">{impact.path}</h3>
          </div>
          <span className="chip">{impact.tipo}</span>
        </div>

        <div className="impact-alert">
          <strong>
            {impact.transactions_count} movimiento(s) clasificados aquí, por{" "}
            {money(impact.transactions_total)}.
          </strong>
          <p>
            Si eliminas esta rama esos movimientos se quedan sin destino. Elige
            qué hacer con ellos antes de continuar.
          </p>
          {impact.transactions_count_others > 0 && (
            <p className="impact-warn">
              Atención: {impact.transactions_count_others} de esos movimientos
              son de otro usuario. El árbol de clasificación es compartido, así
              que tu decisión también les afecta.
            </p>
          )}
        </div>

        {level === "category" && (
          <div className="impact-block">
            <p className="impact-label">
              Subcategorías que desaparecen ({impact.subcategories_count})
            </p>
            <ul className="impact-list">
              {impact.subcategories.map((leaf) => (
                <li key={leaf.id}>
                  <span>{leaf.name}</span>
                  <span className="chip">
                    {leaf.transactions_count} mov.
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {impact.sample.length > 0 && (
          <div className="impact-block">
            <p className="impact-label">
              Tus movimientos afectados
              {impact.transactions_count_mine > impact.sample.length &&
                ` (${impact.sample.length} de ${impact.transactions_count_mine})`}
            </p>
            <ul className="impact-list">
              {impact.sample.map((mov) => (
                <li key={mov.id}>
                  <span>
                    {new Date(mov.created_at).toLocaleDateString()} ·{" "}
                    {mov.description || `movimiento #${mov.id}`}
                  </span>
                  <span
                    className={
                      Number(mov.amount) >= 0 ? "amount income" : "amount expense"
                    }
                  >
                    {money(mov.amount)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="impact-block">
          <p className="impact-label">Qué hacer con esos movimientos</p>

          <label className="impact-choice">
            <input
              type="radio"
              name="impact-strategy"
              value="unclassify"
              checked={strategy === "unclassify"}
              onChange={() => setStrategy("unclassify")}
            />
            <span>
              <strong>Dejarlos sin clasificar</strong>
              <em>
                Se conservan íntegros y aparecen como «Sin clasificar» en
                Movimientos. Los montos y el saldo no cambian.
              </em>
            </span>
          </label>

          <label
            className={`impact-choice ${targets.length === 0 ? "disabled" : ""}`}
          >
            <input
              type="radio"
              name="impact-strategy"
              value="reassign"
              disabled={targets.length === 0}
              checked={strategy === "reassign"}
              onChange={() => setStrategy("reassign")}
            />
            <span>
              <strong>Reasignarlos a otra subcategoría</strong>
              <em>
                {targets.length === 0
                  ? `No hay otra subcategoría de ${impact.tipo} disponible.`
                  : `Sólo se ofrecen las ${targets.length} subcategorías de ${impact.tipo}: reasignar a la otra rama dejaría los movimientos con el signo contrario.`}
              </em>
            </span>
          </label>

          {strategy === "reassign" && targets.length > 0 && (
            <select
              className="impact-target"
              value={target}
              onChange={(event) => setTarget(event.target.value)}
            >
              <option value="">Elige la subcategoría destino...</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.path}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="impact-actions">
          <button type="button" className="ghost-btn" onClick={onCancel}>
            Cancelar
          </button>
          <button
            type="button"
            className="danger"
            disabled={!listo || working}
            onClick={submit}
          >
            {working
              ? "Eliminando..."
              : strategy === "unclassify"
                ? `Eliminar y dejar ${impact.transactions_count} sin clasificar`
                : "Eliminar y reasignar"}
          </button>
        </div>
      </div>
    </div>
  );
}


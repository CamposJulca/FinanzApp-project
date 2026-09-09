import { useCallback, useEffect, useState } from "react";
import {
  fetchTypes,
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  fetchSubCategories,
  createSubCategory,
  updateSubCategory,
  deleteSubCategory,
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

  const load = useCallback(async () => {
    const [t, c, s] = await Promise.all([
      fetchTypes(),
      fetchCategories(),
      fetchSubCategories(),
    ]);
    setTypes(t.types || []);
    setCategories(c.categories || []);
    setSubcategories(s.subcategories || []);
  }, []);

  useEffect(() => {
    let active = true;
    load().catch((error) => {
      if (active) setStatus({ type: "error", message: error.message });
    });
    return () => {
      active = false;
    };
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
          onDelete={(item) =>
            run(() => deleteCategory(item.id), "Categoría eliminada.")
          }
          deleteWarning={(item) =>
            item.subcategories_count > 0
              ? `"${item.name}" tiene ${item.subcategories_count} subcategoría(s). ` +
                "Al borrarla se eliminan también. ¿Continuar?"
              : `¿Eliminar la categoría "${item.name}"?`
          }
        />

        <TreeColumn
          title="Subcategorías"
          hint={selectedCategory ? "filtradas" : "nivel 3"}
          items={visibleSubcategories}
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
          onDelete={(item) =>
            run(() => deleteSubCategory(item.id), "Subcategoría eliminada.")
          }
          deleteWarning={(item) => `¿Eliminar la subcategoría "${item.name}"?`}
        />
      </div>
    </section>
  );
}

function TreeColumn({
  title,
  hint,
  items,
  selectedId = null,
  onSelect,
  subtitle,
  countLabel,
  getLabel = (item) => item.name,
  onCreate,
  onUpdate,
  onDelete,
  deleteWarning,
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

  const handleDelete = async (item) => {
    if (window.confirm(deleteWarning(item))) await onDelete(item);
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
                        onClick={() => handleDelete(item)}
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
          <li className="empty-state">Sin elementos.</li>
        )}
      </ul>
    </div>
  );
}

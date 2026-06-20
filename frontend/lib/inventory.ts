/**
 * Metadatos de presentación del inventario operativo (espejo del módulo backend
 * `inventory`). La fuente de verdad de los datos sigue en el backend.
 */

export const ITEM_CATEGORIES = [
  { id: "vehiculo", label: "Vehículos", hint: "Cuatrimotos, balsas, lanchas…" },
  { id: "equipo", label: "Equipos", hint: "Arneses, cascos, cuerdas…" },
  { id: "salida_emergencia", label: "Salidas de emergencia", hint: "Rutas y puntos de evacuación" },
  { id: "guia", label: "Guías", hint: "Personal y certificaciones" },
  { id: "actividad", label: "Actividades", hint: "Rafting, parapente, canopy…" },
  { id: "riesgo", label: "Riesgos", hint: "Peligros identificados por actividad" },
  { id: "contacto_emergencia", label: "Contactos de emergencia", hint: "Bomberos, ambulancia, ARL…" },
  { id: "otro", label: "Otros", hint: "Cualquier otro elemento operativo" },
] as const;

export type CategoryId = (typeof ITEM_CATEGORIES)[number]["id"];

export type AttrValue = string | number | boolean | string[] | null;

export interface InventoryItem {
  id: string;
  category: CategoryId;
  name: string;
  attributes: Record<string, AttrValue>;
  evidence_count: number;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: string;
  caption: string | null;
  url: string | null;
  uploaded_at: string;
}

export const CATEGORY_LABEL: Record<string, string> = Object.fromEntries(
  ITEM_CATEGORIES.map((c) => [c.id, c.label]),
);

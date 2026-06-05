export interface CatalogValue {
  id: string;
  label?: string;
  [key: string]: unknown;
}

export interface Catalog {
  id: string;
  title?: string;
  values: CatalogValue[];
}

export const catalogPaths = {
  common: {
    sports: "models/catalogs/common/sports.json",
    sexes: "models/catalogs/common/sexes.json",
    sides: "models/catalogs/common/sides.json",
    mediaTypes: "models/catalogs/common/media-types.json",
    referenceCorners: "models/catalogs/common/reference-corners.json",
  },
  swimming: {
    strokes: "models/catalogs/swimming/strokes.json",
    distances: "models/catalogs/swimming/distances.json",
    rounds: "models/catalogs/swimming/rounds.json",
    fieldPresets: "models/catalogs/swimming/field-presets.json",
    annotationEvents: "models/catalogs/swimming/annotation-events.json",
    events: "models/catalogs/swimming/generated/events.json",
  },
  tableTennis: {
    annotationEvents: "models/catalogs/table-tennis/annotation-events.json",
    clipPatterns: "models/catalogs/table-tennis/clip-patterns.json",
  },
} as const;

export async function fetchCatalog(path: string, baseUrl = ""): Promise<Catalog> {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`Unable to load catalog ${path}: ${response.status}`);
  }
  return response.json() as Promise<Catalog>;
}

export function toSelectOptions(catalog: Catalog): Array<{ value: string; label: string }> {
  return catalog.values.map((item) => ({
    value: item.id,
    label: item.label ?? item.id,
  }));
}

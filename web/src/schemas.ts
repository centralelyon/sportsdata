export const schemaPaths = {
  common: {
    media: "models/schemas/common/media.schema.json",
    geometry: "models/schemas/common/geometry.schema.json",
    annotationSimple: "models/schemas/common/annotation-simple.schema.json",
  },
  swimming: {
    eventConfig: "models/schemas/swimming/event-config.schema.json",
    annotationSimple: "models/schemas/swimming/annotation-simple.schema.json",
  },
  tableTennis: {
    matchManifest: "models/schemas/table-tennis/match-manifest.schema.json",
  },
} as const;

export async function fetchSchema(path: string, baseUrl = ""): Promise<Record<string, unknown>> {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`Unable to load schema ${path}: ${response.status}`);
  }
  return response.json() as Promise<Record<string, unknown>>;
}

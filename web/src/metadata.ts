export interface MetadataField {
  id: string;
  sport: string;
  field: string;
  jsonKey: string;
  label: string;
  valueCatalog: {
    scope: string;
    name: string;
    path: string;
  };
  overrideCatalog?: string;
  manualValuesAllowed?: boolean;
  jsonValueField?: string;
  ui?: {
    jsonValueLabel?: string;
    jsonValueControl?: "select" | string;
  };
}

export const metadataPaths = {
  swimming: {
    distance: "models/metadata/swimming/distance.json",
  },
} as const;

export async function fetchMetadataField(path: string, baseUrl = ""): Promise<MetadataField> {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`Unable to load metadata field ${path}: ${response.status}`);
  }
  return response.json() as Promise<MetadataField>;
}

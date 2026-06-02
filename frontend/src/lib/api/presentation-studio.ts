export const PRESENTATION_STUDIO_UI_SCHEMA_VERSION = "presentation_studio_ui.v1";
export const PRESENTATION_STUDIO_OPENAPI_PATH = "/openapi.json";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export type PresentationStudioBlock = {
  block_id: string;
  block_type: "title" | "body" | "chart" | "image" | "table" | "note" | string;
  text?: string | null;
  source_refs?: string[];
  locked?: boolean;
};

export type PresentationStudioSlide = {
  slide_id: string;
  slide_index: number;
  title: string;
  role: string;
  layout_family: string;
  thumbnail_label: string;
  blocks: PresentationStudioBlock[];
  quality_warnings: string[];
  source_refs: string[];
};

export type PresentationStudioAsset = {
  asset_id: string;
  kind: "image" | "chart" | "table" | "citation" | string;
  filename: string;
  checksum_sha256: string;
  provenance_ref: string;
};

export type PresentationStudioSnapshot = {
  schema_version: typeof PRESENTATION_STUDIO_UI_SCHEMA_VERSION;
  presentation_id: string;
  deck_title: string;
  backend_url: string;
  openapi_schema_path: string;
  export_backend_side: true;
  frontend_side_generation_allowed: false;
  arbitrary_model_selector_allowed: false;
  slides: PresentationStudioSlide[];
  assets: PresentationStudioAsset[];
  quality_warnings: string[];
};

export type PresentationStudioDraftRequest = {
  schema_version: typeof PRESENTATION_STUDIO_UI_SCHEMA_VERSION;
  selected_slide_id: string;
  edited_slide_title: string;
  edited_blocks: PresentationStudioBlock[];
  safe_task_events: string[];
};

export type PresentationStudioDraftResponse = {
  presentation_id: string;
  draft_id: string;
  persisted_through_backend_api: true;
  updated_at: string;
};

export type PresentationStudioExportRequest = {
  export_format: "pptx" | "pdf";
  backend_side_export: true;
  presentation_studio_ui_schema_version: typeof PRESENTATION_STUDIO_UI_SCHEMA_VERSION;
};

export type PresentationStudioExportResponse = {
  presentation_id: string;
  artifact_id: string;
  export_format: "pptx" | "pdf";
  backend_side_export: true;
  download_url: string;
};

export function presentationStudioApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configured && configured.length > 0 ? configured.replace(/\/$/, "") : DEFAULT_API_BASE_URL;
}

export function presentationStudioOpenApiUrl(): string {
  return `${presentationStudioApiBaseUrl()}${PRESENTATION_STUDIO_OPENAPI_PATH}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${presentationStudioApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // Keep generic HTTP status when the backend returns non-JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

function jsonRequestInit(method: "POST" | "PUT", payload: unknown): RequestInit {
  return {
    method,
    body: JSON.stringify(payload),
  };
}

export async function getPresentationStudioSnapshot(presentationId: string): Promise<PresentationStudioSnapshot> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to load Presentation Studio.");
  }
  return requestJson<PresentationStudioSnapshot>(`/presentations/${safePresentationId}/studio`);
}

export async function savePresentationStudioDraft(
  presentationId: string,
  request: PresentationStudioDraftRequest,
): Promise<PresentationStudioDraftResponse> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to save Presentation Studio draft edits.");
  }
  return requestJson<PresentationStudioDraftResponse>(
    `/presentations/${safePresentationId}/studio/draft`,
    jsonRequestInit("PUT", request),
  );
}

export async function requestPresentationStudioExport(
  presentationId: string,
  request: PresentationStudioExportRequest,
): Promise<PresentationStudioExportResponse> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to request backend-side export.");
  }
  return requestJson<PresentationStudioExportResponse>(
    `/presentations/${safePresentationId}/exports`,
    jsonRequestInit("POST", request),
  );
}

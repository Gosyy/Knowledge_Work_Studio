export type PresentationCurrentFile = {
  id: string;
  kind: string;
  file_type: string;
  mime_type: string;
  title: string | null;
  original_filename: string | null;
  checksum_sha256: string | null;
  size_bytes: number | null;
  created_at: string;
  updated_at: string;
};

export type PresentationVersionSummary = {
  id: string;
  version_number: number;
  file_id: string;
  parent_version_id: string | null;
  change_summary: string | null;
  created_at: string;
};

export type PresentationSummary = {
  id: string;
  session_id: string;
  current_file_id: string | null;
  presentation_type: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  current_file: PresentationCurrentFile | null;
  latest_version: PresentationVersionSummary | null;
};

const DEFAULT_API_BASE_URL = "http://localhost:8000";

function apiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configured && configured.length > 0 ? configured.replace(/\/$/, "") : DEFAULT_API_BASE_URL;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
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
      // Keep the generic HTTP status message when the backend returns non-JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function listSessionPresentations(sessionId: string): Promise<PresentationSummary[]> {
  const safeSessionId = encodeURIComponent(sessionId.trim());
  if (!safeSessionId) {
    throw new Error("Session id is required to load presentations.");
  }
  return requestJson<PresentationSummary[]>(`/sessions/${safeSessionId}/presentations`);
}

export async function getPresentation(presentationId: string): Promise<PresentationSummary> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required.");
  }
  return requestJson<PresentationSummary>(`/presentations/${safePresentationId}`);
}

export async function listPresentationVersions(presentationId: string): Promise<PresentationVersionSummary[]> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to load version timeline.");
  }
  return requestJson<PresentationVersionSummary[]>(`/presentations/${safePresentationId}/versions`);
}

export type PresentationPlanSlide = {
  slide_id?: string;
  slide_type?: string;
  story_arc_stage?: string;
  title?: string;
  bullets?: string[];
  speaker_notes?: string | null;
  layout_hint?: string | null;
  [key: string]: unknown;
};

export type PresentationPlanPayload = {
  schema_version?: number;
  deck_title?: string;
  deck_goal?: string;
  audience?: string;
  tone?: string;
  target_slide_count?: number;
  story_arc?: string[];
  slides?: PresentationPlanSlide[];
  [key: string]: unknown;
};

export type PresentationPlanSnapshot = {
  snapshot_id: string;
  presentation_id: string;
  presentation_version_id: string | null;
  created_from_task_id: string | null;
  change_summary: string | null;
  created_at: string;
  plan: PresentationPlanPayload;
};

export type PresentationPlanSlideDelta = {
  slide_id: string;
  change_type: "added" | "removed" | "modified";
  before_index: number | null;
  after_index: number | null;
  title_before: string | null;
  title_after: string | null;
  story_arc_stage_before: string | null;
  story_arc_stage_after: string | null;
  layout_hint_before: string | null;
  layout_hint_after: string | null;
  bullets_added: string[];
  bullets_removed: string[];
  speaker_notes_changed: boolean;
};

export type PresentationPlanDiff = {
  presentation_id: string;
  base_version_id: string;
  compared_version_id: string;
  base_snapshot_id: string;
  compared_snapshot_id: string;
  changed_slide_count: number;
  slide_deltas: PresentationPlanSlideDelta[];
};

export async function getCurrentPresentationPlan(presentationId: string): Promise<PresentationPlanSnapshot> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to load the editable plan.");
  }
  return requestJson<PresentationPlanSnapshot>(`/presentations/${safePresentationId}/plan`);
}

export async function getPresentationVersionPlan(
  presentationId: string,
  versionId: string,
): Promise<PresentationPlanSnapshot> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  const safeVersionId = encodeURIComponent(versionId.trim());
  if (!safePresentationId || !safeVersionId) {
    throw new Error("Presentation id and version id are required to load a plan snapshot.");
  }
  return requestJson<PresentationPlanSnapshot>(
    `/presentations/${safePresentationId}/versions/${safeVersionId}/plan`,
  );
}

export async function getPresentationRevisionDiff(
  presentationId: string,
  versionId: string,
): Promise<PresentationPlanDiff> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  const safeVersionId = encodeURIComponent(versionId.trim());
  if (!safePresentationId || !safeVersionId) {
    throw new Error("Presentation id and version id are required to load revision diff.");
  }
  return requestJson<PresentationPlanDiff>(
    `/presentations/${safePresentationId}/revisions/${safeVersionId}/diff`,
  );
}

export type DeckRevisionResponse = {
  presentation_id: string;
  version_id: string;
  version_number: number;
  parent_version_id: string | null;
  stored_file_id: string;
  revised_slide_ids: string[];
  scope: "slide" | "section";
  change_summary: string | null;
  created_at: string;
  current_file_id: string;
  previous_file_id: string | null;
};

export type DeckSlideRevisionRequest = {
  instruction: string;
  target_slide_id?: string | null;
  target_slide_index?: number | null;
  template_id?: string;
  task_id?: string | null;
  change_summary?: string | null;
};

export type DeckSectionRevisionRequest = {
  instruction: string;
  target_stage: string;
  template_id?: string;
  task_id?: string | null;
  change_summary?: string | null;
};

function jsonRequestInit(payload: unknown): RequestInit {
  return {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  };
}

export async function revisePresentationSlideWithoutPlan(
  presentationId: string,
  request: DeckSlideRevisionRequest,
): Promise<DeckRevisionResponse> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to revise a slide.");
  }
  return requestJson<DeckRevisionResponse>(
    `/presentations/${safePresentationId}/revisions/slide`,
    jsonRequestInit(request),
  );
}

export async function revisePresentationSectionWithoutPlan(
  presentationId: string,
  request: DeckSectionRevisionRequest,
): Promise<DeckRevisionResponse> {
  const safePresentationId = encodeURIComponent(presentationId.trim());
  if (!safePresentationId) {
    throw new Error("Presentation id is required to revise a section.");
  }
  return requestJson<DeckRevisionResponse>(
    `/presentations/${safePresentationId}/revisions/section`,
    jsonRequestInit(request),
  );
}

export function formatBytes(sizeBytes: number | null): string {
  if (sizeBytes === null || !Number.isFinite(sizeBytes)) {
    return "unknown size";
  }
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

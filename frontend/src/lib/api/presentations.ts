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

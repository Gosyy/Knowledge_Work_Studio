import { assertSafeArtifactSummary, type ArtifactSummary } from "@/lib/api/artifacts.contract";

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

export async function listSessionArtifacts(sessionId: string): Promise<ArtifactSummary[]> {
  const safeSessionId = encodeURIComponent(sessionId.trim());
  if (!safeSessionId) {
    throw new Error("Session id is required to load artifacts.");
  }

  const artifacts = await requestJson<ArtifactSummary[]>(`/sessions/${safeSessionId}/artifacts`);
  for (const artifact of artifacts) {
    assertSafeArtifactSummary(artifact);
  }
  return artifacts;
}

export function artifactDownloadHref(downloadUrl: string): string {
  if (!downloadUrl.trim()) {
    return "#";
  }
  if (/^https?:\/\//i.test(downloadUrl)) {
    return downloadUrl;
  }
  const normalizedPath = downloadUrl.startsWith("/") ? downloadUrl : `/${downloadUrl}`;
  return `${apiBaseUrl()}${normalizedPath}`;
}

export function formatArtifactBytes(sizeBytes: number | null | undefined): string {
  if (typeof sizeBytes !== "number" || !Number.isFinite(sizeBytes)) {
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

export function formatArtifactDateTime(value: string | null | undefined): string {
  if (!value) {
    return "not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

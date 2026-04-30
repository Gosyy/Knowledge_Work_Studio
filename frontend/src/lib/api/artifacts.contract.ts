"use client";

export type ArtifactSummary = {
  id: string;
  session_id: string;
  task_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
  download_url: string;
};

export function assertSafeArtifactSummary(artifact: ArtifactSummary): void {
  const unknownArtifact = artifact as ArtifactSummary & {
    storage_key?: unknown;
    storage_uri?: unknown;
  };

  if ("storage_key" in unknownArtifact || "storage_uri" in unknownArtifact) {
    throw new Error("Artifact metadata response contains internal storage fields.");
  }

  if (artifact.download_url.includes("local://")) {
    throw new Error("Artifact download URL must not expose internal storage paths.");
  }
}

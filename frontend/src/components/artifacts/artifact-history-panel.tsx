"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  artifactDownloadHref,
  formatArtifactBytes,
  formatArtifactDateTime,
  listSessionArtifacts,
} from "@/lib/api/artifacts";
import type { ArtifactSummary } from "@/lib/api/artifacts.contract";

const mutedTextStyle = {
  color: "#6b7280",
  fontSize: "0.875rem",
};

const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: "0.375rem",
  padding: "0.5rem 0.75rem",
  minWidth: "16rem",
};

const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.5rem 0.75rem",
  cursor: "pointer",
};

const cardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: "0.5rem",
  padding: "0.75rem",
  marginTop: "0.75rem",
};

const metadataGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: "0.5rem",
};

type ArtifactHistoryState = {
  status: "idle" | "loading" | "loaded" | "error";
  error: string | null;
  artifacts: ArtifactSummary[];
};

export function ArtifactHistoryPanel() {
  const [sessionId, setSessionId] = useState("");
  const [state, setState] = useState<ArtifactHistoryState>({
    status: "idle",
    error: null,
    artifacts: [],
  });

  const sortedArtifacts = useMemo(
    () => [...state.artifacts].sort((left, right) => right.created_at.localeCompare(left.created_at)),
    [state.artifacts],
  );

  async function loadArtifacts(event?: FormEvent) {
    event?.preventDefault();

    if (!sessionId.trim()) {
      setState({
        status: "error",
        error: "Enter a session id to load artifact history.",
        artifacts: [],
      });
      return;
    }

    setState((current) => ({ ...current, status: "loading", error: null }));

    try {
      const artifacts = await listSessionArtifacts(sessionId);
      setState({
        status: "loaded",
        error: null,
        artifacts,
      });
    } catch (error) {
      setState({
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load artifact history.",
        artifacts: [],
      });
    }
  }

  return (
    <section aria-labelledby="artifact-history-heading">
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "baseline" }}>
        <div>
          <h2 id="artifact-history-heading">Artifact history</h2>
          <p style={mutedTextStyle}>Download generated exports without exposing internal storage paths.</p>
        </div>
        <span style={mutedTextStyle}>{state.artifacts.length} loaded</span>
      </div>

      <form onSubmit={loadArtifacts} style={{ display: "flex", gap: "0.75rem", alignItems: "end", flexWrap: "wrap" }}>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Artifact history key
          <input
            value={sessionId}
            onChange={(event) => setSessionId(event.target.value)}
            placeholder="ses_..."
            style={inputStyle}
            aria-label="Artifact history key"
          />
        </label>
        <button type="submit" style={buttonStyle} disabled={state.status === "loading"}>
          {state.status === "loading" ? "Loading..." : "Load artifacts"}
        </button>
      </form>

      {state.error ? (
        <p role="alert" style={{ color: "#b91c1c" }}>
          {state.error}
        </p>
      ) : null}

      {state.status === "loaded" && sortedArtifacts.length === 0 ? (
        <p style={mutedTextStyle}>No artifacts were found for this session.</p>
      ) : null}

      {sortedArtifacts.length > 0 ? (
        <div aria-label="Artifact export history">
          {sortedArtifacts.map((artifact) => (
            <article key={artifact.id} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                <div>
                  <h3>{artifact.filename}</h3>
                  <p style={mutedTextStyle}>{artifact.content_type}</p>
                </div>
                <a href={artifactDownloadHref(artifact.download_url)} style={buttonStyle}>
                  Download artifact
                </a>
              </div>
              <dl style={metadataGridStyle}>
                <MetadataRow label="Artifact id" value={artifact.id} />
                <MetadataRow label="Task id" value={artifact.task_id} />
                <MetadataRow label="Size" value={formatArtifactBytes(artifact.size_bytes)} />
                <MetadataRow label="Created" value={formatArtifactDateTime(artifact.created_at)} />
              </dl>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt style={{ ...mutedTextStyle, fontWeight: 600 }}>{label}</dt>
      <dd style={{ margin: 0 }}>{value}</dd>
    </div>
  );
}

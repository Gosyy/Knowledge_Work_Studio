"use client";

import { FormEvent, useMemo, useState } from "react";
import { PlanSnapshotInspector } from "@/components/presentations/plan-snapshot-inspector";
import { RevisionActionPanel } from "@/components/presentations/revision-action-panel";
import {
  formatBytes,
  formatDateTime,
  getPresentation,
  listSessionPresentations,
  type PresentationSummary,
} from "@/lib/api/presentations";

const mutedTextStyle = {
  color: "#6b7280",
  fontSize: "0.875rem",
};

const rowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: "1rem",
  borderBottom: "1px solid #e5e7eb",
  padding: "0.5rem 0",
};

const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.5rem 0.75rem",
  cursor: "pointer",
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#ffffff",
  color: "#111827",
};

const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: "0.375rem",
  padding: "0.5rem 0.75rem",
  minWidth: "16rem",
};

type RegistryState = {
  status: "idle" | "loading" | "loaded" | "error";
  error: string | null;
  presentations: PresentationSummary[];
  selected: PresentationSummary | null;
};

export function PresentationRegistryPanel() {
  const [sessionId, setSessionId] = useState("");
  const [state, setState] = useState<RegistryState>({
    status: "idle",
    error: null,
    presentations: [],
    selected: null,
  });

  const sortedPresentations = useMemo(
    () =>
      [...state.presentations].sort((left, right) =>
        right.updated_at.localeCompare(left.updated_at),
      ),
    [state.presentations],
  );

  async function loadPresentations(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();

    if (!sessionId.trim()) {
      setState((current) => ({
        ...current,
        status: "error",
        error: "Enter a session id to load generated presentations.",
      }));
      return;
    }

    setState((current) => ({ ...current, status: "loading", error: null }));
    try {
      const presentations = await listSessionPresentations(sessionId);
      setState({
        status: "loaded",
        error: null,
        presentations,
        selected: presentations[0] ?? null,
      });
    } catch (error) {
      setState({
        status: "error",
        error: error instanceof Error ? error.message : "Unable to load presentations.",
        presentations: [],
        selected: null,
      });
    }
  }

  async function openPresentation(presentationId: string) {
    setState((current) => ({ ...current, status: "loading", error: null }));
    try {
      const selected = await getPresentation(presentationId);
      setState((current) => ({
        status: "loaded",
        error: null,
        presentations: current.presentations.map((presentation) =>
          presentation.id === selected.id ? selected : presentation,
        ),
        selected,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Unable to open presentation.",
      }));
    }
  }

  return (
    <section aria-labelledby="presentation-registry-title">
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start" }}>
        <div>
          <h2 id="presentation-registry-title">Presentations</h2>
          <p style={mutedTextStyle}>List generated decks for a session and inspect safe metadata.</p>
        </div>
        <span style={{ ...mutedTextStyle, whiteSpace: "nowrap" }}>
          {state.presentations.length} loaded
        </span>
      </div>

      <form onSubmit={loadPresentations} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem" }}>
        <label>
          <span style={{ display: "block", fontSize: "0.875rem", marginBottom: "0.25rem" }}>
            Session id
          </span>
          <input
            value={sessionId}
            onChange={(event) => setSessionId(event.target.value)}
            placeholder="ses_..."
            style={inputStyle}
            aria-label="Session id"
          />
        </label>
        <button type="submit" style={{ ...buttonStyle, alignSelf: "end" }} disabled={state.status === "loading"}>
          {state.status === "loading" ? "Loading..." : "Load presentations"}
        </button>
      </form>

      {state.error ? (
        <div role="alert" style={{ marginTop: "1rem", color: "#991b1b", background: "#fef2f2", padding: "0.75rem", borderRadius: "0.375rem" }}>
          {state.error}
        </div>
      ) : null}

      {state.status === "loaded" && sortedPresentations.length === 0 ? (
        <p style={{ ...mutedTextStyle, marginTop: "1rem" }}>
          No presentations were found for this session.
        </p>
      ) : null}

      {sortedPresentations.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(280px, 0.85fr)", gap: "1rem", marginTop: "1rem" }}>
          <div aria-label="presentation-list">
            {sortedPresentations.map((presentation) => (
              <article
                key={presentation.id}
                style={{
                  border: presentation.id === state.selected?.id ? "2px solid #111827" : "1px solid #e5e7eb",
                  borderRadius: "0.5rem",
                  padding: "0.75rem",
                  marginBottom: "0.75rem",
                  background: "#ffffff",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{presentation.title}</h3>
                    <p style={mutedTextStyle}>{presentation.presentation_type} · {presentation.status}</p>
                  </div>
                  <button
                    type="button"
                    style={secondaryButtonStyle}
                    onClick={() => void openPresentation(presentation.id)}
                  >
                    Open
                  </button>
                </div>
                <div style={{ ...mutedTextStyle, marginTop: "0.5rem" }}>
                  Current file: {presentation.current_file_id ?? "not assigned"} · Updated: {formatDateTime(presentation.updated_at)}
                </div>
              </article>
            ))}
          </div>

          <PresentationDetailCard
            presentation={state.selected}
            onPresentationUpdated={(presentation) =>
              setState((current) => ({
                ...current,
                selected: presentation,
                presentations: current.presentations.map((item) =>
                  item.id === presentation.id ? presentation : item,
                ),
              }))
            }
          />
        </div>
      ) : null}
    </section>
  );
}

function PresentationDetailCard({
  presentation,
  onPresentationUpdated,
}: {
  presentation: PresentationSummary | null;
  onPresentationUpdated: (presentation: PresentationSummary) => void;
}) {
  if (!presentation) {
    return (
      <aside style={{ border: "1px dashed #d1d5db", borderRadius: "0.5rem", padding: "1rem" }}>
        <h3>Presentation detail</h3>
        <p style={mutedTextStyle}>Select a presentation to inspect safe metadata.</p>
      </aside>
    );
  }

  return (
    <aside style={{ border: "1px solid #d1d5db", borderRadius: "0.5rem", padding: "1rem", background: "#f9fafb" }}>
      <h3 style={{ marginTop: 0 }}>{presentation.title}</h3>
      <dl>
        <MetadataRow label="Presentation id" value={presentation.id} />
        <MetadataRow label="Session id" value={presentation.session_id} />
        <MetadataRow label="Status" value={presentation.status} />
        <MetadataRow label="Type" value={presentation.presentation_type} />
        <MetadataRow label="Created" value={formatDateTime(presentation.created_at)} />
        <MetadataRow label="Updated" value={formatDateTime(presentation.updated_at)} />
      </dl>

      <h4>Current file</h4>
      {presentation.current_file ? (
        <dl>
          <MetadataRow label="File id" value={presentation.current_file.id} />
          <MetadataRow label="Kind" value={presentation.current_file.kind} />
          <MetadataRow label="File type" value={presentation.current_file.file_type} />
          <MetadataRow label="Filename" value={presentation.current_file.original_filename ?? "not available"} />
          <MetadataRow label="Size" value={formatBytes(presentation.current_file.size_bytes)} />
        </dl>
      ) : (
        <p style={mutedTextStyle}>No current file is attached.</p>
      )}

      <h4>Latest version</h4>
      {presentation.latest_version ? (
        <dl>
          <MetadataRow label="Version" value={`v${presentation.latest_version.version_number}`} />
          <MetadataRow label="Version id" value={presentation.latest_version.id} />
          <MetadataRow label="Parent" value={presentation.latest_version.parent_version_id ?? "none"} />
          <MetadataRow label="Change" value={presentation.latest_version.change_summary ?? "not provided"} />
        </dl>
      ) : (
        <p style={mutedTextStyle}>No version metadata is available.</p>
      )}

      <PlanSnapshotInspector presentation={presentation} />
      <RevisionActionPanel
        presentation={presentation}
        onRevisionApplied={async () => {
          const updated = await getPresentation(presentation.id);
          onPresentationUpdated(updated);
        }}
      />
    </aside>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={rowStyle}>
      <dt style={{ fontWeight: 600 }}>{label}</dt>
      <dd style={{ margin: 0, textAlign: "right", overflowWrap: "anywhere" }}>{value}</dd>
    </div>
  );
}

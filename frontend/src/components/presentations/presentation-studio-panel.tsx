"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  PRESENTATION_STUDIO_UI_SCHEMA_VERSION,
  getPresentationStudioSnapshot,
  presentationStudioApiBaseUrl,
  presentationStudioOpenApiUrl,
  requestPresentationStudioExport,
  savePresentationStudioDraft,
  type PresentationStudioBlock,
  type PresentationStudioDraftResponse,
  type PresentationStudioExportResponse,
  type PresentationStudioSlide,
  type PresentationStudioSnapshot,
} from "@/lib/api/presentation-studio";

type StudioStatus = "idle" | "loading" | "loaded" | "saving" | "saved" | "exporting" | "export_ready" | "error";

const mutedTextStyle = { color: "#6b7280", fontSize: "0.875rem" };
const inputStyle = {
  border: "1px solid #d1d5db",
  borderRadius: "0.375rem",
  padding: "0.5rem 0.75rem",
  width: "100%",
  boxSizing: "border-box" as const,
};
const buttonStyle = {
  border: "1px solid #111827",
  borderRadius: "0.375rem",
  background: "#111827",
  color: "#ffffff",
  padding: "0.5rem 0.75rem",
  cursor: "pointer",
};
const secondaryButtonStyle = { ...buttonStyle, background: "#ffffff", color: "#111827" };
const cardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: "0.5rem",
  padding: "0.75rem",
};
const studioGridStyle = {
  display: "grid",
  gridTemplateColumns: "14rem minmax(0, 1fr) 18rem",
  gap: "0.75rem",
  alignItems: "start",
};
const thumbnailButtonStyle = {
  ...secondaryButtonStyle,
  width: "100%",
  textAlign: "left" as const,
  marginBottom: "0.5rem",
};
const canvasStyle = {
  ...cardStyle,
  minHeight: "18rem",
  background: "linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)",
  display: "grid",
  gap: "0.75rem",
};
const blockStyle = {
  border: "1px dashed #9ca3af",
  borderRadius: "0.375rem",
  padding: "0.5rem",
  background: "rgba(255,255,255,0.85)",
};

const safeTaskEvents = [
  "presentation_studio.loaded",
  "presentation_studio.slide_selected",
  "presentation_studio.draft_saved_via_backend_api",
  "presentation_studio.backend_export_requested",
];

function normalizeText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function slideBlocks(slide: PresentationStudioSlide | null): PresentationStudioBlock[] {
  return Array.isArray(slide?.blocks) ? [...slide.blocks] : [];
}

function slideById(snapshot: PresentationStudioSnapshot | null, slideId: string | null): PresentationStudioSlide | null {
  if (!snapshot || !slideId) return null;
  return snapshot.slides.find((slide) => slide.slide_id === slideId) ?? null;
}

export function PresentationStudioPanel() {
  const [presentationId, setPresentationId] = useState("pres_studio_ui");
  const [snapshot, setSnapshot] = useState<PresentationStudioSnapshot | null>(null);
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);
  const [editableTitle, setEditableTitle] = useState("");
  const [status, setStatus] = useState<StudioStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [draftResponse, setDraftResponse] = useState<PresentationStudioDraftResponse | null>(null);
  const [exportResponse, setExportResponse] = useState<PresentationStudioExportResponse | null>(null);

  const selectedSlide = useMemo(() => slideById(snapshot, selectedSlideId), [snapshot, selectedSlideId]);
  const blocks = useMemo(() => slideBlocks(selectedSlide), [selectedSlide]);
  const backendUrl = presentationStudioApiBaseUrl();
  const openApiUrl = presentationStudioOpenApiUrl();

  async function loadStudio(event?: FormEvent) {
    event?.preventDefault();
    const safePresentationId = normalizeText(presentationId);
    if (!safePresentationId) {
      setStatus("error");
      setError("Enter a presentation id to open Presentation Studio.");
      return;
    }
    setStatus("loading");
    setError(null);
    setDraftResponse(null);
    setExportResponse(null);
    try {
      const loaded = await getPresentationStudioSnapshot(safePresentationId);
      setSnapshot(loaded);
      const firstSlide = loaded.slides[0] ?? null;
      setSelectedSlideId(firstSlide?.slide_id ?? null);
      setEditableTitle(firstSlide?.title ?? "");
      setStatus("loaded");
    } catch (loadError) {
      setSnapshot(null);
      setSelectedSlideId(null);
      setEditableTitle("");
      setStatus("error");
      setError(loadError instanceof Error ? loadError.message : "Unable to load Presentation Studio.");
    }
  }

  function selectSlide(slide: PresentationStudioSlide) {
    setSelectedSlideId(slide.slide_id);
    setEditableTitle(slide.title);
    setDraftResponse(null);
    setExportResponse(null);
    setStatus((current) => (current === "error" ? "loaded" : current));
    setError(null);
  }

  async function saveDraft() {
    const safePresentationId = normalizeText(presentationId);
    const safeTitle = normalizeText(editableTitle);
    if (!safePresentationId || !selectedSlide || !safeTitle) {
      setStatus("error");
      setError("Select a slide and enter a non-empty title before saving.");
      return;
    }
    setStatus("saving");
    setError(null);
    try {
      const response = await savePresentationStudioDraft(safePresentationId, {
        schema_version: PRESENTATION_STUDIO_UI_SCHEMA_VERSION,
        selected_slide_id: selectedSlide.slide_id,
        edited_slide_title: safeTitle,
        edited_blocks: blocks.map((block) => ({ ...block, text: block.block_type === "title" ? safeTitle : block.text })),
        safe_task_events: safeTaskEvents,
      });
      setDraftResponse(response);
      setSnapshot((current) => {
        if (!current) return current;
        return {
          ...current,
          slides: current.slides.map((slide) =>
            slide.slide_id === selectedSlide.slide_id ? { ...slide, title: safeTitle } : slide,
          ),
        };
      });
      setStatus("saved");
    } catch (saveError) {
      setDraftResponse(null);
      setStatus("error");
      setError(saveError instanceof Error ? saveError.message : "Unable to save Presentation Studio draft.");
    }
  }

  async function requestExport() {
    const safePresentationId = normalizeText(presentationId);
    if (!safePresentationId) {
      setStatus("error");
      setError("Presentation id is required before export.");
      return;
    }
    setStatus("exporting");
    setError(null);
    try {
      const response = await requestPresentationStudioExport(safePresentationId, {
        export_format: "pptx",
        backend_side_export: true,
        presentation_studio_ui_schema_version: PRESENTATION_STUDIO_UI_SCHEMA_VERSION,
      });
      setExportResponse(response);
      setStatus("export_ready");
    } catch (exportError) {
      setExportResponse(null);
      setStatus("error");
      setError(exportError instanceof Error ? exportError.message : "Unable to request backend-side export.");
    }
  }

  return (
    <section>
      <h2>Presentation Studio</h2>
      <p style={mutedTextStyle}>
        API-first slide workspace for thumbnails, canvas preview, block inspection, asset provenance, quality warnings, backend draft persistence, and backend-side export.
      </p>
      <p style={mutedTextStyle}>Backend API: {backendUrl} · OpenAPI: {openApiUrl}</p>
      <p style={mutedTextStyle}>Frontend-side generation: disabled · Arbitrary model selector: disabled · Export source of truth: backend</p>

      <form onSubmit={(event) => void loadStudio(event)} style={{ display: "flex", gap: "0.75rem", alignItems: "end", flexWrap: "wrap" }}>
        <label style={{ display: "grid", gap: "0.25rem", minWidth: "18rem" }}>
          Presentation Studio id
          <input
            value={presentationId}
            onChange={(event) => setPresentationId(event.target.value)}
            placeholder="pres_..."
            style={inputStyle}
            aria-label="Presentation Studio id"
          />
        </label>
        <button type="submit" style={buttonStyle} disabled={status === "loading"}>
          {status === "loading" ? "Loading studio..." : "Load Presentation Studio"}
        </button>
      </form>

      {error ? <p role="alert" style={{ color: "#b91c1c" }}>{error}</p> : null}
      <div role="status" style={{ ...mutedTextStyle, marginTop: "0.75rem" }}>Presentation Studio status: {status}</div>

      {snapshot ? (
        <div style={{ ...cardStyle, marginTop: "0.75rem" }}>
          <h3>{snapshot.deck_title}</h3>
          <p style={mutedTextStyle}>Schema {snapshot.schema_version} · backend-side export only · {snapshot.slides.length} slide(s)</p>

          <div style={studioGridStyle}>
            <aside aria-label="Slide thumbnails" style={cardStyle}>
              <h4>Slide thumbnails</h4>
              {snapshot.slides.map((slide) => (
                <button
                  key={slide.slide_id}
                  type="button"
                  style={{ ...thumbnailButtonStyle, borderColor: slide.slide_id === selectedSlideId ? "#111827" : "#d1d5db" }}
                  onClick={() => selectSlide(slide)}
                  aria-label={`Select slide ${slide.slide_index}`}
                >
                  {slide.thumbnail_label} · {slide.title}
                </button>
              ))}
            </aside>

            <section aria-label="Slide canvas preview" style={canvasStyle}>
              <h4>Canvas preview</h4>
              {selectedSlide ? (
                <>
                  <strong>{selectedSlide.title}</strong>
                  <p style={mutedTextStyle}>Role: {selectedSlide.role} · Layout: {selectedSlide.layout_family}</p>
                  {blocks.map((block) => (
                    <div key={block.block_id} style={blockStyle}>
                      <strong>{block.block_type}</strong>
                      <p>{block.text ?? "Source-backed non-text block"}</p>
                      <small>Sources: {(block.source_refs ?? selectedSlide.source_refs).join(", ") || "none"}</small>
                    </div>
                  ))}
                </>
              ) : (
                <p style={mutedTextStyle}>Load a studio snapshot to preview a slide.</p>
              )}
            </section>

            <aside aria-label="Block inspector" style={cardStyle}>
              <h4>Block inspector</h4>
              {selectedSlide ? (
                <>
                  <label style={{ display: "grid", gap: "0.25rem" }}>
                    Selected slide title
                    <input
                      value={editableTitle}
                      onChange={(event) => setEditableTitle(event.target.value)}
                      style={inputStyle}
                      aria-label="Selected slide title"
                    />
                  </label>
                  <p style={mutedTextStyle}>Quality warnings</p>
                  {selectedSlide.quality_warnings.length > 0 ? (
                    <ul>{selectedSlide.quality_warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                  ) : (
                    <p>No quality warnings for this slide.</p>
                  )}
                  <button type="button" style={buttonStyle} onClick={() => void saveDraft()} disabled={status === "saving"}>
                    Save studio draft via backend API
                  </button>
                  {draftResponse ? <p>Saved draft {draftResponse.draft_id} through backend API.</p> : null}
                </>
              ) : (
                <p style={mutedTextStyle}>Select a slide to inspect editable blocks.</p>
              )}
            </aside>
          </div>

          <section aria-label="Asset tray" style={{ ...cardStyle, marginTop: "0.75rem" }}>
            <h4>Asset tray</h4>
            {snapshot.assets.length > 0 ? (
              <ul>
                {snapshot.assets.map((asset) => (
                  <li key={asset.asset_id}>
                    {asset.kind}: {asset.filename} · {asset.provenance_ref} · {asset.checksum_sha256}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No source assets were attached to this studio snapshot.</p>
            )}
          </section>

          <section aria-label="Deck quality warnings" style={{ ...cardStyle, marginTop: "0.75rem" }}>
            <h4>Deck quality warnings</h4>
            {snapshot.quality_warnings.length > 0 ? (
              <ul>{snapshot.quality_warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
            ) : (
              <p>No deck-level quality warnings.</p>
            )}
          </section>

          <section aria-label="Backend export" style={{ ...cardStyle, marginTop: "0.75rem" }}>
            <h4>Backend export</h4>
            <p style={mutedTextStyle}>Export requests are sent to backend APIs; the frontend never writes PPTX/PDF files itself.</p>
            <button type="button" style={secondaryButtonStyle} onClick={() => void requestExport()} disabled={status === "exporting"}>
              Request backend PPTX export
            </button>
            {exportResponse ? <p>Backend export ready: {exportResponse.artifact_id} · {exportResponse.download_url}</p> : null}
          </section>
        </div>
      ) : null}
    </section>
  );
}

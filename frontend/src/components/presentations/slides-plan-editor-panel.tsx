"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  formatDateTime,
  getCurrentPresentationPlan,
  type PresentationPlanPayload,
  type PresentationPlanSlide,
  type PresentationPlanSnapshot,
} from "@/lib/api/presentations";

type RenderMode = "adaptive" | "template";

type EditorStatus = "idle" | "loading" | "loaded" | "saved" | "ready" | "error";

type RetryPreview = {
  presentation_id: string;
  source_snapshot_id: string;
  render_mode: RenderMode;
  instruction: string;
  safe_task_events: string[];
  plan: PresentationPlanPayload;
};

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
const fieldGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: "0.75rem",
};
const cardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: "0.5rem",
  padding: "0.75rem",
  marginTop: "0.75rem",
};
const eventList = [
  "slides.plan.loaded_for_edit",
  "slides.plan.edited",
  "slides.render_mode.selected",
  "slides.retry.from_saved_plan.requested",
  "slides.generation.ready_for_backend",
];

function normalizeText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function planSlides(plan: PresentationPlanPayload | null): PresentationPlanSlide[] {
  return Array.isArray(plan?.slides) ? [...plan.slides] : [];
}

function slideBulletsValue(slide: PresentationPlanSlide): string {
  return Array.isArray(slide.bullets) ? slide.bullets.join("\n") : "";
}

function parseBullets(value: string): string[] {
  return value
    .split("\n")
    .map((line) => normalizeText(line))
    .filter(Boolean);
}

function validatePlan(plan: PresentationPlanPayload | null): string[] {
  const errors: string[] = [];
  const title = normalizeText(String(plan?.deck_title ?? ""));
  const slides = planSlides(plan);
  if (!title) {
    errors.push("Deck title is required before retry.");
  }
  if (slides.length === 0) {
    errors.push("At least one slide is required before retry.");
  }
  slides.forEach((slide, index) => {
    if (!normalizeText(String(slide.title ?? ""))) {
      errors.push(`Slide ${index + 1} title is required.`);
    }
  });
  return errors;
}

export function SlidesPlanEditorPanel() {
  const [presentationId, setPresentationId] = useState("");
  const [snapshot, setSnapshot] = useState<PresentationPlanSnapshot | null>(null);
  const [editablePlan, setEditablePlan] = useState<PresentationPlanPayload | null>(null);
  const [savedPlan, setSavedPlan] = useState<PresentationPlanPayload | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>("adaptive");
  const [retryInstruction, setRetryInstruction] = useState("");
  const [status, setStatus] = useState<EditorStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [retryPreview, setRetryPreview] = useState<RetryPreview | null>(null);

  const editableSlides = useMemo(() => planSlides(editablePlan).slice(0, 8), [editablePlan]);
  const canSaveDraft = Boolean(editablePlan && status !== "loading");
  const canPrepareRetry = Boolean(savedPlan && normalizeText(retryInstruction).length >= 8);

  async function loadPlan(event?: FormEvent) {
    event?.preventDefault();
    const safePresentationId = normalizeText(presentationId);
    if (!safePresentationId) {
      setStatus("error");
      setError("Enter a presentation id to load a saved editable plan.");
      return;
    }
    setStatus("loading");
    setError(null);
    setRetryPreview(null);
    try {
      const loadedSnapshot = await getCurrentPresentationPlan(safePresentationId);
      setSnapshot(loadedSnapshot);
      setEditablePlan(loadedSnapshot.plan);
      setSavedPlan(null);
      setStatus("loaded");
    } catch (loadError) {
      setSnapshot(null);
      setEditablePlan(null);
      setSavedPlan(null);
      setStatus("error");
      setError(loadError instanceof Error ? loadError.message : "Unable to load editable plan.");
    }
  }

  function updatePlan(update: Partial<PresentationPlanPayload>) {
    setEditablePlan((current) => (current ? { ...current, ...update } : current));
    setSavedPlan(null);
    setRetryPreview(null);
    setStatus((current) => (current === "error" ? "loaded" : current));
    setError(null);
  }

  function updateSlide(index: number, update: Partial<PresentationPlanSlide>) {
    setEditablePlan((current) => {
      if (!current) return current;
      const slides = planSlides(current);
      if (!slides[index]) return current;
      slides[index] = { ...slides[index], ...update };
      return {
        ...current,
        slides,
        target_slide_count: typeof current.target_slide_count === "number" ? current.target_slide_count : slides.length,
      };
    });
    setSavedPlan(null);
    setRetryPreview(null);
    setStatus((current) => (current === "error" ? "loaded" : current));
    setError(null);
  }

  function saveEditableDraft() {
    const validationErrors = validatePlan(editablePlan);
    if (validationErrors.length > 0) {
      setStatus("error");
      setError(validationErrors.join(" "));
      setSavedPlan(null);
      setRetryPreview(null);
      return;
    }
    if (!editablePlan) return;
    const slides = planSlides(editablePlan);
    const normalizedPlan: PresentationPlanPayload = {
      ...editablePlan,
      deck_title: normalizeText(String(editablePlan.deck_title ?? "")),
      slides,
      target_slide_count: typeof editablePlan.target_slide_count === "number" ? editablePlan.target_slide_count : slides.length,
    };
    setEditablePlan(normalizedPlan);
    setSavedPlan(normalizedPlan);
    setRetryPreview(null);
    setStatus("saved");
    setError(null);
  }

  function prepareRetryFromSavedPlan() {
    if (!savedPlan || !snapshot) {
      setStatus("error");
      setError("Save an editable plan draft before preparing retry.");
      return;
    }
    const instruction = normalizeText(retryInstruction);
    if (instruction.length < 8) {
      setStatus("error");
      setError("Retry instruction must be at least 8 characters.");
      return;
    }
    const preview: RetryPreview = {
      presentation_id: normalizeText(presentationId),
      source_snapshot_id: snapshot.snapshot_id,
      render_mode: renderMode,
      instruction,
      safe_task_events: eventList,
      plan: savedPlan,
    };
    setRetryPreview(preview);
    setStatus("ready");
    setError(null);
  }

  return (
    <section>
      <h2>Slides plan editor</h2>
      <p style={mutedTextStyle}>
        Load a saved plan snapshot, edit the outline before generation, select adaptive or template mode, and prepare a safe retry request.
      </p>

      <form onSubmit={(event) => void loadPlan(event)} style={{ display: "flex", gap: "0.75rem", alignItems: "end", flexWrap: "wrap" }}>
        <label style={{ display: "grid", gap: "0.25rem", minWidth: "18rem" }}>
          Plan editor presentation id
          <input
            value={presentationId}
            onChange={(event) => setPresentationId(event.target.value)}
            placeholder="pres_..."
            style={inputStyle}
            aria-label="Plan editor presentation id"
          />
        </label>
        <button type="submit" style={buttonStyle} disabled={status === "loading"}>
          {status === "loading" ? "Loading editable plan..." : "Load editable plan"}
        </button>
      </form>

      {error ? <p role="alert" style={{ color: "#b91c1c" }}>{error}</p> : null}

      <div role="status" style={{ ...mutedTextStyle, marginTop: "0.75rem" }}>
        Plan-first status: {status}
      </div>

      {snapshot && editablePlan ? (
        <div style={cardStyle}>
          <h3>Editable saved plan</h3>
          <p style={mutedTextStyle}>
            Snapshot {snapshot.snapshot_id} · Version {snapshot.presentation_version_id ?? "current"} · {formatDateTime(snapshot.created_at)}
          </p>

          <div style={fieldGridStyle}>
            <label style={{ display: "grid", gap: "0.25rem" }}>
              Editable deck title
              <input
                value={String(editablePlan.deck_title ?? "")}
                onChange={(event) => updatePlan({ deck_title: event.target.value })}
                style={inputStyle}
                aria-label="Editable deck title"
              />
            </label>
            <label style={{ display: "grid", gap: "0.25rem" }}>
              Target slide count
              <input
                value={String(editablePlan.target_slide_count ?? editableSlides.length)}
                onChange={(event) => {
                  const parsed = Number.parseInt(event.target.value, 10);
                  updatePlan({ target_slide_count: Number.isFinite(parsed) ? parsed : editableSlides.length });
                }}
                style={inputStyle}
                aria-label="Target slide count"
                inputMode="numeric"
              />
            </label>
          </div>

          <fieldset style={{ ...cardStyle, marginTop: "1rem" }}>
            <legend>Render mode</legend>
            <label style={{ marginRight: "1rem" }}>
              <input
                type="radio"
                name="slides-render-mode"
                checked={renderMode === "adaptive"}
                onChange={() => setRenderMode("adaptive")}
                aria-label="Adaptive mode"
              />{" "}
              Adaptive mode
            </label>
            <label>
              <input
                type="radio"
                name="slides-render-mode"
                checked={renderMode === "template"}
                onChange={() => setRenderMode("template")}
                aria-label="Template mode"
              />{" "}
              Template mode
            </label>
          </fieldset>

          <div style={{ marginTop: "1rem" }}>
            <h4>Outline slides</h4>
            {editableSlides.length > 0 ? (
              <ol>
                {editableSlides.map((slide, index) => (
                  <li key={slide.slide_id ?? index} style={{ marginBottom: "0.75rem" }}>
                    <div style={fieldGridStyle}>
                      <label style={{ display: "grid", gap: "0.25rem" }}>
                        Slide {index + 1} title
                        <input
                          value={String(slide.title ?? "")}
                          onChange={(event) => updateSlide(index, { title: event.target.value })}
                          style={inputStyle}
                          aria-label={`Slide ${index + 1} title`}
                        />
                      </label>
                      <label style={{ display: "grid", gap: "0.25rem" }}>
                        Slide {index + 1} stage
                        <input
                          value={String(slide.story_arc_stage ?? "")}
                          onChange={(event) => updateSlide(index, { story_arc_stage: event.target.value })}
                          style={inputStyle}
                          aria-label={`Slide ${index + 1} stage`}
                        />
                      </label>
                    </div>
                    <label style={{ display: "grid", gap: "0.25rem", marginTop: "0.5rem" }}>
                      Slide {index + 1} bullets
                      <textarea
                        value={slideBulletsValue(slide)}
                        onChange={(event) => updateSlide(index, { bullets: parseBullets(event.target.value) })}
                        style={{ ...inputStyle, minHeight: "4.5rem" }}
                        aria-label={`Slide ${index + 1} bullets`}
                      />
                    </label>
                  </li>
                ))}
              </ol>
            ) : (
              <p style={mutedTextStyle}>No editable slides were found in this plan snapshot.</p>
            )}
          </div>

          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "end" }}>
            <button type="button" style={secondaryButtonStyle} onClick={saveEditableDraft} disabled={!canSaveDraft}>
              Save editable plan draft
            </button>
            <label style={{ display: "grid", gap: "0.25rem", minWidth: "22rem", flex: "1" }}>
              Retry instruction
              <input
                value={retryInstruction}
                onChange={(event) => setRetryInstruction(event.target.value)}
                placeholder="Explain why this saved plan should be retried."
                style={inputStyle}
                aria-label="Retry instruction"
              />
            </label>
            <button type="button" style={buttonStyle} onClick={prepareRetryFromSavedPlan} disabled={!canPrepareRetry}>
              Prepare retry from saved plan
            </button>
          </div>
        </div>
      ) : null}

      {status === "saved" ? <p role="status">Saved editable plan draft.</p> : null}

      {retryPreview ? (
        <section style={cardStyle}>
          <h3>Retry from saved plan ready</h3>
          <p>
            {retryPreview.render_mode} mode · {retryPreview.source_snapshot_id} · {planSlides(retryPreview.plan).length} slide(s)
          </p>
          <pre style={{ overflowX: "auto", whiteSpace: "pre-wrap" }}>{JSON.stringify(retryPreview, null, 2)}</pre>
        </section>
      ) : null}
    </section>
  );
}

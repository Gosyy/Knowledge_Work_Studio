import {
  PRESENTATION_STUDIO_OPENAPI_PATH,
  PRESENTATION_STUDIO_UI_SCHEMA_VERSION,
  presentationStudioOpenApiUrl,
  type PresentationStudioSnapshot,
} from "./presentation-studio";

const samplePresentationStudioSnapshot: PresentationStudioSnapshot = {
  schema_version: PRESENTATION_STUDIO_UI_SCHEMA_VERSION,
  presentation_id: "pres_studio_contract",
  deck_title: "Presentation Studio Contract Deck",
  backend_url: "http://localhost:8000",
  openapi_schema_path: PRESENTATION_STUDIO_OPENAPI_PATH,
  export_backend_side: true,
  frontend_side_generation_allowed: false,
  arbitrary_model_selector_allowed: false,
  slides: [
    {
      slide_id: "slide_001",
      slide_index: 1,
      title: "Contract overview",
      role: "opening",
      layout_family: "title_body",
      thumbnail_label: "01",
      blocks: [{ block_id: "b_title", block_type: "title", text: "Contract overview", source_refs: ["src_001"] }],
      quality_warnings: [],
      source_refs: ["src_001"],
    },
  ],
  assets: [
    {
      asset_id: "asset_image_001",
      kind: "image",
      filename: "source-chart.png",
      checksum_sha256: "sha256:contract",
      provenance_ref: "src_001",
    },
  ],
  quality_warnings: ["contract-only UI smoke; backend remains source of truth"],
};

if (samplePresentationStudioSnapshot.frontend_side_generation_allowed !== false) {
  throw new Error("Presentation Studio must not allow frontend-side generation as source of truth.");
}

if (samplePresentationStudioSnapshot.export_backend_side !== true) {
  throw new Error("Presentation Studio export must remain backend-side.");
}

if (!presentationStudioOpenApiUrl().endsWith(PRESENTATION_STUDIO_OPENAPI_PATH)) {
  throw new Error("Presentation Studio OpenAPI URL contract failed.");
}

export { samplePresentationStudioSnapshot };

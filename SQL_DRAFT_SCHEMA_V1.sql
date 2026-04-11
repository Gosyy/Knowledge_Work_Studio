-- SQL_DRAFT_SCHEMA_V1.sql
-- KW Studio
-- Postgres draft schema v1
--
-- Based on DB_AND_STORAGE_ARCHITECTURE.md
-- Goals:
-- - Postgres as the single metadata truth layer
-- - storage backend as the binary truth layer
-- - lineage/provenance support
-- - versioning support
-- - task/execution/LLM traceability
--
-- Notes:
-- - This is a draft schema meant for implementation planning.
-- - It intentionally does not include every future optimization.
-- - Binary files are NOT stored here as the primary storage strategy.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- sessions
-- =========================================================

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    created_by TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT sessions_status_check
        CHECK (status IN ('active', 'archived', 'deleted'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at
    ON sessions (created_at DESC);

-- =========================================================
-- tasks
-- =========================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    prompt_text TEXT,
    result_data_json JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT tasks_status_check
        CHECK (status IN ('pending', 'running', 'succeeded', 'failed')),

    CONSTRAINT tasks_task_type_check
        CHECK (
            task_type IN (
                'docx_generate',
                'docx_rewrite',
                'pdf_summary',
                'pptx_generate',
                'data_analysis'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_tasks_session_id
    ON tasks (session_id);

CREATE INDEX IF NOT EXISTS idx_tasks_status
    ON tasks (status);

CREATE INDEX IF NOT EXISTS idx_tasks_task_type
    ON tasks (task_type);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at
    ON tasks (created_at DESC);

-- =========================================================
-- stored_files
-- =========================================================

CREATE TABLE IF NOT EXISTS stored_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,

    kind TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    title TEXT,
    original_filename TEXT,
    storage_backend TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    checksum_sha256 TEXT,
    size_bytes BIGINT,
    is_remote BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT stored_files_kind_check
        CHECK (
            kind IN (
                'uploaded_source',
                'generated_artifact',
                'derived_representation',
                'preview',
                'temporary'
            )
        ),

    CONSTRAINT stored_files_file_type_check
        CHECK (
            file_type IN (
                'docx',
                'pptx',
                'pdf',
                'txt',
                'md',
                'json',
                'csv',
                'xlsx',
                'png',
                'jpg',
                'jpeg',
                'html',
                'other'
            )
        ),

    CONSTRAINT stored_files_storage_backend_check
        CHECK (
            storage_backend IN (
                'local',
                'minio',
                's3_compatible',
                'remote_object_storage',
                'other'
            )
        ),

    CONSTRAINT stored_files_size_nonnegative_check
        CHECK (size_bytes IS NULL OR size_bytes >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stored_files_storage_backend_key
    ON stored_files (storage_backend, storage_key);

CREATE INDEX IF NOT EXISTS idx_stored_files_session_id
    ON stored_files (session_id);

CREATE INDEX IF NOT EXISTS idx_stored_files_task_id
    ON stored_files (task_id);

CREATE INDEX IF NOT EXISTS idx_stored_files_kind
    ON stored_files (kind);

CREATE INDEX IF NOT EXISTS idx_stored_files_file_type
    ON stored_files (file_type);

CREATE INDEX IF NOT EXISTS idx_stored_files_checksum
    ON stored_files (checksum_sha256);

CREATE INDEX IF NOT EXISTS idx_stored_files_created_at
    ON stored_files (created_at DESC);

-- =========================================================
-- documents
-- =========================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    current_file_id UUID REFERENCES stored_files(id) ON DELETE SET NULL,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT documents_status_check
        CHECK (status IN ('active', 'archived', 'deleted')),

    CONSTRAINT documents_document_type_check
        CHECK (
            document_type IN (
                'report',
                'proposal',
                'memo',
                'contract_draft',
                'summary',
                'other'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_documents_session_id
    ON documents (session_id);

CREATE INDEX IF NOT EXISTS idx_documents_current_file_id
    ON documents (current_file_id);

CREATE INDEX IF NOT EXISTS idx_documents_document_type
    ON documents (document_type);

-- =========================================================
-- document_versions
-- =========================================================

CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
    version_number INTEGER NOT NULL,
    created_from_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    parent_version_id UUID REFERENCES document_versions(id) ON DELETE SET NULL,
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT document_versions_version_number_positive_check
        CHECK (version_number > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_document_versions_doc_version
    ON document_versions (document_id, version_number);

CREATE INDEX IF NOT EXISTS idx_document_versions_document_id
    ON document_versions (document_id);

CREATE INDEX IF NOT EXISTS idx_document_versions_file_id
    ON document_versions (file_id);

CREATE INDEX IF NOT EXISTS idx_document_versions_task_id
    ON document_versions (created_from_task_id);

-- =========================================================
-- presentations
-- =========================================================

CREATE TABLE IF NOT EXISTS presentations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    current_file_id UUID REFERENCES stored_files(id) ON DELETE SET NULL,
    presentation_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT presentations_status_check
        CHECK (status IN ('active', 'archived', 'deleted')),

    CONSTRAINT presentations_presentation_type_check
        CHECK (
            presentation_type IN (
                'management_deck',
                'sales_pitch',
                'strategy_deck',
                'status_update',
                'other'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_presentations_session_id
    ON presentations (session_id);

CREATE INDEX IF NOT EXISTS idx_presentations_current_file_id
    ON presentations (current_file_id);

CREATE INDEX IF NOT EXISTS idx_presentations_type
    ON presentations (presentation_type);

-- =========================================================
-- presentation_versions
-- =========================================================

CREATE TABLE IF NOT EXISTS presentation_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presentation_id UUID NOT NULL REFERENCES presentations(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
    version_number INTEGER NOT NULL,
    created_from_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    parent_version_id UUID REFERENCES presentation_versions(id) ON DELETE SET NULL,
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT presentation_versions_version_number_positive_check
        CHECK (version_number > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_presentation_versions_presentation_version
    ON presentation_versions (presentation_id, version_number);

CREATE INDEX IF NOT EXISTS idx_presentation_versions_presentation_id
    ON presentation_versions (presentation_id);

CREATE INDEX IF NOT EXISTS idx_presentation_versions_file_id
    ON presentation_versions (file_id);

CREATE INDEX IF NOT EXISTS idx_presentation_versions_task_id
    ON presentation_versions (created_from_task_id);

-- =========================================================
-- artifacts
-- =========================================================

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
    artifact_type TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT artifacts_type_check
        CHECK (
            artifact_type IN (
                'generated_docx',
                'generated_pptx',
                'summary_report',
                'analysis_chart',
                'derived_text',
                'other'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_artifacts_task_id
    ON artifacts (task_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_session_id
    ON artifacts (session_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_file_id
    ON artifacts (file_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_type
    ON artifacts (artifact_type);

CREATE INDEX IF NOT EXISTS idx_artifacts_created_at
    ON artifacts (created_at DESC);

-- =========================================================
-- artifact_sources
-- =========================================================

CREATE TABLE IF NOT EXISTS artifact_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES stored_files(id) ON DELETE SET NULL,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    source_presentation_id UUID REFERENCES presentations(id) ON DELETE SET NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT artifact_sources_role_check
        CHECK (
            role IN (
                'primary_source',
                'reference_source',
                'template_source',
                'background_material'
            )
        ),

    CONSTRAINT artifact_sources_at_least_one_source_check
        CHECK (
            source_file_id IS NOT NULL
            OR source_document_id IS NOT NULL
            OR source_presentation_id IS NOT NULL
        )
);

CREATE INDEX IF NOT EXISTS idx_artifact_sources_artifact_id
    ON artifact_sources (artifact_id);

CREATE INDEX IF NOT EXISTS idx_artifact_sources_source_file_id
    ON artifact_sources (source_file_id);

CREATE INDEX IF NOT EXISTS idx_artifact_sources_source_document_id
    ON artifact_sources (source_document_id);

CREATE INDEX IF NOT EXISTS idx_artifact_sources_source_presentation_id
    ON artifact_sources (source_presentation_id);

-- =========================================================
-- derived_contents
-- =========================================================

CREATE TABLE IF NOT EXISTS derived_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES stored_files(id) ON DELETE CASCADE,
    content_kind TEXT NOT NULL,
    text_content TEXT,
    structured_json JSONB,
    outline_json JSONB,
    language TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT derived_contents_content_kind_check
        CHECK (
            content_kind IN (
                'extracted_text',
                'normalized_structure',
                'slide_outline',
                'document_sections',
                'table_data',
                'other'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_derived_contents_file_id
    ON derived_contents (file_id);

CREATE INDEX IF NOT EXISTS idx_derived_contents_kind
    ON derived_contents (content_kind);

-- =========================================================
-- llm_runs
-- =========================================================

CREATE TABLE IF NOT EXISTS llm_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    purpose TEXT NOT NULL,
    input_ref TEXT,
    output_ref TEXT,
    usage_json JSONB,
    status TEXT NOT NULL DEFAULT 'succeeded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT llm_runs_provider_check
        CHECK (
            provider IN (
                'gigachat',
                'openai',
                'qwen',
                'noop',
                'other'
            )
        ),

    CONSTRAINT llm_runs_purpose_check
        CHECK (
            purpose IN (
                'classification',
                'rewrite',
                'summary',
                'outline_generation',
                'slide_content_generation',
                'other'
            )
        ),

    CONSTRAINT llm_runs_status_check
        CHECK (
            status IN (
                'pending',
                'running',
                'succeeded',
                'failed'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_llm_runs_task_id
    ON llm_runs (task_id);

CREATE INDEX IF NOT EXISTS idx_llm_runs_provider
    ON llm_runs (provider);

CREATE INDEX IF NOT EXISTS idx_llm_runs_model
    ON llm_runs (model);

CREATE INDEX IF NOT EXISTS idx_llm_runs_purpose
    ON llm_runs (purpose);

CREATE INDEX IF NOT EXISTS idx_llm_runs_created_at
    ON llm_runs (created_at DESC);

-- =========================================================
-- execution_runs
-- =========================================================

CREATE TABLE IF NOT EXISTS execution_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    engine_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    stdout_text TEXT,
    stderr_text TEXT,
    result_json JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    CONSTRAINT execution_runs_engine_type_check
        CHECK (
            engine_type IN (
                'python_subprocess',
                'python_kernel',
                'other'
            )
        ),

    CONSTRAINT execution_runs_status_check
        CHECK (
            status IN (
                'pending',
                'running',
                'succeeded',
                'failed'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_execution_runs_task_id
    ON execution_runs (task_id);

CREATE INDEX IF NOT EXISTS idx_execution_runs_engine_type
    ON execution_runs (engine_type);

CREATE INDEX IF NOT EXISTS idx_execution_runs_status
    ON execution_runs (status);

-- =========================================================
-- optional trigger helper for updated_at
-- =========================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sessions_updated_at ON sessions;
CREATE TRIGGER trg_sessions_updated_at
BEFORE UPDATE ON sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_stored_files_updated_at ON stored_files;
CREATE TRIGGER trg_stored_files_updated_at
BEFORE UPDATE ON stored_files
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;
CREATE TRIGGER trg_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_presentations_updated_at ON presentations;
CREATE TRIGGER trg_presentations_updated_at
BEFORE UPDATE ON presentations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_derived_contents_updated_at ON derived_contents;
CREATE TRIGGER trg_derived_contents_updated_at
BEFORE UPDATE ON derived_contents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;

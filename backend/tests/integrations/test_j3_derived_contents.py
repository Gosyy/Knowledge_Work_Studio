from datetime import datetime, timezone
from pathlib import Path

from backend.app.domain import DerivedContent
from backend.app.repositories.sqlite import SqliteDerivedContentRepository


def test_j3_sqlite_derived_content_repository_persists_extracted_text(tmp_path: Path) -> None:
    repository = SqliteDerivedContentRepository(str(tmp_path / "derived.sqlite3"))
    derived_content = DerivedContent(
        id="dcon_1",
        file_id="file_1",
        content_kind="extracted_text",
        text_content="cached source text",
        structured_json={"kind": "text"},
        outline_json=None,
        language="en",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    repository.create(derived_content)

    assert repository.list_by_file("file_1") == [derived_content]

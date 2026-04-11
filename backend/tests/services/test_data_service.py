from backend.app.core.config import Settings
from backend.app.services.data_service import DataAnalysisService


def test_data_service_runs_kernel_backed_csv_analysis() -> None:
    service = DataAnalysisService.from_settings(Settings(kernel_server_auth_token=""))

    result = service.analyze_tabular_content(
        content="col_a,col_b\n1,2\n3,4\n5,6",
        file_type="csv",
    )

    assert "Rows: 3" in result.summary_text
    assert "Columns: 2" in result.summary_text
    assert "Numeric cells: 6" in result.summary_text
    assert result.artifact_content.decode("utf-8") == result.summary_text

import asyncio

from backend.app.core.config import Settings
from backend.app.domain import TaskType
from backend.app.orchestrator import OrchestratorIntegrationSurface
from backend.app.runtime.browser.interface import BrowserRuntimeInterface
from backend.app.runtime.browser.utils import BrowserRuntimeConfig
from backend.app.runtime.browser.browser_supervisor import BrowserSupervisor
from backend.app.runtime.browser.playwright_controller import PlaywrightController
from backend.app.runtime.kernel.interface import KernelRuntimeInterface
from backend.app.services.docx_service import DocxService, DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfService, PdfServiceEntrypoint


def test_orchestrator_integration_surface_routes_docx_and_pdf_preview() -> None:
    kernel = KernelRuntimeInterface.from_settings(Settings(kernel_server_auth_token=""))

    browser_supervisor = BrowserSupervisor(
        config=BrowserRuntimeConfig(
            enabled=False,
            preferred_backend="playwright",
            allow_unsafe_features=False,
            max_restart_attempts=1,
        ),
        controller=PlaywrightController(
            config=BrowserRuntimeConfig(
                enabled=False,
                preferred_backend="playwright",
                allow_unsafe_features=False,
                max_restart_attempts=1,
            )
        ),
    )
    browser = BrowserRuntimeInterface(supervisor=browser_supervisor)

    surface = OrchestratorIntegrationSurface(
        docx=DocxServiceEntrypoint(service=DocxService()),
        pdf=PdfServiceEntrypoint(service=PdfService()),
        kernel=kernel,
        browser=browser,
    )

    docx_output = surface.preview_task_execution(TaskType.DOCX_EDIT, "draft outline")
    pdf_output = surface.preview_task_execution(
        TaskType.PDF_SUMMARY,
        "Alpha point. Beta point. Gamma point.",
    )

    assert docx_output == "final outline"
    assert pdf_output == "Alpha point. Beta point."


def test_runtime_interfaces_are_callable_for_internal_wiring() -> None:
    kernel = KernelRuntimeInterface.from_settings(Settings(kernel_server_auth_token=""))
    session_id = kernel.create_session()

    assert kernel.execute(session_id=session_id, code="1+1") == "accepted"
    assert kernel.active_sessions() == 1
    assert kernel.shutdown_session(session_id) is True

    browser = BrowserRuntimeInterface.from_env()
    asyncio.run(browser.start())
    assert asyncio.run(browser.ensure_healthy()) in {True, False}
    asyncio.run(browser.stop())

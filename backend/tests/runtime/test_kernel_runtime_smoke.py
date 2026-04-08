from backend.app.core.config import Settings
from backend.app.runtime.kernel import KernelInspector, build_kernel_bootstrap


def test_kernel_runtime_has_no_import_time_side_effects() -> None:
    bootstrap = build_kernel_bootstrap(Settings(kernel_server_auth_token=""))

    assert bootstrap.runtime.active_session_count() == 0
    assert bootstrap.server.health() == {"active_sessions": 0}


def test_kernel_runtime_session_execute_shutdown_flow() -> None:
    bootstrap = build_kernel_bootstrap(Settings(kernel_server_auth_token="secret-token"))
    session = bootstrap.server.create_session(auth_token="secret-token")

    result = bootstrap.server.execute(
        session_id=session.id,
        code="print('hello')",
        timeout_seconds=10,
        auth_token="secret-token",
    )

    inspector = KernelInspector(bootstrap.runtime)

    assert result.session_id == session.id
    assert result.status == "accepted"
    assert inspector.snapshot_dict() == {"active_sessions": 1}

    assert bootstrap.server.shutdown_session(session_id=session.id, auth_token="secret-token") is True
    assert inspector.snapshot_dict() == {"active_sessions": 0}

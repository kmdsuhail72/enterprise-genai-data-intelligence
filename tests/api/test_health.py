"""Tests for liveness, readiness, and safe API error responses."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from enterprise_ai.api.routes import health
from enterprise_ai.main import create_app


class _Connection:
    """Minimal async connection fake used by readiness tests."""

    async def __aenter__(self) -> "_Connection":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        assert str(statement) == "SELECT 1"


class _Engine:
    """Minimal engine fake exposing the async context manager contract."""

    def connect(self) -> _Connection:
        return _Connection()


class _BrokenConnection:
    """Connection fake that reports a database failure on query execution."""

    async def __aenter__(self) -> "_BrokenConnection":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        raise SQLAlchemyError("database-password-must-not-leak")


class _BrokenEngine:
    """Engine fake that fails its readiness query."""

    def connect(self) -> _BrokenConnection:
        return _BrokenConnection()


class _RefusedConnection:
    """Connection fake that models a refused TCP connection."""

    async def __aenter__(self) -> "_RefusedConnection":
        raise ConnectionRefusedError("database connection refused")

    async def __aexit__(self, *_args: object) -> None:
        return None


class _RefusedEngine:
    """Engine fake that cannot establish a network connection."""

    def connect(self) -> _RefusedConnection:
        return _RefusedConnection()


def test_health_is_independent_of_database(monkeypatch) -> None:
    """Liveness returns healthy without opening a database connection."""

    def fail_if_called() -> _Engine:
        raise AssertionError("liveness must not connect to the database")

    monkeypatch.setattr(health, "get_engine", fail_if_called)

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"]
    assert response.headers["X-Request-ID"]


def test_readiness_when_database_is_connected(monkeypatch) -> None:
    """Readiness returns HTTP 200 when its database probe succeeds."""
    monkeypatch.setattr(health, "get_engine", _Engine)

    with TestClient(create_app()) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"] == {"database": "connected"}


def test_readiness_when_database_is_unavailable(monkeypatch) -> None:
    """Readiness reports 503 without leaking the underlying DB exception."""
    monkeypatch.setattr(health, "get_engine", _BrokenEngine)

    with TestClient(create_app()) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"] == {"database": "unavailable"}
    assert "database-password-must-not-leak" not in response.text


def test_readiness_when_database_connection_is_refused(monkeypatch) -> None:
    """Map low-level connection-refused errors to HTTP 503."""
    monkeypatch.setattr(health, "get_engine", _RefusedEngine)

    with TestClient(create_app()) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "database connection refused" not in response.text


def test_validation_error_is_consistent_and_does_not_echo_input() -> None:
    """Validation errors have a stable envelope and omit submitted values."""
    app = create_app()

    @app.get("/test/{item_id}")
    async def validate_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    with TestClient(app) as client:
        response = client.get("/test/sensitive-input")

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "validation_error"
    assert "sensitive-input" not in response.text


def test_unhandled_error_is_safe_and_has_request_id() -> None:
    """Unhandled errors use the safe response contract and correlation header."""
    app = create_app()

    @app.get("/test/failure")
    async def fail() -> None:
        raise RuntimeError("internal-database-password")

    with TestClient(app, raise_server_exceptions=False) as client:
        request_id = "96a344f2-4c79-4743-8cfb-437854116c32"
        response = client.get("/test/failure", headers={"X-Request-ID": request_id})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id
    assert "internal-database-password" not in response.text


def test_malformed_request_id_is_replaced() -> None:
    """Malformed request IDs are replaced with a generated UUID."""
    with TestClient(create_app()) as client:
        response = client.get("/health", headers={"X-Request-ID": "not-a-uuid"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "not-a-uuid"

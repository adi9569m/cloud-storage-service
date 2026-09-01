"""Integration tests for Request Tracing, Security Headers, and Rate Limiting middlewares."""

import pytest
from fastapi.testclient import TestClient
from app.core.rate_limiter import limiter
from app.main import app


@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear rate limiter cache before each test."""
    limiter.reset()
    yield
    limiter.reset()


def test_request_id_and_security_headers():
    """Test that all API responses include X-Request-ID and security headers."""
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200

        # Request Tracing
        assert "x-request-id" in resp.headers
        assert "x-process-time" in resp.headers

        # Security Headers
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("x-xss-protection") == "1; mode=block"


def test_custom_request_id_forwarding():
    """Test that client-supplied X-Request-ID header is preserved."""
    with TestClient(app) as client:
        custom_id = "trace-custom-uuid-12345"
        resp = client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.status_code == 200
        assert resp.headers["x-request-id"] == custom_id


def test_rate_limiter_allows_under_threshold():
    """Test that rate limiter allows requests within threshold."""
    key = "127.0.0.1:/test"
    for _ in range(5):
        assert limiter.is_allowed(key, max_requests=5, window_seconds=60) is True

    # 6th request exceeds limit
    assert limiter.is_allowed(key, max_requests=5, window_seconds=60) is False

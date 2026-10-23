"""Shared test fixtures.

The production HTTP middleware in ``titan_utils.api`` enforces 60 requests per
minute per client IP. TestClient traffic all arrives from one synthetic IP, so
a whole-suite run on a fast machine can trip the limiter and fail unrelated
tests with 429s. This fixture disarms the *instance* used by the live app for
the duration of each test; the limiter's contract itself is covered with its
own deterministic fake-clock test (``test_rate_limit_is_60_per_minute_per_ip_in_memory``)
which constructs a private ``InMemoryRateLimiter`` and is unaffected here.
Production behaviour is unchanged: the middleware still allows 60 req/min/IP.
"""

import pytest


@pytest.fixture(autouse=True)
def _disarm_rate_limiter(monkeypatch):
    from titan_utils.api import RATE_LIMITER

    monkeypatch.setattr(RATE_LIMITER, "allow", lambda ip, *, now=None: True)
    yield

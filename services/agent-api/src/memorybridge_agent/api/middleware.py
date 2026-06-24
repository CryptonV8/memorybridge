import uuid
import time
import logging
from collections import defaultdict, deque
from typing import DefaultDict, Deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Fail closed behavior: log the exception securely, but return generic error to client
            logger.error(f"Internal server error: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "correlation_id": getattr(request.state, "correlation_id", "unknown")
                }
            )


# ── In-memory rate limiter ────────────────────────────────────────────────────
# WARNING: This implementation is DEMO-ONLY.
# It uses per-process memory. In a multi-instance Cloud Run deployment each
# replica has independent state, so a determined client could exceed limits by
# cycling between instances. Replace with a shared Redis-backed store (e.g.
# slowapi + Redis) before production deployment.
#
# Rate limit key = f"{actor_id}:{client_ip}"
# actor_id is extracted from the bearer token by the auth dependency — it is
# server-validated and cannot be spoofed by the client.
_rate_limit_store: DefaultDict[str, Deque[float]] = defaultdict(deque)

# Routes that mutate state and require rate limiting
RATE_LIMITED_ROUTES = {
    # (method, path_prefix): (max_requests, window_seconds)
    ("POST", "/api/routines/interpret"):    (10, 60),
    ("POST", "/api/users/"):               (10, 60),   # /help and /contact
    ("POST", "/api/routines/"):            (20, 60),   # /approve, /reject, /status
    ("PATCH", "/api/routines/"):           (20, 60),
}


def _get_rate_limit(method: str, path: str):
    """Return (max_requests, window_seconds) for this route, or None if not rate-limited."""
    for (m, prefix), limits in RATE_LIMITED_ROUTES.items():
        if method == m and path.startswith(prefix):
            return limits
    return None


def _extract_actor_id(request: Request) -> str:
    """Extract actor_id from the validated token stored in request.state, or fall back to IP."""
    # The auth dependency stores actor_id on request.state after token validation
    actor_id = getattr(request.state, "actor_id", None)
    if actor_id:
        return str(actor_id)
    # Fallback: use Authorization header hash (not the token value itself)
    auth = request.headers.get("Authorization", "")
    return f"token:{hash(auth) & 0xFFFFFF}"


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window in-memory rate limiter.

    Applied only to state-changing API endpoints (see RATE_LIMITED_ROUTES).
    Key = actor_id:IP for better granularity than IP alone.
    """
    async def dispatch(self, request: Request, call_next):
        limits = _get_rate_limit(request.method, request.url.path)
        if limits is None:
            # Not a rate-limited route — pass through
            return await call_next(request)

        max_requests, window_seconds = limits
        actor_id = _extract_actor_id(request)
        client_ip = _get_client_ip(request)
        key = f"{actor_id}:{client_ip}"
        now = time.monotonic()
        window_start = now - window_seconds

        bucket = _rate_limit_store[key]
        # Evict timestamps outside the sliding window
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= max_requests:
            logger.warning(
                f"Rate limit exceeded: key={key!r} path={request.url.path!r} "
                f"count={len(bucket)}/{max_requests} window={window_seconds}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please wait a moment before trying again.",
                    "retry_after_seconds": window_seconds,
                },
                headers={"Retry-After": str(window_seconds)},
            )

        bucket.append(now)
        return await call_next(request)

import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "anonymous"
        window, now = 60, time.time()
        q = self.hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse({"detail": "Rate limit exceeded. Please retry shortly."}, status_code=429)
        q.append(now)
        return await call_next(request)

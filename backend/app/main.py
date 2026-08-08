import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.database.session import init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.api import auth, agents, platform, demo

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("trust-safety")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-agent Trust & Safety platform: fraud, review manipulation and counterfeit defense.",
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(platform.router)
app.include_router(demo.router)

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database ready. DEMO_MODE=%s", settings.DEMO_MODE)

@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse({"error": exc.detail, "status_code": exc.status_code}, status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse({"error": "Validation failed", "details": exc.errors()[:5]}, status_code=422)

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse({"error": "An internal error occurred. Please contact your administrator."},
                        status_code=500)

@app.get("/")
def root():
    return {"name": settings.APP_NAME, "version": settings.VERSION, "docs": "/docs",
            "demo_mode": settings.DEMO_MODE}

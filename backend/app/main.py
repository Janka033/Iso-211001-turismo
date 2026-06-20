from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.generation.router import router as generation_router
from app.modules.inventory.router import router as inventory_router
from app.modules.onboarding.router import router as onboarding_router

settings = get_settings()

# Rate limiting por IP: protege /generation (cada llamada cuesta cuota de IA) y
# /auth contra abuso/fuerza bruta. Ajustable; en multi-instancia conviene Redis.
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])

app = FastAPI(title="ColAdventure API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS: orígenes restringidos por env (CORS_ORIGINS), métodos/headers acotados.
# Nunca usar "*" junto con allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(generation_router)
app.include_router(inventory_router)
app.include_router(onboarding_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

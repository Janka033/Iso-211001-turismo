from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ancla el .env a backend/ para que la carga no dependa del directorio de
# trabajo (uvicorn corre desde backend/, los seeds desde la raíz del repo).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: str = ""
    # service_role: SOLO seed + provisioning. Salta RLS — no usar en el flujo normal.
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""
    supabase_jwt_audience: str = "authenticated"

    # IA
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # gemini-embedding-001 emite 3072 dims por defecto; el provider pide 768
    # (output_dimensionality) para calzar con vector(768) de knowledge_chunks.
    gemini_embedding_model: str = "gemini-embedding-001"
    # Timeout (ms) de las llamadas a Gemini. Evita que un upstream colgado
    # cuelgue la request indefinidamente. 120s: la generación de documentos
    # con thinking puede superar los 60s (medido en el ensayo E2E; a 60s los
    # turnos largos morían en timeout → 502).
    gemini_timeout_ms: int = 120000

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

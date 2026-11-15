"""
Groundy API — configuracion por entorno.
Nada sensible se escribe aqui: todo llega por variables de entorno o por un
archivo .env en la RAIZ del proyecto (no versionado).
"""
import os
import sys

# Raiz del proyecto (un nivel arriba de api/)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_ROOT, ".env")

# Cargar .env de la raiz de forma explicita (no depende del directorio actual).
# Si existe .env pero python-dotenv no esta instalado, avisar claramente.
_DOTENV_MSG = None
if os.path.isfile(_ENV_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=_ENV_PATH, override=False)
    except Exception:
        _DOTENV_MSG = ("[config] Hay un .env en la raiz pero python-dotenv no esta "
                       "instalado: sus variables NO se cargaron. Instala con "
                       "'pip install python-dotenv' o exporta las variables con $env: / export.")
        print(_DOTENV_MSG, file=sys.stderr)


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return int(default)


# --- Google Earth Engine ---
GEE_KEY_PATH = os.environ.get("GEE_KEY_PATH", os.path.join("secrets", "gee_key.json"))

# --- Supabase (la service_role vive SOLO aqui, en el servidor) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
CACHE_TABLE = os.environ.get("CACHE_TABLE", "analysis_cache")

# --- Caracteristicas de la cache ---
CACHE_TTL_DAYS = _int("CACHE_TTL_DAYS", 30)
CACHE_COORD_DECIMALS = _int("CACHE_COORD_DECIMALS", 4)
PROC_VERSION = os.environ.get("PROC_VERSION", "1.2")

DATA_SIGNATURE = os.environ.get(
    "DATA_SIGNATURE",
    "POWER:2001-2025;MOD13Q1;MOD11A2;SMAP008:2020-2025;IMERGv07:2001-2025;"
    "S2SR_HARM:2023-2025;SRTM",
)

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

CACHE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


def cache_status():
    """Diagnostico SIN exponer secretos: dice que falta para activar la cache."""
    faltan = []
    if not SUPABASE_URL:
        faltan.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_KEY:
        faltan.append("SUPABASE_SERVICE_KEY")
    return {
        "cache_enabled": CACHE_ENABLED,
        "supabase_url_set": bool(SUPABASE_URL),
        "service_key_set": bool(SUPABASE_SERVICE_KEY),
        "service_key_len": len(SUPABASE_SERVICE_KEY),   # longitud, NO el valor
        "table": CACHE_TABLE,
        "faltan": faltan,
        "env_file_detectado": os.path.isfile(_ENV_PATH),
        "dotenv_aviso": _DOTENV_MSG,
    }

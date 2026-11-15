"""
Groundy — diagnostico de CACHE (corre en tu PC). NO toca GEE.
Verifica configuracion y hace un put+get+borrado REAL contra Supabase.

    $env:SUPABASE_URL="https://svaksbawrhndxyzugjjr.supabase.co"
    $env:SUPABASE_SERVICE_KEY="<service_role>"
    python api/diag_cache.py

No imprime la llave; solo si esta presente y su longitud.
"""
import os, sys, json, logging
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT); sys.path.insert(0, _ROOT)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from api import config, cache

print("=== 1. Configuracion (sin exponer secretos) ===")
print(json.dumps(config.cache_status(), indent=2, ensure_ascii=False))

if not config.CACHE_ENABLED:
    print("\n>> CACHE DESACTIVADA. Falta:", config.cache_status()["faltan"])
    print("   En PowerShell usa  $env:VAR=\"valor\"  (NO 'set'), o crea un .env en la raiz.")
    sys.exit(1)

print("\n=== 2. Selftest put -> get -> delete (REAL contra Supabase) ===")
res = cache.selftest()
print(json.dumps(res, indent=2, ensure_ascii=False))
print("\n>> RESULTADO:", "CACHE OK" if res.get("ok") else "FALLA EN: " + str(res.get("paso")))
sys.exit(0 if res.get("ok") else 2)

"""
Groundy — prueba de CACHE de punta a punta (corre en tu PC, con GEE y Supabase).

Requiere en el entorno:
    set GEE_KEY_PATH=secrets/gee_key.json
    set SUPABASE_URL=https://svaksbawrhndxyzugjjr.supabase.co
    set SUPABASE_SERVICE_KEY=<tu service_role>
    python api/probar_cache.py

Esperado:
    intento 1 -> fuente=vivo  (lento, consulta GEE)
    intento 2 -> fuente=cache (rapido, desde Supabase)
Si cache=False, falta configurar SUPABASE_URL/SERVICE_KEY (el API igual responde en vivo).
"""
import os, sys, time
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT); sys.path.insert(0, _ROOT); sys.path.insert(0, os.path.join(_ROOT, "src"))

from fastapi.testclient import TestClient
from api.main import app
from api import config

def medir(c, ruta, body, etiqueta):
    t = time.time(); r = c.post(ruta, json=body); dt = time.time() - t
    j = r.json(); m = j.get("meta", {})
    print(f"  {etiqueta}: HTTP {r.status_code}  fuente={m.get('fuente')}  {dt:.1f}s"
          f"  generado={m.get('generado_en')}  entregado={m.get('entregado_en')}")

with TestClient(app) as c:
    print("cache activa:", config.CACHE_ENABLED, "| proc_version:", config.PROC_VERSION)
    print("\n>> PUNTO (Pasto) x2  -> 1=vivo, 2=cache")
    medir(c, "/analizar/punto", {"lat": 1.21, "lon": -77.28}, "intento 1")
    medir(c, "/analizar/punto", {"lat": 1.21, "lon": -77.28}, "intento 2")
    print("\n>> AREA (finca rural) x2  -> 1=vivo, 2=cache")
    coords = [[-77.30,1.15],[-77.28,1.15],[-77.28,1.17],[-77.30,1.17]]
    medir(c, "/analizar/area", {"coords": coords}, "area 1")
    medir(c, "/analizar/area", {"coords": coords}, "area 2")
    print("\n>> Coordenada distinta -> debe volver a vivo")
    medir(c, "/analizar/punto", {"lat": 1.095, "lon": -77.35}, "nuevo punto")

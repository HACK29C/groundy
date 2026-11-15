"""
Prueba el API en tu maquina (Windows), donde GEE si autentica.
No levanta servidor: llama la app en proceso con TestClient.

    set GEE_KEY_PATH=secrets/gee_key.json
    python api/probar_local.py
"""
import os, sys, json
_ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)
sys.path.insert(0,_ROOT)
sys.path.insert(0,os.path.join(_ROOT,"src"))
os.environ.setdefault("GEE_KEY_PATH", os.path.join("secrets", "gee_key.json"))

from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as c:
    print(">> /salud:", c.get("/salud").json())
    d = c.get("/cultivos").json()
    print(">> /cultivos:", d["total"], "cultivos")

    print("\n>> POST /analizar/punto  (Pasto 1.21, -77.28) ...")
    r = c.post("/analizar/punto", json={"lat": 1.21, "lon": -77.28})
    print("   HTTP", r.status_code)
    if r.status_code == 200:
        j = r.json()
        print("   clima:", j["climate"])
        print("   confianza:", j["confidence"], "| sitio hermano:", j["sister_site"])
        print("   mejor rotacion:", j["best_rotation"])
        print("   top cultivos:", [x["id"] for x in j["crops_top"]])
    else:
        print("   ", r.json())

    zonas = {
        "URBANA (casco de Pasto, NDVI debe ser BAJO)":
            [[-77.29,1.20],[-77.27,1.20],[-77.27,1.22],[-77.29,1.22]],
        "RURAL (campo al sur de Pasto, NDVI debe ser ALTO)":
            [[-77.30,1.15],[-77.28,1.15],[-77.28,1.17],[-77.30,1.17]],
    }
    for etiqueta, coords in zonas.items():
        print("\n>> POST /analizar/area  ->", etiqueta)
        r = c.post("/analizar/area", json={"coords": coords})
        print("   HTTP", r.status_code)
        if r.status_code == 200:
            j = r.json()
            print("   area_ha:", j["area_ha"])
            s2 = j["vegetacion"]["ndvi_sentinel2_10m"]
            mo = j["vegetacion"]["ndvi_modis_250m"]
            print("   NDVI Sentinel-2 10m:", s2)
            print("   NDVI MODIS 250m   :", mo)
        else:
            print("   ", r.json())

"""Prueba del motor por punto (Camino B) con la cuenta de servicio.
Ejecutar desde la raíz del proyecto:  .venv\\Scripts\\python.exe test_point.py
"""
import sys, json
sys.path.insert(0, "src")
import point_engine as pe

KEY = r"C:\Users\jhona\develop\shagra-ml\secrets\gee_key.json"

pe.init_ee(KEY)
print("Earth Engine con cuenta de servicio: OK")

# Un punto NUEVO, que no es ninguno de los 12 (Pasto, Narino)
r = pe.analizar_punto(1.21, -77.28)
print(json.dumps({k: r[k] for k in ["lat", "lon", "elev_m", "climate", "confidence", "sister_site",
                                     "potato", "best_rotation"]}, ensure_ascii=False, indent=2))
print("NDVI mensual:", r["vegetation_monthly"]["ndvi"])
print("Humedad raiz mensual:", r["vegetation_monthly"]["sm_root"])

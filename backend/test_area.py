import sys, json
sys.path.insert(0, "src")
import point_engine as pe
pe.init_ee(r"C:\Users\jhona\develop\shagra-ml\secrets\gee_key.json")
# una finca de ejemplo (poligono pequeno cerca de Pasto)
finca = [[-77.29, 1.20], [-77.27, 1.20], [-77.27, 1.22], [-77.29, 1.22]]
r = pe.analizar_area(finca)
print(json.dumps({k: r[k] for k in ["centroide", "area_ha", "terreno_dentro_de_la_finca",
                                     "vegetacion", "clima_regional", "aptitud", "mejor_rotacion",
                                     "confianza", "resolucion"]}, ensure_ascii=False, indent=2))

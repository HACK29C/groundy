# Contrato de API — Groundy

Versión 1.0 · Camino B (motor en vivo, global)

Este documento es el acuerdo entre el **frontend** (demo / mapa) y el
**backend** (motor). Mientras exista y se respete, ambos equipos pueden
avanzar en paralelo sin bloquearse.

---

## 1. Qué es

Una sola puerta HTTP (FastAPI) sobre el motor `point_engine`. El cliente
solo habla con esta API; **Google Earth Engine, NASA POWER y Supabase
quedan detrás** y nunca se consultan desde el navegador.

- **Base URL (local, desarrollo):** `http://localhost:8000`
- **Base URL (producción):** por definir al montar (Cloud Run / Supabase).
- **Autenticación:** ninguna por ahora (v1). 
- **CORS:** abierto (`*`) para que el demo, en otro dominio, pueda llamar.
- **Formato:** JSON en entrada y salida. Codificación UTF-8.
- **Bloque `meta`:** toda respuesta de análisis incluye un `meta` al nivel
  superior con `fuente` ("cache"|"vivo"), `proc_version`, `generado_en`
  (cuándo se calculó) y `entregado_en` (cuándo se respondió). Ver `docs/CACHE.md`.
- **Documentación viva:** al correr la API, `GET /docs` (Swagger) muestra
  y permite probar todos los endpoints.

---

## 2. Cómo correr (desarrollo)

```bash
# desde la raíz del proyecto
set GEE_KEY_PATH=secrets\gee_key.json        # Windows
# export GEE_KEY_PATH=secrets/gee_key.json   # Linux/Mac
uvicorn api.main:app --reload --port 8000
```

La llave de GEE se lee de la variable de entorno `GEE_KEY_PATH`; **nunca
va escrita en el código ni se sube al repo** (está en `secrets/`, ignorada
por git).

---

## 3. Endpoints

### 3.1 `GET /salud`
Comprueba que la API está viva y si GEE quedó inicializado.

**Respuesta 200:**
```json
{ "estado": "ok", "gee": true, "cultivos": 42, "cache": true, "proc_version": "1.1" }
```
- `gee: false` significa que la API está arriba pero GEE no autenticó
  (llave ausente o sin red). Los endpoints de análisis responderán 503.

---

### 3.2 `GET /cultivos`
Lista de cultivos disponibles. Úsalo para llenar menús/selectores.

**Respuesta 200:**
```json
{
  "total": 42,
  "cultivos": [
    { "id": "papa", "name_es": "Papa", "role": "tuberculo",
      "family": "Solanaceae", "is_legume": false },
    { "id": "cebada", "name_es": "Cebada", "role": "cereal",
      "family": "Poaceae", "is_legume": false }
  ]
}
```
El `id` es la clave estable; `name_es` es la etiqueta para mostrar.

---

### 3.3 `POST /analizar/punto`
Caracteriza un **punto** (lat/lon): clima, vegetación, aptitud,
rotaciones y nivel de confianza.

**Cuerpo:**
```json
{ "lat": 1.21, "lon": -77.28 }
```
- `lat`: −90 a 90. `lon`: −180 a 180. Ambos obligatorios.

**Respuesta 200 (estructura; valores de ejemplo reales de Pasto):**
```json
{
  "lat": 1.21, "lon": -77.28, "elev_m": 2600,
  "climate": {
    "tmean_c": 12.4,
    "rain_mm_yr": 1105,            // NASA POWER
    "et0_mm_yr": 1180,
    "aridity": 0.94,              // lluvia / ET0
    "rain_imerg_mm_yr": 2171,     // GPM IMERG (satelital)
    "rain_range_mm": [1105, 2171] // rango entre fuentes (honestidad)
  },
  "vegetation_monthly": {          // 12 valores (ene..dic) por capa
    "ndvi": [...], "evi": [...], "lst_c": [...],
    "sm_surf": [...], "sm_root": [...], "rain_imerg": [...]
  },
  "vegetation_status": {           // "ok" | "sin_datos" | "error" por capa
    "ndvi": "ok", "sm_root": "ok", ...
  },
  "confidence": "alta",           // alta | media | baja
  "sister_site": "Ipiales",       // sitio de referencia más parecido
  "potato": { "suit": 0.78, "reliability": 0.9,
              "limiting": "...", "best_month_es": "..." },
  "crops_top": [                   // mejores 6 cultivos para el sitio
    { "id": "papa", "suit": 0.78, "best_month": "...", "limits": "..." }
  ],
  "rotations": [
    { "name": "A. Papa continua", "score": 61.2,
      "seq": ["papa","papa","papa"], "notes": "..." }
  ],
  "best_rotation": "C. Papa - oca - quinua",
  "provenance": { "climate": "NASA POWER ...", "ndvi_evi": "MODIS ...", ... }
}
```

**Campos clave para el front:**
- `climate.rain_range_mm`: mostrar como rango, no un número único.
- `vegetation_monthly.*`: 12 puntos → gráficas mensuales.
- `confidence`: pintar la bandera (alta/media/baja). **No presentar los
  puntajes como receta exacta**, sino como orientación con su confianza.
- `rotations` / `best_rotation`: tabla ordenada de mayor a menor `score`.

---

### 3.4 `POST /analizar/area`
Caracteriza una **finca** (polígono): separa lo que varía *dentro* del
predio (relieve/pendiente 30 m, NDVI) de lo *regional* por resolución
gruesa (humedad SMAP ~9 km, clima POWER ~50 km).

**Cuerpo:**
```json
{ "coords": [[-77.29,1.20],[-77.27,1.20],[-77.27,1.22],[-77.29,1.22]] }
```
- `coords`: lista de vértices `[lon, lat]`, **mínimo 3**. Orden del
  polígono (no hace falta cerrar: el último no tiene que repetir el primero).

**Respuesta 200 (estructura; ejemplo real finca Pasto):**
```json
{
  "centroide": { "lat": 1.21, "lon": -77.28 },
  "area_ha": 487.3,
  "terreno_dentro_de_la_finca": {
    "elevacion_m": { "media": 2589, "desv": 41, "min": 2515, "max": 2663 },
    "pendiente_grados": { "media": 7.8, "desv": 5.1, "min": 0, "max": 33 }
  },
  "vegetacion": {
    "ndvi_modis_250m":   { "media": 0.62, "desv": 0.062, ... },
    "ndvi_sentinel2_10m":{ "media": 0.58, "desv": 0.156, ... }  // detalle fino
  },
  "clima_regional": { ... },                 // igual que climate del punto
  "humedad_suelo_regional_mensual": [...],    // 12 valores SMAP
  "aptitud": { "suit": 0.78, ... },
  "mejor_rotacion": "C. Papa - oca - quinua",
  "rotaciones": [ ... ],
  "confianza": "alta",
  "resolucion": {
    "relieve_pendiente": "SRTM 30m — varía dentro de la finca",
    "ndvi": "MODIS 250m — grueso (Sentinel-2 10m para detalle fino)",
    "humedad_suelo": "SMAP ~9km — valor regional",
    "clima": "NASA POWER ~50km — valor regional"
  }
}
```

**Lectura honesta para el front:** `terreno_*` y `ndvi_sentinel2_10m`
describen variación REAL dentro de la finca; `clima_regional` y
`humedad_suelo_regional` son valores de la zona, no de cada metro. El
bloque `resolucion` explica qué es qué — conviene mostrarlo.

---

## 4. Errores

| Código | Cuándo | Cuerpo |
|---|---|---|
| **422** | Entrada inválida (lat/lon fuera de rango, polígono con <3 vértices) | `{ "detail": [...] }` (validación de FastAPI) |
| **503** | GEE no inicializado (sin llave o sin red) | `{ "detail": "Google Earth Engine no esta inicializado..." }` |
| **500** | Error del motor durante el cálculo | `{ "detail": "Error analizando el punto: ..." }` |

El front debe manejar 503 (mostrar "servicio de datos no disponible,
reintente") distinto de 422 (corregir la entrada del usuario).

---

## 5. Pendiente para v2 (no rompe este contrato)

- **Caché en Supabase** (`analysis_cache`): IMPLEMENTADA. Ver `docs/CACHE.md`.
  Transparente al cliente; cada respuesta trae un bloque `meta` que indica si
  vino de caché o en vivo.
- **Filtro de cultivos por petición** (campo `crops`): hoy la API evalúa
  el set completo (42). Cuando se agregue, será opcional y por defecto el
  comportamiento actual.
- **Autenticación / límites de uso** al exponer en producción.
- GAEZ (FAO) como segunda opinión de aptitud (roadmap).

Cualquier cambio que agregue campos a la respuesta es compatible; quitar o
renombrar campos existentes requiere acordar una nueva versión del contrato.

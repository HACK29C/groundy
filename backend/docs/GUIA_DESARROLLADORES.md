# Groundy — Guía para desarrolladores (frontend)

Cómo consumir la API de Groundy desde la app. Todo listo para conectar.

## URL base
```
https://api.groundy.site
```
- HTTPS automático, 24/7.
- **CORS abierto** (`*`) — se puede llamar desde GitHub Pages o cualquier dominio.
- Formato: JSON en entrada y salida.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| GET  | `/salud` | Estado del servicio (vivo, GEE, caché) |
| GET  | `/cultivos` | Lista de los 42 cultivos (para menús) |
| POST | `/analizar/punto` | Análisis de un punto `{lat, lon}` |
| POST | `/analizar/area` | Análisis de una finca `{coords:[[lon,lat],...]}` |

Documentación interactiva (Swagger): `https://api.groundy.site/docs`
Contrato completo con todos los campos: `docs/CONTRATO_API.md`

## Ejemplos

### Punto (JavaScript / fetch)
```js
const API = "https://api.groundy.site";

async function analizarPunto(lat, lon) {
  const r = await fetch(`${API}/analizar/punto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon }),
  });
  if (!r.ok) throw new Error("Error " + r.status);
  return r.json();
}

// uso:
const data = await analizarPunto(1.21, -77.28);
console.log(data.crops_top);      // mejores cultivos
console.log(data.best_rotation);  // mejor rotación
console.log(data.meta.fuente);    // "cache" | "vivo"
```

### Área / finca (polígono)
```js
async function analizarArea(coords) {   // coords = [[lon,lat], ...]
  const r = await fetch(`${API}/analizar/area`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ coords }),
  });
  return r.json();
}
```

### curl (para probar)
```bash
curl -s https://api.groundy.site/cultivos
curl -s -X POST https://api.groundy.site/analizar/punto \
  -H "Content-Type: application/json" -d '{"lat":1.21,"lon":-77.28}'
```

## Qué devuelve (resumen de campos clave)
- `climate`: tmean_c, rain_mm_yr (POWER), rain_imerg_mm_yr (IMERG), rain_range_mm, et0_mm_yr, aridity.
- `crops_top`: 6 mejores cultivos con `suit` (0–1), `best_month`, `limits`.
- `rotations`: rotaciones ordenadas por `score`, con `seq` y `notes` (notas honestas de limitaciones).
- `best_rotation`, `confidence` ("alta/media/baja"), `sister_site`.
- `vegetation_monthly`: 12 valores por capa (ndvi, evi, lst_c, sm_surf, sm_root, rain_imerg) → para gráficas.
- (área) `terreno_dentro_de_la_finca` (elevación, pendiente), `vegetacion.ndvi_sentinel2_10m`, `resolucion`.
- `meta`: `fuente` ("cache"|"vivo"), `generado_en`, `entregado_en`, `proc_version`.

## Tiempos y caché
- **Primera consulta de un punto nuevo: ~60 s** (consulta satelital en vivo a GEE).
- **Consultas repetidas del mismo punto: instantáneas** (caché en Supabase, `meta.fuente="cache"`).
- Recomendación para la demo: **precalentar** los puntos que se van a mostrar (consultarlos una vez antes).
- En el frontend: muestra un spinner "Analizando…" en la primera consulta.

## Errores
| Código | Significado | Qué hacer |
|---|---|---|
| 422 | Entrada inválida (lat/lon fuera de rango, polígono <3 vértices) | Corregir la entrada del usuario |
| 503 | GEE no disponible | Mostrar "servicio de datos no disponible, reintente" |
| 500 | Error del motor | Reintentar / reportar |

## Notas
- No se necesita API key por ahora.
- La URL `api.groundy.site` es fija y permanente.
- El frontend (la app) se publica aparte (GitHub Pages) y apunta a esta URL.

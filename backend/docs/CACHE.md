# Groundy — Caché-First (Supabase)

Rendimiento y reutilización de datos sin tocar el motor. Todo vive *alrededor*
de la API (`api/config.py`, `api/cache.py`, `api/main.py`). El motor
(`point_engine`, `rotation_score`, `climate_tools`) queda intacto.

## 1. Idea

GEE tarda varios segundos por consulta. Con caché-first, la primera consulta
de un punto/finca se calcula en vivo y se guarda; las siguientes idénticas se
devuelven al instante desde Supabase. Si Supabase no está, la API sigue
respondiendo en vivo (la caché nunca es un punto de falla).

## 2. Tabla `analysis_cache` (SQL de creación)

```sql
create table if not exists public.analysis_cache (
  cache_key    text primary key,     -- SHA-256 de la identidad de la consulta
  kind         text not null check (kind in ('punto','area')),
  lat          double precision,     -- punto: coord; area: centroide (inspección)
  lon          double precision,
  params       jsonb not null,       -- identidad legible (coords, datasets, versión)
  proc_version text not null,        -- versión del procesamiento
  source       text,                 -- procedencia resumida
  payload      jsonb not null,       -- respuesta completa del motor (sin 'meta')
  is_valid     boolean not null default true,
  created_at   timestamptz not null default now(),  -- fecha de extracción
  expires_at   timestamptz,          -- vigencia
  hits         integer not null default 0
);
create index if not exists analysis_cache_expires_idx on public.analysis_cache (expires_at);
create index if not exists analysis_cache_latlon_idx  on public.analysis_cache (lat, lon);

-- RLS activo sin políticas: solo la service_role (servidor) accede.
alter table public.analysis_cache enable row level security;
```
No se modifican `point_cache` ni las demás tablas.

## 3. Clave de caché (SHA-256)

Se arma con la identidad completa de la consulta, de modo que dos consultas que
puedan dar resultados distintos nunca comparten clave:

- `kind` (punto | area)
- geometría: punto = `[lon,lat]` redondeado; area = lista completa de vértices redondeados (el orden importa)
- `DATA_SIGNATURE` (datasets + períodos del motor)
- `proc_version` (versión del procesamiento)
- `decimals` (redondeo usado)
- `extra` (parámetros/variables futuros)

Redondeo por defecto: **4 decimales (~11 m)**. Subir `PROC_VERSION` o cambiar
`DATA_SIGNATURE` invalida toda la caché anterior automáticamente.

## 4. Flujo

```
POST /analizar/punto|area
  clave = SHA256(identidad)
  [lock por clave: evita 2 consultas idénticas simultáneas en el mismo proceso]
  get(clave):
     hit vigente y válido -> devolver payload           meta.fuente = "cache"
     miss / vencido / inválido / Supabase caído:
        payload = motor(...)            (point_engine, intacto)
        si resultado VÁLIDO -> upsert (is_valid, expires_at = now + TTL)
        devolver payload                                 meta.fuente = "vivo"
```

"Válido" = el motor devolvió datos reales. No se cachea si falta el clima
(punto) o la elevación (área), o si todas las capas vienen en error.

## 5. Respuesta: bloque `meta` (nivel superior, no cambia el motor)

```json
{
  "meta": {
    "plataforma": "Groundy",
    "fuente": "cache",                      // "cache" | "vivo"
    "proc_version": "1.1",
    "cache_key": "a3f9...",
    "generado_en": "2026-11-15T09:00:00Z",  // cuándo se CALCULÓ el resultado
    "vigencia_hasta": "2026-12-15T09:00:00Z",
    "entregado_en": "2026-11-15T14:05:00Z"  // cuándo se ENTREGA esta respuesta
  },
  "climate": { ... }, "vegetation_monthly": { ... }, ...   // igual que siempre
}
```
`generado_en` ≠ `entregado_en` cuando el dato viene de caché.

## 6. Variables de entorno

| Variable | Obligatoria | Default | Para qué |
|---|---|---|---|
| `GEE_KEY_PATH` | sí (análisis) | `secrets/gee_key.json` | llave de Earth Engine |
| `SUPABASE_URL` | no (activa caché) | — | URL del proyecto |
| `SUPABASE_SERVICE_KEY` | no (activa caché) | — | service_role (SECRETA, solo servidor) |
| `CACHE_TABLE` | no | `analysis_cache` | tabla de caché |
| `CACHE_TTL_DAYS` | no | `30` | vigencia de un resultado |
| `CACHE_COORD_DECIMALS` | no | `4` | redondeo de coordenadas |
| `PROC_VERSION` | no | `1.1` | versión; súbela para invalidar caché |
| `DATA_SIGNATURE` | no | (datasets+períodos) | firma de fuentes del motor |
| `CORS_ORIGINS` | no | `*` | dominios autorizados |

Sin `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`, la caché queda desactivada y la API
funciona 100% en vivo. Plantilla en `api/.env.example`. El `.env` no va al repo.

## 7. Tolerancia a fallos

- Cualquier error de Supabase (red, credenciales, timeout) → `get` devuelve miss
  y `put` no lanza. La API responde en vivo.
- Solo se guardan resultados válidos.
- Candado por clave (por proceso) evita consultas duplicadas simultáneas.

## 8. Pruebas

**Lógica (sin red/GEE)** — `python /tmp/test_cache_logic.py` en desarrollo:
clave determinista y sensible (coords, geometría, versión), hit/miss,
expiración, validez, y Supabase caído. 18/18 OK.

**Punta a punta (en tu PC, con GEE + Supabase)** — `python api/probar_cache.py`:
- 1ª consulta → `fuente=vivo` (lenta); 2ª idéntica → `fuente=cache` (rápida).
- Punto y área.
- Coordenada distinta → vuelve a `vivo`.
- Expiración: baja `CACHE_TTL_DAYS=0` (o edita `expires_at` en la tabla) → vivo.
- Cambio de versión: sube `PROC_VERSION` → nueva clave → vivo.
- Supabase no disponible: quita `SUPABASE_URL` → `cache=false`, sigue en vivo.

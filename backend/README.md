# Groundy — Backend

API de apoyo a la decisión para **rotación de cultivos** en cualquier punto o
finca del planeta. Combina datos satelitales y climáticos en vivo con
requisitos agronómicos para estimar qué cultivos encajan y qué rotaciones
convienen, con su nivel de confianza.

**NASA Space Apps Challenge 2026 — Field Shift · Equipo Potatonauts**

- **API en vivo:** https://api.groundy.site
- **Docs interactivas:** https://api.groundy.site/docs

## Qué hace

Para un punto (`lat,lon`) o una finca (polígono) devuelve:
- Clima (NASA POWER) y lluvia satelital (GPM IMERG), con rango entre fuentes.
- Vegetación: NDVI/EVI (MODIS), NDVI fino 10 m (Sentinel-2), temperatura
  superficial (MODIS LST), humedad del suelo (SMAP).
- Relieve y pendiente (SRTM 30 m).
- Aptitud de 42 cultivos y rotaciones puntuadas (base FAO EcoCrop).
- Bandera de confianza y sitio de referencia más parecido.

## Arquitectura

```
Frontend (groundy.site)
        │  HTTP/JSON
        ▼
API FastAPI  ──►  Motor (point_engine / rotation_score / climate_tools)
        │               │
        │               ├─ Google Earth Engine (MODIS, SMAP, Sentinel-2, SRTM)
        │               └─ NASA POWER (clima)
        ▼
Supabase (PostgreSQL) — caché de resultados (respuestas instantáneas)
```

- Una sola puerta HTTP; GEE, POWER y Supabase quedan detrás.
- **Caché-first**: la primera consulta se calcula en vivo y se guarda; las
  repetidas responden al instante. Ver `docs/CACHE.md`.
- Corre en producción sobre un **Orange Pi 5B** (Docker) expuesto con
  **Cloudflare Tunnel** (URL fija, HTTPS, 24/7).

## Estructura

```
api/      API FastAPI (main, cache, config) y scripts de prueba
src/      Motor de análisis (no se modifica desde la API)
data/     crop_requirements.csv (42 cultivos, FAO EcoCrop)
db/       Esquema y carga a Supabase
docs/     Contrato de API, caché, guía de desarrolladores, despliegue
notebooks/ Exploración y validación de datos
```

## Correr localmente

```bash
pip install -r api/requirements.txt
set GEE_KEY_PATH=secrets/gee_key.json          # Windows (PowerShell: $env:)
set SUPABASE_URL=...                             # opcional (activa caché)
set SUPABASE_SERVICE_KEY=...                     # opcional (activa caché)
uvicorn api.main:app --reload --port 8000
# docs: http://localhost:8000/docs
```

Las credenciales (llave de GEE, service key de Supabase) van por variables de
entorno — **nunca en el repo** (ver `api/.env.example`).

## Documentación

- `docs/CONTRATO_API.md` — contrato completo de la API.
- `docs/GUIA_DESARROLLADORES.md` — cómo consumir la API desde el frontend.
- `docs/CACHE.md` — diseño de la caché-first (Supabase).
- `docs/DEPLOY.md` — despliegue (referencia).

## Limitaciones (honestidad)

Los umbrales de cultivo (FAO EcoCrop) son **genéricos por especie**, no por
variedad ni calibrados localmente; la papa andina se ajustó a mano. Clima y
humedad son de resolución regional. Es **orientación con su nivel de
confianza**, no una receta de siembra definitiva: no evalúa suelo (pH,
textura, drenaje), plagas locales, mercado ni riego.

## Fuentes de datos

NASA POWER · NASA GPM IMERG · MODIS (MOD13Q1, MOD11A2) · SMAP L4 · SRTM ·
Copernicus Sentinel-2 · FAO EcoCrop.

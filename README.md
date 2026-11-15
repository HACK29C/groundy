# 🌱 Groundy

**Plataforma global de apoyo a la decisión para la rotación de cultivos.**
Combina datos satelitales y climáticos en vivo con requisitos agronómicos para
estimar, en cualquier punto o finca del planeta, qué cultivos encajan y qué
rotaciones convienen — con su nivel de confianza.

> **NASA Space Apps Challenge 2026 — Field Shift · Equipo Potatonauts**

- 🌐 **API en vivo:** https://api.groundy.site · [Docs](https://api.groundy.site/docs)

---

## Estructura del repositorio

```
groundy/
├── backend/     API + motor de análisis (este repo lo tiene completo y en vivo)
│   ├── api/         API FastAPI (endpoints, caché, config, rotaciones globales)
│   ├── src/         Motor de análisis (GEE, NASA POWER, puntuación de rotación)
│   ├── data/        crop_requirements.csv (42 cultivos, FAO EcoCrop)
│   ├── db/          Esquema y carga a Supabase
│   ├── docs/        Contrato de API, caché, guía de desarrolladores, despliegue
│   └── notebooks/   Cuadernos Jupyter: pruebas y validación de datos
└── frontend/    Aplicación web (en desarrollo por el equipo)
```

## Qué hace

Para un **punto** (`lat,lon`) o una **finca** (polígono) devuelve:
- **Clima** (NASA POWER) y **lluvia satelital** (GPM IMERG), con rango entre fuentes.
- **Vegetación:** NDVI/EVI (MODIS), NDVI fino 10 m (Sentinel-2), temperatura
  superficial (MODIS LST), **humedad del suelo** (SMAP).
- **Relieve y pendiente** (SRTM 30 m).
- **Aptitud de 42 cultivos** y **rotaciones puntuadas**, adaptadas al clima real
  de cada lugar (Andes → papa/chocho; Sahel → mijo/caupí; etc.).
- **Nivel de confianza** y sitio de referencia más parecido.

## Arquitectura

```
Frontend (groundy.site)
        │  HTTP / JSON
        ▼
API FastAPI  (api.groundy.site)   ── una sola puerta
        │
        ├── Motor (src/): point_engine · rotation_score · climate_tools
        │        ├─ Google Earth Engine  (MODIS, SMAP, Sentinel-2, SRTM)
        │        └─ NASA POWER            (clima)
        │
        └── Supabase (PostgreSQL)  ── caché-first (respuestas instantáneas)
```

- **Una sola puerta HTTP:** la app nunca toca GEE, POWER ni credenciales.
- **Caché-first:** la primera consulta se calcula en vivo y se guarda; las
  repetidas responden al instante (ver `backend/docs/CACHE.md`).
- **Despliegue:** contenedor Docker sobre un **Orange Pi 5B**, expuesto con un
  **túnel de Cloudflare** con nombre → URL fija HTTPS 24/7 (`api.groundy.site`).

## Integraciones y fuentes de datos

| Fuente | Vía | Qué aporta |
|---|---|---|
| NASA POWER | API REST | Clima diario (temperatura, lluvia, radiación, ET0) |
| NASA GPM IMERG | Google Earth Engine | Lluvia satelital mensual |
| MODIS (MOD13Q1 / MOD11A2) | Google Earth Engine | NDVI/EVI 250 m, temperatura superficial |
| SMAP L4 | Google Earth Engine | Humedad del suelo ~9 km |
| Copernicus Sentinel-2 | Google Earth Engine | NDVI fino 10 m |
| SRTM | Google Earth Engine | Elevación y pendiente 30 m |
| FAO EcoCrop | CSV | Requisitos de 42 cultivos |
| Supabase (PostgreSQL) | API REST | Caché de resultados |

## Escalabilidad

- **Modular:** cada fuente de datos es un módulo independiente; agregar una nueva
  (ERA5, FAO GAEZ, bases de suelo) es añadir una función, sin reescribir el resto.
- **Caché-first:** reduce el costo de cómputo y la latencia; comparte resultados
  entre dispositivos vía Supabase.
- **Contenedorizado:** la misma imagen Docker corre en el Orange Pi, en la nube
  (Cloud Run, Render) o en un VPS, solo cambiando variables de entorno.
- **Contrato estable:** los campos nuevos son retrocompatibles; el frontend no
  se rompe al evolucionar el backend.

## Pruebas y validación

En `backend/notebooks/` están los cuadernos Jupyter usados para **validar las
integraciones** (GEE, NASA POWER, IMERG, Sentinel-2) y **verificar la calidad de
los datos** (comparación de fuentes de lluvia, NDVI MODIS vs Sentinel-2,
coherencia de las series). La caché y el motor tienen además pruebas de
funcionamiento en `backend/api/` (`diag_cache.py`, `probar_cache.py`,
`probar_local.py`).

## Cómo correr el backend

```bash
cd backend
pip install -r api/requirements.txt
# variables de entorno (nunca en el repo): GEE_KEY_PATH, SUPABASE_URL, SUPABASE_SERVICE_KEY
uvicorn api.main:app --reload --port 8000
# docs: http://localhost:8000/docs
```
Detalles de despliegue en `backend/docs/DEPLOY.md`.

## Documentación

- `backend/docs/CONTRATO_API.md` — contrato completo de la API.
- `backend/docs/GUIA_DESARROLLADORES.md` — cómo consumir la API desde el frontend.
- `backend/docs/CACHE.md` — diseño de la caché-first (Supabase).
- `backend/docs/DEPLOY.md` — despliegue.

## Limitaciones (honestidad)

Los umbrales de cultivo (FAO EcoCrop) son **genéricos por especie**, no por
variedad ni calibrados localmente (la papa andina se ajustó a mano). Clima y
humedad son de resolución regional. Es **orientación con su nivel de confianza**,
no una receta de siembra: no evalúa suelo (pH, textura, drenaje), plagas locales,
mercado ni riego.

## Equipo

**Potatonauts** — NASA Space Apps Challenge 2026, Ipiales (Nariño, Colombia).

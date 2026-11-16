# 🌱 Groundy

### Earth intelligence for every field — working at the edge, even offline.

**Groundy** is an AgTech decision-support platform that turns NASA Earth-observation
and climate data into clear, location-specific **crop-rotation guidance** for any
field on the planet. It is built to run where farming actually happens: on a
**low-power edge device at the farm**, so it keeps delivering value when rural
connectivity is weak or absent.

> **NASA Space Apps Challenge 2026 — Field Shift · Team Potatonauts**

| | |
|---|---|
| 🌐 **Live API** | https://api.groundy.site |
| 📖 **Interactive docs** | https://api.groundy.site/docs |
| 🧩 **Stack** | FastAPI · Google Earth Engine · NASA POWER · Supabase · Docker |
| 🖥️ **Runs on** | Orange Pi 5B (edge) + Cloudflare Tunnel (24/7 HTTPS) |

## The problem we tackle

| Challenge | Why it matters |
|---|---|
| **Soil depletion from monoculture** | Repeating the same crop drains nutrients and raises pest pressure. Smart rotation restores soil health — but farmers rarely have data-driven, field-specific guidance. |
| **Data exists, decisions don't** | Satellite and climate data are abundant yet hard to translate into "what should I plant next?" |
| **Connectivity gap in the field** | Rural farmland often has little or no internet, so cloud-only tools fail exactly where they are needed most. |

## Our solution

Groundy answers one practical question for **any point or farm polygon on Earth**:
*what crops fit here, and which rotation keeps the soil healthy?* — each result
carrying its own **confidence level** so the user knows how much to trust it.

| Groundy delivers | Source |
|---|---|
| Climate profile (temperature, rainfall, evapotranspiration) | NASA POWER |
| Satellite rainfall, with cross-source range | NASA GPM IMERG |
| Vegetation vigor (NDVI/EVI) and land-surface temperature | MODIS |
| High-resolution field vegetation (10 m) | Copernicus Sentinel-2 |
| Soil moisture | SMAP |
| Terrain and slope | SRTM |
| Suitability of 42 crops + data-driven rotations | FAO EcoCrop + Groundy engine |

## Edge computing: built for the field

Most AgTech tools assume a stable cloud connection. **Groundy proposes the
opposite: an edge-first model.** The platform runs on an **Orange Pi 5B** — a
low-power single-board computer — installed at or near the farm, acting as a
local server and data store rather than depending on a distant data center.

| Orange Pi 5B — edge node | Spec |
|---|---|
| CPU | 8-core ARM (4× Cortex-A76 + 4× Cortex-A55) |
| Memory | Up to 16 GB RAM |
| Power | A few watts — can run on solar/battery, 24/7 |
| Runtime | Linux + Docker (portable, reproducible) |

**Why it matters for farmers**

| Capability | Benefit |
|---|---|
| **Local data store** | Field analyses and crop records live on the device, close to the user. |
| **Farmer-owned records** | A farmer can register their **fields (location/polygon), crops and planting history**, building a private log over seasons. |
| **Resilient connectivity** | Designed to keep serving with intermittent internet and sync results when a connection is available. |
| **Low cost & replicable** | Affordable hardware means one node per farm, cooperative, or extension office. |

## Architecture

```
            Farmer / Web app  (groundy.site)
                     │   HTTP · JSON
                     ▼
        ┌──────────────────────────────────┐
        │   Groundy API  (api.groundy.site) │   one single gateway
        │              FastAPI              │
        └───────────────┬──────────────────┘
                        │
         ┌──────────────┼───────────────────┐
         ▼              ▼                    ▼
   Analysis engine  NASA POWER        Supabase (PostgreSQL)
   (Earth Engine)   (climate)         cache + records
   MODIS · SMAP
   Sentinel-2 · SRTM
```

| Principle | What it means |
|---|---|
| **Single gateway** | The app only talks to the API; satellite services and credentials stay on the server, never in the browser. |
| **Cache-first** | The first query for a site is computed live and stored; repeated queries return instantly. |
| **Clean separation** | Data sources are independent modules — the analysis engine never mixes with the web layer. |

## Scalability

| Lever | How Groundy scales |
|---|---|
| **Modular data layer** | Each source is a plug-in module; adding a new dataset (ERA5, FAO GAEZ, soil databases) means adding one module, not rewriting the system. |
| **Cache-first performance** | Reduces compute cost and latency; results are shared across devices. |
| **Containerized** | The same Docker image runs on an edge Pi, a cloud service, or a VPS — only environment variables change. |
| **Stable API contract** | New fields are backward-compatible, so the frontend never breaks as the backend grows. |

## Validation & testing

Data quality was verified with **Jupyter notebooks** (`backend/notebooks/`):
cross-checking rainfall sources, comparing MODIS vs Sentinel-2 vegetation,
and reviewing the consistency of the time series. The API and cache ship with
functional tests (`diag_cache.py`, `probar_cache.py`, `probar_local.py`).

## Repository structure

```
groundy/
├── backend/          API + analysis engine (complete and live)
│   ├── api/          FastAPI service (endpoints, cache, global rotations)
│   ├── src/          Analysis engine (Earth Engine, NASA POWER, scoring)
│   ├── data/         Crop requirements (42 crops, FAO EcoCrop)
│   ├── db/           Supabase schema and loaders
│   ├── docs/         API contract, developer guide, cache, deployment
│   └── notebooks/    Data validation (Jupyter)
└── frontend/         Web application (in development)
```

## Transparent by design

Groundy is built to be trusted, not oversold. Crop thresholds come from the
global FAO EcoCrop database; climate and soil-moisture layers are regional in
resolution. Every result is framed as **guidance with a confidence level**, not
a guaranteed prescription — it does not yet model soil chemistry, local pests,
market or irrigation. This honesty is part of the product: the user always knows
how far to trust each recommendation.

## Roadmap

| Next | Value |
|---|---|
| Offline-first local database on the edge node | Full operation without internet |
| Farmer dashboard to register and track fields | Season-over-season crop history |
| Additional layers (ERA5, FAO GAEZ, soil maps) | Richer, calibrated recommendations |
| Local-variety calibration | Advice tuned to regional cultivars |

## Team

**Potatonauts** — NASA Space Apps Challenge 2026 · Ipiales, Nariño, Colombia.

# Groundy — Frontend

Web application of Groundy (Potatonauts · NASA Space Apps Challenge 2026 · Field Shift).
It consumes the backend in this same repository through **https://api.groundy.site** and is published at **groundy.site**.

- Integration guide: `../backend/docs/GUIA_DESARROLLADORES.md`
- API contract: `../backend/docs/CONTRATO_API.md`
- Product and frontend plans: `docs/00_ANALISIS.md`, `docs/01_PLAN_PRODUCTO.md`, `docs/02_PLAN_FRONTEND.md`

## Run locally

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build in dist/
```

## Stack

React + Vite + TypeScript · Tailwind CSS v4 · React Router · i18next (EN default, ES) ·
MapLibre GL + Terra Draw + Turf · Dexie (IndexedDB, local-first) · Chart.js · Phosphor Icons.
Fonts: Young Serif (headings) and Quicksand (body), self-hosted.

## Folders

```
frontend/
├── assets-src/     original brand assets from the team (logo, Potatonaut, farmer, hero video)
├── public/brand/   optimized images (WebP/PNG) generated from assets-src
├── public/media/   compressed hero video and poster
├── docs/           analysis and plans
└── src/
    ├── features/   landing, estilo (style guide), and app sections
    ├── i18n/       en.ts · es.ts · useDict()
    └── styles/     design tokens (tokens.css)
```

## Working with the backend branch

This frontend lives on the `frontend` branch, created from the team repository's `main`, so it always has the
backend next to it. When the backend team updates `main`:

```bash
git fetch equipo
git merge equipo/main      # brings the latest backend into the frontend branch
```

Remotes used: `equipo` → github.com/HACK29C/groundy · `origin` → github.com/Tania-M11/Groundy (GitHub Pages deploy).

# Groundy · Análisis de partida (15-nov-2026, 14:30)

Fuentes revisadas: `Potatonauts_v2.0.docx` (Documento Maestro, 09:27), `Potatonauts_estructura_app_4_secciones.md` (11:25),
`Potatonauts · las cuatro funcionalidades.html` (11:53), `Propuesta_Funcional_Potatonauts.docx` (12:32),
`Groundy_Registro_y_Gestion_de_Cultivos_corregido.docx` (13:03), `Groundy_Arquitectura_Backend.pdf` (13:59)
y la API en vivo `https://api.groundy.site` (probada hoy).

---

## 0. Restricción dominante: el tiempo

El Documento Maestro y el `.md` fijan el cierre **hoy, domingo 15-nov, 11:59 p. m. (Colombia)**, con congelamiento de
código a T−4 h (≈ 8 p. m.). A las 14:30 quedan ≈ 5,5 h útiles de desarrollo. La Propuesta Funcional describe un producto
de varias semanas (cuentas, trazabilidad, evidencias, modelos). **Hay que separar lo que se construye hoy de lo que se
cuenta como visión.** Si la fecha cambió, este análisis se reajusta.

---

## 1. Lo que existe

| Pieza | Estado verificado |
|---|---|
| Backend (FastAPI en Orange Pi 5B + Cloudflare Tunnel) | **Vivo.** `/salud` → ok, GEE ok, caché ok, 42 cultivos, `proc_version 1.2`. |
| Motor | Aptitud por cultivo, rotaciones puntuadas con notas, clima POWER, IMERG, MODIS, SMAP, SRTM, Sentinel-2 (en área). |
| Caché Supabase | Funciona: 2.ª consulta instantánea, vigencia 30 días. |
| Frontend | **No existe.** La carpeta `Groundy` solo tiene `.idea`; `groundy.site` no responde. |
| Repositorio | `Groundy` está **dentro del repo git de `Downloads`**, que tiene archivos *staged* de otro proyecto (MyApplication). Hay que darle repo propio. |
| Arte de Papanauta | No encontrado en la carpeta. |
| Imagen de referencia (propuesta) | Mockup tipo Dribbble (clima por hora, "Health 98 %", "pH 7.2", "Harvest prediction"): **solo inspiración visual**; varias de esas cifras no las podemos mostrar con honestidad. |

### 1.1 Lo que devuelve la API (real, no lo documentado)

`POST /analizar/punto {lat, lon}` (claves en inglés):
- `climate`: `tmean_c`, `rain_mm_yr` (POWER), `rain_imerg_mm_yr`, `rain_range_mm`, `et0_mm_yr`, `aridity` — **solo promedios anuales**.
- `crops_top` (6): `id`, `suit` (0–1), `limits` (`ninguno|lluvia|temperatura`), `best_month` (`"oct"`). Sin nombre → cruzar con `/cultivos`.
- `potato`: aptitud de papa siempre presente.
- `rotations` (5): `seq`, `name`, `score`, `notes` (prosa en español sin tildes: "botanica", "anos").
- `vegetation_monthly`: 12 valores climatológicos de `ndvi`, `evi`, `lst_c`, `sm_surf`, `sm_root`, `rain_imerg` + `vegetation_status`.
- `provenance` (fuente y resolución por variable), `confidence`, `sister_site`, `meta` (`fuente cache|vivo`, `generado_en`, `vigencia_hasta`).

`POST /analizar/area {coords}` (claves **en español**, otra forma): `area_ha` (calculada por la API), `terreno_dentro_de_la_finca`
(elevación y pendiente con media/desv/min/max), `vegetacion` (NDVI MODIS y Sentinel-2), `clima_regional`,
`humedad_suelo_regional_mensual`, `aptitud` (solo papa), `rotaciones`, `confianza`, `resolucion`. **No trae `crops_top` ni series NDVI.**

Medido hoy: consulta nueva en Ipiales = **103 s** (el PDF dice ~60 s); repetida = instantánea; 422 bien formado.

---

## 2. Contradicciones entre documentos (hay que decidir una sola versión)

| Tema | Maestro v2.0 / .md (mañana) | Propuesta / Registro / Backend (tarde) | Recomendación |
|---|---|---|---|
| Nombre | Potatonauts · Papanauta | Groundy (dominio, backend) | **Groundy** = app; Potatonauts = equipo; Papanauta = guía. |
| Plataforma | Web (MapLibre, `apps/web`) | "Aplicación móvil", stack sin definir; backend dice frontend en GitHub Pages | **Web móvil instalable (PWA)**: los jueces abren un enlace; un APK no. |
| Cuentas y privacidad | Sin cuentas; polígonos solo en el navegador; coordenadas solo por POST | Propuesta: Supabase con usuarios y trazabilidad. Registro (más reciente): geometrías **locales** | **Hoy: local (IndexedDB), sin cuenta.** Supabase Auth como siguiente paso. |
| Fuentes activas | "Declarar solo NASA POWER" | Backend ya corre MODIS, SMAP, IMERG, SRTM, Sentinel-2 | Se pueden declarar activas **las que devuelve la API**; IMERG da ≈ 2× la lluvia de POWER → mostrar como rango, no como titular. |
| Dónde se dibuja la parcela | Propuesta §5.1: en Mapa | Registro (13:03): dentro de «Registrar cultivo»; Mapa solo visualiza | **Registro** (es el más reciente). |
| 4.ª sección | `.md`: «Aprender» | Propuesta: «Historial» | **Historial** (trazabilidad + agroclimático) y lo de Aprender va en «Saber más». |
| Núcleo científico | Serie 2001–2025, P−ET₀ mensual, calendario hídrico Wilson, Z5 (R por año) | Backend: aptitud + rotaciones + climatología mensual | Ver brecha G1. |
| Idioma | App abre en **inglés** (regla NASA) | Propuesta: selector ES/EN | Abre en EN, selector ES. Requiere que la API no devuelva prosa (G5). |

---

## 3. Brechas: lo que falta para lo que prometen los documentos

**Datos y backend**
- **G1 · No hay histórico año a año.** La API solo da promedios. Sin datos por año no hay calendario hídrico con Wilson, mapa de calor Mes×Año, comparación de años, Z5 (R) ni gráficas de "¿Qué ocurrió en años anteriores?" del «Saber más». Opciones: (a) endpoint nuevo `POST /historico/punto` con POWER mensual 2001–2025 (P, ET₀, T, radiación); (b) JSON precalculados para los sitios de la demo. Llamar POWER desde el navegador rompe la regla de coordenadas por POST.
- **G2 · El análisis ignora el cultivo declarado.** Solo recibe lat/lon; si el agricultor declara un cultivo fuera del top 6 no hay aptitud para él. Falta: aptitud de los 42 o parámetro `cultivo`. Fecha de siembra, suelo y prioridad no entran en ningún cálculo.
- **G3 · Rotaciones no parten del cultivo actual** ni usan suelo, riego o prioridad (el simulador del Registro sí lo pide). Siempre empiezan en papa.
- **G4 · `confidence` siempre "desconocida"** (punto y área). El PDF promete alta/media/baja.
- **G5 · Contrato inconsistente:** punto en inglés, área en español y con otra forma; textos en prosa española sin tildes; meses como `"oct"`. Impide i18n EN y obliga a un adaptador en el frontend.
- **G6 · Escala:** no hay `grid_cells` ni `area_fraction`. Pasto e Ipiales devuelven el mismo clima (misma celda POWER): es justo el caso que la app debe explicar. Se puede calcular la huella de la celda en el cliente (malla 0,5° × 0,625°).
- **G7 · Latencia de 100 s** en puntos nuevos: el registro no puede quedar bloqueado; análisis en segundo plano, estado "Analizando…", y pre-calentar los puntos de la demo.
- **G8 · No hay catálogo de ciclo** (duración, etapas, Kc) → no se puede mostrar "día 35 del ciclo", etapa ni cosecha estimada. Se necesita un catálogo pequeño (4–6 cultivos de Nariño) rotulado "pendiente de validación agronómica".

**Frontend y producto**
- **G9 · No existe motor de recomendaciones ni de alertas.** Hay que definir reglas deterministas que conviertan la respuesta de la API en tarjetas (situación, motivo, acción de verificación, evidencia) y no prometer alertas en tiempo real: los datos son climatología.
- **G10 · Persistencia** de finca, parcelas, ciclos, actividades y evidencias: no existe ningún esquema. El Supabase del backend es solo caché.
- **G11 · Mapa base satelital** (licencia y atribución), dibujo de polígonos y cálculo de área: por elegir.
- **G12 · Papanauta:** sin arte, sin plantillas, sin conjunto de intenciones para el chat guiado.
- **G13 · Entregables NASA:** deck ≤ 7 diapositivas en inglés, video ≤ 30 s, `AI_USAGE.md`, campos del formulario. No son la app pero compiten por el mismo tiempo.

---

## 4. Cómo se abordaría

**Stack propuesto:** React + Vite + TypeScript, PWA; MapLibre GL + Terra Draw (dibujo) + Turf (área geodésica);
mapa satelital Esri World Imagery con atribución; gráficos con una librería ligera; i18n ES/EN; datos del usuario en IndexedDB;
despliegue en GitHub Pages → `groundy.site`. Paleta del Maestro (§4.2) como tokens.

**Capas del frontend:**
1. `api/` cliente + **adaptador** que unifica punto y área en un solo modelo (resuelve G5 sin tocar el backend).
2. `domain/` finca → parcela → ciclo → evento (la parcela permanece; cada temporada es un ciclo nuevo).
3. `facts/` convierte cada análisis en hechos con id, valor, unidad, fuente, periodo y escala.
4. `rules/` genera recomendaciones desde los hechos (validada / revisar / exploratoria).
5. `papanauta/` plantillas ES/EN + intenciones del chat guiado; «Saber más» se arma con los mismos hechos.

**Plan por ítems (orden de prioridad para hoy):**

| # | Ítem | Entra hoy |
|---|---|---|
| 0 | Repo propio, scaffold, tokens, i18n, despliegue vacío en `groundy.site` | Sí |
| 1 | Esqueleto: 4 secciones, perfil arriba, botón flotante de Papanauta | Sí |
| 2 | Cultivos: «+ Registrar cultivo» con mapa integrado (dibujar, área, nombre) + formulario corto + estados del ciclo | Sí |
| 3 | Análisis en segundo plano por parcela (adaptador, caché local, estados de carga y error) | Sí |
| 4 | Ficha de parcela: aptitud del cultivo, clima con escala honesta, huella de celda, fuentes | Sí |
| 5 | Recomendaciones deterministas + «Saber más» (con climatología mensual que sí existe) | Sí |
| 6 | Planear rotación con las rotaciones de la API ("Guardar como plan" ≠ "Registrar siembra") | Sí |
| 7 | Mapa: visor de parcelas guardadas + capas | Si alcanza |
| 8 | Historial: línea de tiempo de eventos y cosecha | Si alcanza |
| 9 | Papanauta chat guiado por intenciones | Si alcanza (mínimo: chips + respuestas de plantilla) |
| 10 | Inicio con resumen y 3 tarjetas | Sí (reutiliza 4–5) |
| 11 | Histórico 25 años, Wilson, Z5, cuentas Supabase, evidencias con foto | Next Steps, salvo que el backend agregue G1 |

---

## 5. Decisiones pendientes que bloquean el inicio

1. ¿El cierre sigue siendo hoy a las 11:59 p. m.?
2. ¿Web móvil (PWA) o app Android nativa?
3. ¿Hoy sin cuenta (datos en el teléfono) o con Supabase Auth?
4. ¿Quién mantiene el backend y puede añadir hoy G1/G2/G4? (Regla: no tocar la Orange Pi sin avisar.)
5. ¿Hay arte de Papanauta y logo de Groundy?
6. ¿Parcelas de ejemplo precargadas para la demo (Ipiales) o solo las dibujadas por el usuario?

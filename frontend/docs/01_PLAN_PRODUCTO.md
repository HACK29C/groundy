# Groundy · Plan de producto (v1, 15-nov-2026)

**Groundy** es una aplicación web hecha por el equipo **Potatonauts** para el reto *Field Shift: Adapting Farms with NASA Data*.
Su asistente se llama **Potatonaut**. Este documento define la idea completa antes de programar. Reemplaza las decisiones
abiertas de `00_ANALISIS.md`.

---

## 1. La idea en una frase

> Groundy le muestra al agricultor **su finca vista desde el espacio**, a la escala real de cada dato, registra **lo que pasa en
> cada parcela** y explica **cada recomendación con la evidencia que la respalda**: fuente, periodo, resolución y método.

### 1.1 Qué hace distinta a Groundy (innovación con sustento)

| # | Diferenciador | Qué ve el usuario | Por qué es nuevo |
|---|---|---|---|
| D1 | **Cadena de evidencia** | Cada cifra y cada recomendación tiene «¿De dónde sale?»: fuente, producto, resolución, periodo, método, fecha de cálculo y versión del motor. | Las apps agrícolas muestran el número y no su origen. Aquí la recomendación se puede rastrear hasta la consulta que la produjo (`cache_key`, `proc_version`). |
| D2 | **Lupa de escala** | Sobre la parcela se dibuja el tamaño real de cada dato: píxel Sentinel-2 (10 m), MODIS (250 m), SMAP (~9 km) y celda NASA POWER (~55 × 69 km). | Hace visible que Pasto e Ipiales reciben el mismo dato de clima porque caen en la misma celda. Enseña escala sin tecnicismos. |
| D3 | **Caminar el lindero** | Además de dibujar con el dedo, el agricultor recorre el borde y el GPS traza el polígono, mostrando la precisión en metros. | Delimitar sin saber leer una imagen satelital; el área se calcula de forma geodésica y se compara con la de la API. |
| D4 | **Ventana de siembra** | Compara la fecha que declara el agricultor con el mejor mes que estima el motor para ese cultivo y esa ubicación. | Conecta lo declarado con lo satelital sin pronosticar el clima. |
| D5 | **Trazabilidad con sello de integridad** | Cada evento del ciclo (siembra, labores, cosecha, decisión frente a una recomendación) queda encadenado con un hash; un botón verifica que nada se alteró. | Da la garantía que se buscaba con blockchain, sin su costo, y puede exportarse como certificado. |
| D6 | **El agricultor alimenta los modelos** | Con su consentimiento, sus ciclos y cosechas se vuelven datos de campo etiquetados. | Los modelos se entrenan con datos verdaderos de campo, no con supuestos; esto responde a que todavía no hay modelos entrenados. |
| D7 | **Potatonaut cita sus fuentes y dice «no sé»** | Cada respuesta trae chips con los datos usados; si no hay datos responde que no lo sabe. | Un chatbot que no inventa cifras y respeta la escala de cada dato. |

### 1.2 Principios (de dónde vienen)

| Principio | Origen |
|---|---|
| No pronosticar ni fingir precisión de parcela | Documento Maestro v2.0, principio rector |
| Distinguir medido / estimado / declarado / calculado / histórico | Propuesta Funcional §1.2 y §4.2 |
| Faltante = «Sin información», nunca 0 | Maestro §7.3, Registro §7 |
| La parcela permanece; cada temporada es un ciclo nuevo | Registro §1 |
| Plan de rotación ≠ siembra real | Registro §5 y §6 |
| Credenciales solo en el servidor | Arquitectura Backend §4 |
| Inglés por defecto, ES disponible | Maestro §3.1 (regla NASA) |

---

## 2. Arquitectura

```
                         ┌──────────────── Navegador (groundy.site) ────────────────┐
                         │  Web app (PWA) · Mapa · GPS · Potatonaut                 │
                         └──────┬─────────────────────────────────┬────────────────┘
               datos del usuario│ (Auth + RLS)                    │ ciencia (HTTPS/JSON)
                                ▼                                 ▼
                ┌──────────── Supabase ───────────┐   ┌──── Orange Pi 5B (Docker) ────────────┐
                │ Auth · perfiles · fincas        │   │ API FastAPI  api.groundy.site          │
                │ parcelas (PostGIS) · ciclos     │   │ Motor: aptitud, rotaciones, clima      │
                │ eventos con sello de integridad │   │ GEE · NASA POWER · IMERG               │
                │ evidencias (Storage)            │   │ Almacenamiento local:                  │
                │ recomendaciones y decisiones    │   │  · series históricas por celda         │
                │ caché de análisis (existente)   │◄──┤  · catálogo de cultivos y ciclos       │
                └─────────────────────────────────┘   │  · base de conocimiento de Potatonaut  │
                       respaldo nocturno ────────────►│  · datasets y modelos (futuros)        │
                                                      │  · copia de respaldo de Supabase       │
                                                      └────────────────────────────────────────┘
```

### 2.1 Reparto del almacenamiento (una sola fuente de verdad por dato)

| Dato | Dueño (maestro) | Copia | Motivo |
|---|---|---|---|
| Cuenta, perfil, finca, parcelas, ciclos, eventos, evidencias, decisiones | **Supabase** | Orange Pi (respaldo nocturno `pg_dump`) | Auth y políticas por usuario (RLS) listas; acceso desde cualquier dispositivo. |
| Resultado de cada análisis | Supabase `analysis_cache` (ya existe) | — | Caché-first del backend actual. |
| Series 2001–2025, catálogos, base de conocimiento, datasets, modelos | **Orange Pi** | — | Datos pesados y científicos; no son del usuario; sin costo de nube. |

Regla: **nunca dos maestros para el mismo dato**. La Orange Pi guarda copia de lo del usuario, no la edita.

### 2.2 Quién habla con quién
- El navegador usa **Supabase directamente** solo para datos del usuario, con la clave pública y RLS: cada usuario ve
  únicamente sus fincas.
- Toda la ciencia pasa por **`api.groundy.site`**. El navegador nunca llama a GEE ni a NASA POWER.
- Las coordenadas exactas viajan solo por POST.

### 2.3 Stack propuesto

| Capa | Elección | Motivo |
|---|---|---|
| Web | React + Vite + TypeScript, instalable (PWA) | Ligera, funciona en el celular y se publica en GitHub Pages. |
| Mapa | MapLibre GL + imagen satelital (Esri World Imagery, con atribución) | Abierto; permite superponer polígonos, huellas y capas. |
| Dibujo y GPS | Terra Draw + Geolocation API (`watchPosition`) + Turf (área geodésica) | Dibujo táctil, edición de vértices y modo «caminar el lindero». |
| Gráficas | Una librería ligera (p. ej. Chart.js) | Climatología de 12 meses y comparaciones. |
| Usuario | Supabase (Auth, Postgres + PostGIS, Storage, RLS) | Ya decidido por el equipo. |
| Idiomas | i18n ES/EN; ningún texto en el código | Regla NASA y textos de Potatonaut. |

---

## 3. Las secciones

Navegación inferior: **Inicio · Mapa · Cultivos · Historial**. Arriba, el avatar de **Perfil**. En todas, el botón flotante de **Potatonaut**.

### 3.1 Inicio — «Hoy en mi finca»
Pregunta que responde: *¿qué debo mirar hoy?*

| Bloque | Contenido | Dato que lo respalda |
|---|---|---|
| Encabezado | Saludo, finca activa, perfil | Supabase |
| Resumen | Parcelas, ciclos activos, área total | Supabase |
| **Este mes en tu zona** | Cómo suele comportarse el mes actual: lluvia IMERG, humedad del suelo SMAP y verdor NDVI frente al resto del año | `vegetation_monthly` (climatología, no pronóstico) |
| Potatonaut te sugiere (máx. 3) | Situación → motivo → qué verificar → «Saber más» | Reglas sobre los hechos del análisis |
| Próximas actividades | Tareas planificadas en los ciclos | Eventos en Supabase |
| Estado de los datos | Último análisis, origen (caché o vivo) y vigencia | `meta` de la API |

Se excluye a propósito el «clima ahora» (30 °C, viento) del mockup de referencia: no tenemos esa fuente y la regla es no usar «tiempo real» para datos que no lo son.

### 3.2 Mapa — «Mi finca desde el espacio»
Objetivo: ver la finca **a partir de los datos**, con la ubicación del usuario en tiempo real.

1. **Ubicación en tiempo real**: el usuario da permiso, el mapa lo sigue y muestra un círculo de precisión. Sin permiso, se usa un buscador.
2. **Delimitar parcela**: (a) tocar vértices sobre la imagen satelital, o (b) caminar el lindero con GPS. Se puede deshacer,
   mover vértices y ver el área y el perímetro antes de guardar. Es el mismo componente que se abre desde «Registrar cultivo» en Cultivos.
3. **Parcelas guardadas**: polígonos coloreados por cultivo o por estado del ciclo.
4. **Capas de datos** (interruptor, leyenda, fuente y resolución):
   NDVI (Sentinel-2 10 m / MODIS 250 m), pendiente y elevación (SRTM 30 m), humedad del suelo (SMAP ~9 km), lluvia (IMERG / POWER).
5. **Lupa de escala** (D2): huellas superpuestas de cada fuente.
6. **Selector de mes**: recorre los 12 meses de la climatología.
7. **Ficha de parcela** (hoja inferior al tocarla): área, cultivo y etapa, terreno, vegetación, clima regional, aptitud, «Saber más» y acceso a Cultivos e Historial.

### 3.3 Cultivos — «Ciclo productivo»
1. **Mis parcelas**: tarjetas con filtros (En cultivo · Planificadas · En descanso) y el botón **«+ Registrar cultivo»**.
2. **Registrar cultivo** (flujo del documento de Registro): parcela existente o nueva → qué pasa en la parcela
   (sembrado / planificado / descanso / varias zonas) → formulario corto → resumen → guardar.
3. **Detalle de parcela**, en tres pestañas:
   - **Ciclo actual**: aptitud del cultivo declarado, factor limitante, ventana de siembra (D4), días transcurridos y etapa
     (cuando exista el catálogo de ciclos), recomendaciones.
   - **Planear rotación**: rotaciones puntuadas con notas y límites; «Guardar como plan» no es lo mismo que «Registrar siembra».
   - **Actividades**: registro rápido (riego, fertilización, tratamiento, monitoreo, labor, cosecha) con fecha, cantidad,
     foto y **ubicación verificada** (el GPS confirma que el registro se hizo dentro de la parcela).

### 3.4 Historial — «Lo que pasó»
Dos líneas que no se mezclan:

| Historial productivo (Supabase) | Memoria agroclimática (API / Orange Pi) |
|---|---|
| Línea de tiempo por parcela y ciclo; cosechas; recomendaciones con su decisión (aceptada, descartada, pendiente) | Climatología de 12 meses (NDVI, EVI, temperatura de superficie, humedad, lluvia) |
| **Sello de integridad** (D5) y exportación del historial | Comparación POWER vs IMERG (rango de lluvia) |
| Comparar ciclos de la misma parcela | Serie 2001–2025, calendario hídrico (Wilson) y comparación de años **cuando exista el endpoint histórico** |

### 3.5 Perfil
Cuenta, finca y productor, parcelas, idioma, consentimientos (ubicación, uso de datos para modelos), exportar y eliminar datos
(Ley 1581 de 2012 de protección de datos de Colombia), fuentes y métodos, versión, y los campos de la convocatoria cuando se confirmen.

### 3.6 «Saber más» (componente común)
Tres niveles: **¿Por qué?** (2–3 frases + fichas de evidencia) → **Mira los datos** (1–2 gráficas) →
**¿De dónde sale?** (fuente, periodo, resolución, método, versión, limitaciones). Cada gráfica lleva título en forma de pregunta,
una línea «cómo leerla» y un pie con fuente · periodo · resolución.

---

## 4. Potatonaut: el asistente de datos

### 4.1 Comportamiento
- Botón flotante en las cuatro secciones; recibe el contexto: sección, parcela, ciclo y capa activa.
- Preguntas sugeridas según la sección; cada respuesta trae chips con los datos usados y abre el «Saber más».
- Nunca: pronóstico de lluvia o helada, diagnóstico de plagas, prescripción de dosis, cifras que no estén en los datos.

### 4.2 De qué datos se alimenta

| Fuente de conocimiento | Contenido | Dónde vive |
|---|---|---|
| Hechos del análisis | Cada valor de la API convertido en hecho con id, unidad, fuente, periodo y escala | Generados en la web desde la respuesta |
| Datos del agricultor | Parcela, ciclo, actividades, decisiones | Supabase |
| Base de conocimiento | Glosario, fichas de cultivos y guías agronómicas con cita (FAO, AGROSAVIA, CIP) | Orange Pi |
| Catálogo de cultivos | 42 cultivos del motor y, a futuro, duración, etapas y Kc | Orange Pi |

### 4.3 Hoja de ruta de los modelos (no hay ninguno entrenado todavía)

| Etapa | Qué se usa | Sustento |
|---|---|---|
| **v0 (lanzamiento)** | Clasificación de la pregunta en intenciones + plantillas ES/EN rellenadas con hechos. Sin modelo entrenado. | Maestro §8: cero cifras libres. |
| **v1** | Modelo de lenguaje con recuperación (RAG) solo sobre hechos y base de conocimiento; cada frase cita su hecho y un validador revisa cifras, unidades y periodos. | Maestro §8.2; evals adversariales (§8.3). |
| **v2** | Modelos entrenados con los datos de campo de D6: clasificador de intenciones propio, aptitud calibrada con cosechas reales, detección de anomalías. | Requiere dataset etiquetado, partición por año o por finca y validación independiente. |

Cada modelo tendrá su **ficha de modelo**: datos de entrenamiento, periodo, métricas, límites y versión.

---

## 5. Sustento de cada cosa: estándar de procedencia

Todo dato que se muestra lleva:

| Campo | Ejemplo |
|---|---|
| Tipo | medido · estimado · histórico · declarado · calculado |
| Fuente / producto | NASA POWER (MERRA-2) · MODIS MOD13Q1 · SMAP L4 · SRTM · Sentinel-2 · GPM IMERG |
| Resolución | 0,5° × 0,625° · 250 m · ~9 km · 30 m · 10 m |
| Periodo | 2001–2025 / climatología mensual |
| Método | p. ej. ET₀ FAO-56 Penman–Monteith (Allen et al., 1998); intervalo de Wilson (1927) |
| Versión y fecha | `proc_version`, `generado_en`, `vigencia_hasta` |
| Huella | `cache_key` del análisis que lo produjo |

**Documentos que acompañan el código** (para jueces y equipo):
- `docs/FUENTES.md`: cada fuente con URL/DOI, resolución, licencia y lo que **no** puede decir.
- `docs/METODOS.md`: cada cálculo con fórmula, unidades, supuestos y prueba (incluido el método de aptitud del motor, a documentar con el equipo backend).
- `docs/DECISIONES.md`: registro de decisiones con fecha y documento de origen.
- `AI_USAGE.md`: requisito NASA; en qué se usó IA y qué decidió el equipo.

---

## 6. Modelo de datos en Supabase

| Tabla | Campos principales |
|---|---|
| `perfiles` | usuario, nombre, idioma, consentimientos |
| `fincas` / `finca_miembros` | nombre, municipio/vereda, unidad; rol del miembro |
| `parcelas` | finca, nombre, `geom` (PostGIS), `area_m2`, `area_metodo`, padre (subparcela) |
| `ciclos` | parcela, cultivo, variedad, estado (planificado → sembrado → en desarrollo → cosechado / perdido / cancelado), fechas, área sembrada, suelo y riego declarados, prioridad |
| `eventos` | ciclo, tipo, fecha, datos, ubicación verificada, autor, `hash`, `hash_anterior` |
| `evidencias` | evento, ruta en Storage |
| `analisis` | parcela, `cache_key`, `proc_version`, fecha |
| `recomendaciones` / `decisiones` | regla, hechos usados, estado; respuesta del agricultor |

RLS: cada fila es visible solo para los miembros de su finca. Los eventos no se editan: una corrección es un evento nuevo que referencia al anterior.

---

## 7. Lo que el backend necesita agregar

| Id | Endpoint o cambio | Desbloquea |
|---|---|---|
| B1 | `POST /historico/punto`: POWER mensual 2001–2025 (P, ET₀, T, radiación) | Calendario hídrico, comparación de años, Z5 |
| B2 | Aptitud del **cultivo declarado** (o de los 42) | Ciclo actual y ventana de siembra |
| B3 | Rotaciones que **parten del cultivo actual** | Planear rotación |
| B4 | `confidence` calculada (alta/media/baja + motivo) | Insignias de confianza |
| B5 | Capas como teselas (GEE `getMapId`) | Capas sobre el mapa |
| B6 | Códigos en vez de prosa; mismas claves en punto y área | Idioma EN y un solo modelo en la web |

Mientras no existan, la web usa un **adaptador** y muestra «Disponible próximamente» en lugar de inventar datos.

---

## 8. Plan ordenado de ejecución

| Fase | Contenido | Resultado verificable |
|---|---|---|
| 0 · Definición | Este documento, decisiones y contrato de datos | El equipo aprueba |
| 1 · Fundaciones | Repo propio, scaffold web, tokens de diseño, i18n, Supabase (esquema + RLS + Auth), despliegue en `groundy.site` | Registro e inicio de sesión funcionando en línea |
| 2 · Mapa y parcelas | GPS en tiempo real, dibujo, caminar el lindero, área, guardado | Una parcela dibujada aparece al recargar |
| 3 · Cultivos y trazabilidad | Registrar cultivo, estados del ciclo, actividades con ubicación verificada, sello de integridad | Un ciclo completo con eventos encadenados |
| 4 · Análisis y evidencia | Adaptador de la API, análisis en segundo plano, ficha de parcela, lupa de escala, recomendaciones, «Saber más» | Cada cifra abre su procedencia |
| 5 · Historial | Línea de tiempo, verificación de integridad, climatología, POWER vs IMERG | Dos historiales separados |
| 6 · Potatonaut v0 | Intenciones, plantillas, chips con fuentes, respuestas «no sé» | Pasa las preguntas adversariales |
| 7 · Backend (B1–B6) | Por el equipo backend | Desbloquea las partes marcadas como «próximamente» |
| 8 · Datos para IA | Consentimiento, exportación de dataset anonimizado, fichas de modelo | Base para v1/v2 |
| 9 · Entrega | QA móvil, pre-calentar puntos de la demo, deck, video, `AI_USAGE.md` | Enviado |

---

## 9. Por confirmar
1. Fecha real de entrega (los documentos dicen hoy, 15-nov, 11:59 p. m.).
2. ¿El reparto Supabase (usuario) / Orange Pi (ciencia, conocimiento, respaldo) es el que imaginaban?
3. ¿Quién hace B1–B6 en el backend?
4. ¿Hay arte del personaje Potatonaut y logo de Groundy?

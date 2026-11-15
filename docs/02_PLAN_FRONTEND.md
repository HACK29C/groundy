# Groundy · Plan de programación del frontend (15-nov-2026, 15:30)

Entrega: **hoy 11:59 p. m.** Se trabaja por pasos cortos; cada paso termina con algo que se puede ver y probar,
y no se empieza el siguiente sin validar el anterior.

---

## 1. Concepto visual

**Idea:** «la finca vista desde el espacio, contada por una papa astronauta». Fresco, juvenil, con curvas: colinas,
nubes y casco. Hereda de Flashly la base crema, las manchas curvas de fondo, los botones tipo píldora y la tipografía.

### 1.1 Recursos del equipo (carpeta del proyecto)
| Recurso | Uso |
|---|---|
| `hero.mp4` (8 s, 1280×720: la papa en la colina) | Fondo del hero en bucle, sin sonido; póster estático para móviles con ahorro de datos |
| `Logotipo Groundy en verde bosque.png` | Encabezado, pantalla de acceso, favicon (versión recortada) |
| `Patata astronauta kawaii en 3D.png` | Avatar de Potatonaut: botón flotante, chat, estados vacíos |
| `inspiracion diseño/heroinspo.jpg` | Composición del hero: personaje a la izquierda, texto sobre el cielo a la derecha |
| Capturas de Flashly | Fondo crema con manchas curvas, botones píldora, campos redondeados |

### 1.2 Paleta (muestreada de los recursos)
| Token | Hex | De dónde sale | Uso |
|---|---|---|---|
| `bosque` | `#0E3B23` | Logo | Texto principal, botones primarios, navegación |
| `cielo` | `#3C9CB4` | Cielo del video | Datos satelitales, enlaces, capas |
| `pradera` | `#7AB22A` | Pasto del video | Vegetación, éxito, superávit |
| `papa` | `#E49C54` | Potatonaut | Acento de Potatonaut y llamados (solo rellenos, no texto sobre blanco) |
| `casco` | `#CFE8F2` | Orejeras del casco | Manchas de fondo, chips, tarjetas suaves |
| `crema` | `#FFF9F5` | Fondo de Flashly | Fondo general |
| `arcilla` | `#C4452D` | Documento Maestro | Déficit y alertas, siempre con ícono o patrón |

Se verificará contraste WCAG AA en cada combinación de texto antes de cerrar los tokens.

### 1.3 Tipografía
- **Young Serif**: títulos.
- **Quicksand**: contenido e interfaz (pesos 400–700, números tabulares en cifras).
- Auto-alojadas con `@fontsource` para que funcionen sin conexión.

### 1.4 Formas e íconos
- Curvas: secciones que terminan en una colina (borde inferior curvo), tarjetas con radio grande, hojas inferiores redondeadas.
  Cada nivel tiene su propio radio; no todas las piezas son iguales.
- Íconos: **Phosphor Icons** (variantes *duotone* y *fill*, trazos redondeados, encajan con lo juvenil).
- Movimiento: un solo momento orquestado (la entrada del hero); en la app, movimiento solo como respuesta a una acción
  (abrir hoja, guardar). Se respeta `prefers-reduced-motion`.

### 1.5 Estructura (ajustada al pasar de app a web, referencia: quenaris.vercel.app)
Como web ya no hay que meter todo en cuatro pestañas: hay un sitio público que se entiende sin cuenta
(útil para los jueces) y un área privada «Mi finca».

```
SITIO PÚBLICO (barra superior: Inicio · Explorar · Cómo funciona · Datos y métodos · Equipo · [Entrar])
/                 Landing
                    hero con video → el reto (granjero) → la plataforma (diferenciadores D1–D7)
                    → datos NASA que usamos (fuente, resolución) → cómo funciona (cadena de evidencia)
                    → Potatonaut → equipo Potatonauts → llamado «Entrar a mi finca» → footer con recursos
/explorar         Herramienta pública: tocar cualquier punto del planeta (o usar mi ubicación) y ver su análisis,
                    la lupa de escala y «Saber más». Sin cuenta.
/metodos          Datos y métodos: cada fuente con resolución, periodo, licencia y lo que no puede decir;
                    cada cálculo con su fórmula. (Es el «sustento» visible.)
/estilo           Guía de estilo (interna)

ÁREA PRIVADA «MI FINCA» (requiere cuenta; datos primero locales)
/finca            Inicio · Hoy en mi finca
/finca/mapa       Mi finca desde el espacio (dibujo de parcelas, GPS, capas)
/finca/cultivos   Ciclo productivo
/finca/historial  Lo que pasó
/finca/perfil     Perfil y consentimientos
+ Potatonaut      botón flotante en todo el sitio (en el público conoce el punto explorado)
```
Footer (como Quenaris): Plataforma (Explorar, Mi finca) · Recursos (Datos y métodos, API `api.groundy.site/docs`,
AI_USAGE, repositorio) · Equipo · Privacidad.

Móvil: en «Mi finca», barra inferior de 4 secciones y botón flotante encima. Escritorio: riel lateral izquierdo
y el mapa ocupa el resto. Sitio público: barra superior que en móvil se vuelve menú.

**Cambio en los pasos:** F1 construye el landing y la barra pública; «Explorar» se arma en F6 reutilizando el mapa
de F4 y la ficha de análisis, sin cuenta.

---

## 2. Stack del frontend

| Necesidad | Herramienta |
|---|---|
| Base | Vite + React + TypeScript, carpeta `web/` |
| Estilos | Tailwind CSS v4 con los tokens como variables CSS |
| Rutas y estado | React Router · Zustand |
| **Datos locales (el plus)** | **Dexie (IndexedDB)**: todo se guarda primero en el dispositivo y luego se sincroniza con Supabase y la Orange Pi |
| Sin conexión | `vite-plugin-pwa`: la app abre y registra actividades en el campo sin internet |
| Mapa | MapLibre GL + imagen satelital Esri + Terra Draw (dibujo) + Turf (área geodésica) + Geolocation API |
| Gráficas | Chart.js |
| Idiomas | i18next (EN por defecto, ES) |
| Íconos | `@phosphor-icons/react` |
| Pruebas visuales | Skill `webapp-testing` (Playwright): captura en móvil y escritorio de cada paso |

Skills instaladas en `Groundy/.claude/skills`: `frontend-design`, `webapp-testing`, `supabase`,
`supabase-postgres-best-practices` (además de `impeccable`, ya disponible).

### 2.1 Capa de datos «primero local»
```
Pantallas → repositorio (interfaz) → Dexie (IndexedDB)  ← siempre funciona
                                   ↘ cola de sincronización → Supabase (cuando haya conexión)
                                                            → Orange Pi (respaldo y ciencia)
```
Las pantallas nunca hablan con Supabase directamente: así el frontend se construye hoy sin esperar al backend,
y conectar Supabase después es cambiar una pieza, no reescribir.

---

## 3. Pasos

| Paso | Qué se construye | Cómo se verifica | Tiempo |
|---|---|---|---|
| **F0 · Base** | Repo propio, scaffold en `web/`, dependencias, fuentes, tokens, recursos optimizados (logo recortado, papa en WebP, video comprimido + póster) | `npm run dev` abre una página con colores y fuentes | 30 min |
| **F1 · Landing** | Hero con video y texto sobre el cielo, colina curva, secciones y botón de entrada | Captura móvil y escritorio | 45 min |
| **F2 · Esqueleto de la app** | Layout, 4 secciones, avatar de perfil, botón flotante de Potatonaut con panel vacío, EN/ES | Navegar entre secciones y cambiar idioma | 30 min |
| **F3 · Datos locales** | Esquema Dexie: finca, parcela, ciclo, evento con sello de integridad; datos de ejemplo de Ipiales | Recargar y que los datos sigan ahí | 30 min |
| **F4 · Mapa** | Satélite, ubicación en tiempo real, dibujar parcela, caminar el lindero, área y guardado | Dibujar, guardar, recargar y verla | 60 min |
| **F5 · Cultivos** | Mis parcelas, flujo «Registrar cultivo», detalle con 3 pestañas, registro de actividades | Registrar un ciclo con dos actividades | 60 min |
| **F6 · Análisis** | Cliente de la API + adaptador, análisis en segundo plano, ficha de parcela, lupa de escala | La ficha muestra datos reales y su fuente | 45 min |
| **F7 · Evidencia** | Hechos → reglas → tarjetas de recomendación → «Saber más» con gráficas | Cada tarjeta abre su procedencia | 45 min |
| **F8 · Inicio e Historial** | «Hoy en mi finca», línea de tiempo, verificación de integridad, climatología | Tarjetas con datos reales | 45 min |
| **F9 · Potatonaut v0** | Preguntas sugeridas por sección, plantillas EN/ES, chips de fuentes, «no lo sé» | Responde con cifras de los datos y rechaza pronósticos | 40 min |
| **F10 · Cierre** | Modo sin conexión, despliegue en GitHub Pages, QA móvil, puntos de la demo pre-calentados | Abre desde un celular con datos móviles | 30 min |

**Línea de corte:** F0–F7 son el recorrido de la demo. F8–F10 entran según el tiempo.
Supabase (sincronización y Auth) y los cambios del backend (B1–B6) se hacen después de F7, cuando me des los permisos.

---

## 4. Riesgos que hay que mirar ya
1. **Regla de la NASA sobre IA:** según la guía del evento, las imágenes o videos generados con IA llevan marca de agua visible.
   Si la papa o el video se hicieron con IA, hay que poner una etiqueta visible discreta («Imagen generada con IA») y declararlo en `AI_USAGE.md`.
2. **Publicación:** GitHub Pages necesita un repositorio en tu cuenta y que el dominio `groundy.site` apunte a él.
3. **Tiempo de la API:** 100 s en puntos nuevos; los puntos de la demo se pre-calientan antes de grabar.

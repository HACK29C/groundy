# Base de datos de la plataforma (Supabase) — guía para desarrolladores

Proyecto: **BD_Potatonauts** · Postgres en Supabase · acceso público **solo de lectura**.

## 1. Conectarse (3 líneas)

```
URL   : https://svaksbawrhndxyzugjjr.supabase.co
Clave : sb_publishable_W7nHJjURfWWxa3NuHySTKw_pYydW_Sy     (pública; segura para el navegador)
```

La clave pública solo puede **leer**. Escribir exige la clave secreta, que vive únicamente en el PC de quien carga los datos y **nunca** va en el código, en Git ni en el chat. Si la app necesita guardar algo propio (usuarios, preferencias), se crea otra tabla con sus propias reglas.

**Ejemplos**

```bash
# curl: últimos 2 días de POWER en Ipiales
curl "https://svaksbawrhndxyzugjjr.supabase.co/rest/v1/power_daily?site=eq.Ipiales&order=date.desc&limit=2" \
     -H "apikey: sb_publishable_W7nHJjURfWWxa3NuHySTKw_pYydW_Sy"
```

```js
// supabase-js
import { createClient } from '@supabase/supabase-js'
const db = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_KEY)
const { data } = await db.from('master_monthly').select('month,ndvi,rain_mm').eq('site','Puno').order('month')
```

```python
# Python
import requests
r = requests.get(URL + "/rest/v1/rain_monthly", params={"site": "eq.Ipiales", "select": "month,power_mm,imerg_pixel_mm"},
                 headers={"apikey": KEY}); rows = r.json()
```

Filtros útiles: `eq.`, `gte.`, `lte.` (`date=gte.2020-01-01`), `order=`, `select=col1,col2`.
**Ojo:** cada llamada devuelve máximo **1.000 filas**. Para `power_daily` (109.572 filas) filtra por `site` y fechas, o pagina con `limit` y `offset`.

## 2. Qué hay en las tablas

| Tabla | Filas | Qué contiene | Llave |
|---|---|---|---|
| `sites` | 12 | Los sitios de referencia: grupo, zona, lat, lon, elevación (aprox. y SRTM) | `site` |
| `power_daily` | 109.572 | Clima diario NASA POWER 2001–2025: temperaturas, lluvia, humedad, viento, radiación | `site`, `date` |
| `imerg_daily` | 3.294 | Lluvia satelital IMERG diaria (solo 2024) con variables de calidad | `site`, `date` |
| `rain_monthly` | 108 | Lluvia mensual 2024 por fuente (POWER, IMERG píxel, IMERG media 5×5, microondas) y rango | `site`, `month` |
| `rain_sites` | 9 | Resumen por sitio: totales anuales por fuente, días de lluvia, racha seca máxima | `site` |
| `master_monthly` | *pendiente* | Tabla mensual unificada: lluvia, ET0, temperatura, NDVI/EVI, humedad del suelo (SMAP) y anomalías | `site`, `month` |

`master_monthly` se llena cuando termine el notebook 04 (NDVI y SMAP). Hoy existe pero está vacía.
Unidades: lluvia en mm, temperatura en °C, humedad del suelo en m³/m³, NDVI sin unidad (−0,2 a 1).

## 3. Por qué Supabase y no la NASA directo

La app **sí** puede llamar a NASA POWER en vivo (API pública, por coordenadas, responde en segundos). Con el resto de fuentes no conviene, por estas razones:

| Fuente | Directo desde la app | Problema |
|---|---|---|
| POWER (clima) | Sí | Ninguno; se usa en vivo para puntos nuevos y se guarda en caché |
| IMERG (lluvia satelital) | No | Exige cuenta Earthdata; ≈9 s por cada día pedido (un año ≈ 55 min) |
| NDVI, SMAP, SRTM (vía AppEEARS) | No | Funciona por tareas asíncronas: se envía la solicitud y NASA responde en **minutos u horas**; requiere usuario y contraseña de Earthdata |

Además:
- **Credenciales:** una app pública no puede llevar la contraseña de Earthdata. Aquí queda solo en el PC de quien procesa.
- **Velocidad y disponibilidad:** consultar Supabase tarda milisegundos y está activo 24/7; la cola de NASA no se puede predecir.
- **Datos ya limpios:** los notebooks filtran valores de relleno, nubes/nieve (calidad de píxel) y convierten unidades. La app recibe tablas listas, no archivos crudos.
- **Reproducible y estable:** todos los usuarios ven los mismos números, y los análisis del equipo se pueden citar.
- **Costo:** las tablas son pequeñas (menos de 50 MB), caben en el plan gratuito.

## 4. Cómo llegan los datos (flujo)

```
NASA (POWER, IMERG, AppEEARS)
   → notebooks 01–04 (PC del equipo: descarga, limpieza, estadística)
   → archivos en data/*.csv
   → python db/upload_to_supabase.py   (clave secreta, campo oculto)
   → Supabase (tablas de arriba)  → app (clave pública, solo lectura)
```

Para recargar o actualizar: ejecutar de nuevo `db/upload_to_supabase.py`. Es seguro repetirlo (actualiza por llave primaria, no duplica). El esquema está en `db/01_schema.sql`.

## 5. Lo que hay que tener presente al mostrar los datos

- **Son 12 sitios de referencia**, no un mapa global: 9 climas contrastantes y 3 zonas andinas de papa (Ventaquemada, Huancayo, Puno). Mostrar como "casos de estudio".
- **La lluvia no coincide entre fuentes** (en Ipiales: POWER 1.183, IMERG 1.661 mm/año). Mostrar el **rango** y usar totales semanales o mensuales; no usar el dato diario para alertas.
- Un píxel satelital (IMERG ≈ 11 km; SMAP ≈ 9 km) **no es una parcela**: puede diferir bastante del campo.
- `imerg_daily` cubre solo **2024**; las series largas (2001–2025) son de POWER.
- Los datos de IMERG, NDVI y SMAP **no se actualizan solos**: se recargan cuando el equipo corre los notebooks.

## 6. Seguridad

- Seguridad por filas (RLS) activada en todas las tablas, con política "lectura pública".
- Los roles públicos solo tienen permiso de lectura; insertar, actualizar y borrar están revocados.
- Plan gratuito de Supabase: se **pausa tras ~1 semana sin uso**. Antes de la demo, abrir el proyecto o hacer una consulta; para producción, plan de pago.

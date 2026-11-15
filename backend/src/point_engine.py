"""Camino B — motor por punto (live global engine).

CUALQUIER lat/lon: NDVI/EVI/humedad/temperatura (GEE) + clima (NASA POWER) + puntaje de rotacion.
Usa la cuenta de servicio (llave permanente). Reporta estado y procedencia de cada capa.
"""
import io
import numpy as np
import pandas as pd
import requests
import ee

import climate_tools as ct
import rotation_score as rs

SA_EMAIL = "papanauta-server@kinetic-anvil-457906-e8.iam.gserviceaccount.com"
PROJECT = "kinetic-anvil-457906-e8"


def init_ee(key_path):
    creds = ee.ServiceAccountCredentials(SA_EMAIL, key_path)
    ee.Initialize(creds, project=PROJECT)


def _modis_clim(coll, band, scale, lat, lon, start, end, factor, offset=0.0):
    """Climatologia mensual (12) para MODIS: muestrea el punto imagen por imagen y agrupa por mes."""
    pt = ee.Geometry.Point([lon, lat])
    c = ee.ImageCollection(coll).select(band).filterDate(start, end)

    def f(img):
        v = img.reduceRegion(ee.Reducer.first(), pt, scale).get(band)
        return ee.Feature(None, {"moy": img.date().get("month"), "v": v})

    fc = ee.FeatureCollection(c.map(f)).filter(ee.Filter.notNull(["v"]))
    groups = fc.reduceColumns(ee.Reducer.mean().group(groupField=1, groupName="moy"), ["v", "moy"]).get("groups").getInfo()
    out = [None] * 12
    for g in groups:
        out[int(g["moy"]) - 1] = round(float(g["mean"]) * factor + offset, 4)
    return out


def _smap_clim(band, scale, lat, lon, start="2020-01-01", end="2025-12-31"):
    """SMAP (cada 3 h): filtra a ~1 imagen/dia, muestrea el punto por imagen y agrupa por mes.
    No usa .mean() sobre la coleccion entera (eso es lo que agotaba la memoria)."""
    pt = ee.Geometry.Point([lon, lat])
    c = (ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").select(band)
         .filterDate(start, end).filter(ee.Filter.calendarRange(13, 13, "hour")))

    def f(img):
        v = img.reduceRegion(ee.Reducer.first(), pt, scale).get(band)
        return ee.Feature(None, {"moy": img.date().get("month"), "v": v})

    fc = ee.FeatureCollection(c.map(f)).filter(ee.Filter.notNull(["v"]))
    groups = fc.reduceColumns(ee.Reducer.mean().group(groupField=1, groupName="moy"), ["v", "moy"]).get("groups").getInfo()
    out = [None] * 12
    for g in groups:
        out[int(g["moy"]) - 1] = round(float(g["mean"]), 4)
    return out


def _layer(fn):
    """Ejecuta una capa y devuelve su estado + valores (no confunde 'sin datos' con 'error')."""
    try:
        vals = fn()
        ok = any(v is not None for v in vals)
        return {"status": "ok" if ok else "sin_datos", "values": vals}
    except Exception as ex:
        return {"status": "error", "reason": repr(ex)[:90], "values": [None] * 12}


def gee_point(lat, lon):
    return {
        "ndvi":    _layer(lambda: _modis_clim("MODIS/061/MOD13Q1", "NDVI", 250, lat, lon, "2001-01-01", "2025-12-31", 0.0001)),
        "evi":     _layer(lambda: _modis_clim("MODIS/061/MOD13Q1", "EVI", 250, lat, lon, "2001-01-01", "2025-12-31", 0.0001)),
        "lst_c":   _layer(lambda: _modis_clim("MODIS/061/MOD11A2", "LST_Day_1km", 1000, lat, lon, "2001-01-01", "2025-12-31", 0.02, -273.15)),
        "sm_surf": _layer(lambda: _smap_clim("sm_surface", 11000, lat, lon)),
        "sm_root": _layer(lambda: _smap_clim("sm_rootzone", 11000, lat, lon)),
        "rain_imerg": _layer(lambda: _imerg_clim(lat, lon)),
    }


def elev_point(lat, lon):
    dem = ee.Image("USGS/SRTMGL1_003")
    v = dem.reduceRegion(ee.Reducer.mean(), ee.Geometry.Point([lon, lat]), 90).get("elevation").getInfo()
    return None if v is None else float(v)


def power_point(lat, lon, start="20010101", end="20251231"):
    """Clima diario de NASA POWER. Verifica la respuesta HTTP y el encabezado antes de procesar."""
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=" + ",".join(ct.VARS) +
           f"&community=AG&longitude={lon}&latitude={lat}&start={start}&end={end}&format=CSV")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    txt = r.text
    if "-END HEADER-" not in txt:
        raise ValueError("Respuesta de NASA POWER sin encabezado valido: " + txt[:200])
    body = txt[txt.index("-END HEADER-") + len("-END HEADER-"):].strip()
    d = pd.read_csv(io.StringIO(body)).replace(-999, np.nan)
    missing = [c for c in ct.VARS if c not in d.columns]
    if missing:
        raise ValueError("Faltan columnas en POWER: " + ",".join(missing))
    if {"MO", "DY"} <= set(d.columns):
        date = pd.to_datetime(dict(year=d.YEAR, month=d.MO, day=d.DY))
    else:
        date = pd.to_datetime(d.YEAR.astype(str), format="%Y") + pd.to_timedelta(d.DOY - 1, unit="D")
    out = d[ct.VARS].copy()
    out.index = date
    out.index.name = "fecha"
    return out


def _annual_mean(monthly_series):
    """Promedio anual real: acumula por ano (solo anos con 12 meses) y promedia."""
    annual = monthly_series.resample("YS").sum(min_count=12)
    return float(annual.mean()) if annual.notna().any() else float("nan")


def _confidence(pw, lat, elev):
    try:
        import site_similarity as ss
        ref = ss.reference_table(["../data", "data"])
        sim = ss.Similarity(ref)
        return sim.flag(ss.features(pw, lat, elev))
    except Exception as ex:
        return {"confidence": "desconocida", "note": f"sin patron de referencia ({repr(ex)[:60]})"}


def analizar_punto(lat, lon, crops=None):
    crops = crops if crops is not None else rs.load_crops()
    pw = power_point(lat, lon)
    elev = elev_point(lat, lon)
    elev = 0.0 if elev is None else elev
    clim = rs.monthly_from_power(pw, lat, elev)
    summ = rs.crop_table(clim, crops, pw)
    tab, notes = rs.compare_strategies(summ, crops)
    veg = gee_point(lat, lon)
    flag = _confidence(pw, lat, elev)
    best = tab.index[0]
    rain_yr = _annual_mean(clim["rain"])
    et0_yr = _annual_mean(clim["et0"])
    _im = veg.get("rain_imerg", {}).get("values", [None]*12)
    imerg_yr = round(sum(x for x in _im if x is not None)) if any(x is not None for x in _im) else None
    _sources = [v for v in [round(rain_yr), imerg_yr] if v is not None]
    return {
        "lat": lat, "lon": lon, "elev_m": round(elev),
        "climate": {"tmean_c": round(float(clim["tmean"].mean()), 1),
                    "rain_mm_yr": round(rain_yr),
                    "et0_mm_yr": round(et0_yr),
                    "aridity": round(rain_yr / max(et0_yr, 1), 2),
                    "rain_imerg_mm_yr": imerg_yr,
                    "rain_range_mm": [min(_sources), max(_sources)] if len(_sources) > 1 else None},
        "vegetation_monthly": {k: v["values"] for k, v in veg.items()},
        "vegetation_status": {k: v["status"] for k, v in veg.items()},
        "confidence": flag.get("confidence"),
        "sister_site": flag.get("sister_site"),
        "potato": {k: (round(float(v), 2) if isinstance(v, float) else v)
                   for k, v in summ.loc["papa"].items() if k in ["suit", "reliability", "limiting", "best_month_es"]},
        "crops_top": [{"id": i, "suit": round(float(r.suit), 2), "best_month": r.best_month_es, "limits": r.limiting}
                      for i, r in summ.head(6).iterrows()],
        "rotations": [{"name": k, "score": round(float(r["score"]), 1), "seq": rs.STRATEGIES[k],
                       "notes": notes[k]} for k, r in tab.iterrows()],
        "best_rotation": best,
        "provenance": {"climate": "NASA POWER (grid 0.5x0.625)", "ndvi_evi": "MODIS MOD13Q1 250m",
                       "lst": "MODIS MOD11A2 1km", "soil_moisture": "SMAP L4 ~9km", "elevation": "SRTM 30m",
                       "note": "caracterizacion ambiental del punto, no medicion directa de la parcela"},
    }


# ---------------------------------------------------------------------------
# Camino B (area): caracterizar una FINCA (poligono), no solo un punto.
# Separa lo que varia DENTRO del predio (relieve/pendiente 30m, NDVI) de lo
# que es REGIONAL por resolucion gruesa (humedad SMAP ~9km, clima POWER ~50km).
# ---------------------------------------------------------------------------
def _r(x, n=3):
    return None if x is None else round(float(x), n)


def _polygon(coords):
    """coords = lista de [lon, lat] (vertices de la finca)."""
    ring = list(coords)
    if ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    return ee.Geometry.Polygon([ring])


def _zonal(img, band, geom, scale):
    """Media, desviacion, min y max de una capa dentro del poligono."""
    red = (ee.Reducer.mean()
           .combine(ee.Reducer.stdDev(), sharedInputs=True)
           .combine(ee.Reducer.minMax(), sharedInputs=True))
    d = img.reduceRegion(red, geom, scale, maxPixels=int(1e9), bestEffort=True).getInfo()
    return {"media": _r(d.get(band + "_mean")), "desv": _r(d.get(band + "_stdDev")),
            "min": _r(d.get(band + "_min")), "max": _r(d.get(band + "_max"))}


def analizar_area(coords, crops=None):
    """Caracteriza una finca (poligono de [lon,lat])."""
    geom = _polygon(coords)
    c = geom.centroid(1).coordinates().getInfo()
    lon, lat = float(c[0]), float(c[1])
    area_ha = geom.area(1).getInfo() / 10000.0

    dem = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(dem).rename("slope")
    terreno = {"elevacion_m": _zonal(dem, "elevation", geom, 30),
               "pendiente_grados": _zonal(slope, "slope", geom, 30)}

    ndvi_img = (ee.ImageCollection("MODIS/061/MOD13Q1").select("NDVI")
                .filterDate("2022-01-01", "2025-12-31").mean().multiply(0.0001).rename("NDVI"))
    vegetacion = {"ndvi_modis_250m": _zonal(ndvi_img, "NDVI", geom, 250),
                  "ndvi_sentinel2_10m": _s2_ndvi_zonal(geom)}

    punto = analizar_punto(lat, lon, crops=crops)
    return {
        "centroide": {"lat": round(lat, 5), "lon": round(lon, 5)},
        "area_ha": round(area_ha, 2),
        "terreno_dentro_de_la_finca": terreno,
        "vegetacion": vegetacion,
        "clima_regional": punto["climate"],
        "humedad_suelo_regional_mensual": punto["vegetation_monthly"].get("sm_root"),
        "aptitud": punto["potato"],
        "mejor_rotacion": punto["best_rotation"],
        "rotaciones": punto["rotations"],
        "confianza": punto["confidence"],
        "resolucion": {"relieve_pendiente": "SRTM 30m — varia dentro de la finca",
                       "ndvi": "MODIS 250m — variacion gruesa (Sentinel-2 10m para detalle fino, fase 2)",
                       "humedad_suelo": "SMAP ~9km — valor regional",
                       "clima": "NASA POWER ~50km — valor regional"},
    }


# ---------------------------------------------------------------------------
# IMERG (lluvia satelital) y Sentinel-2 (NDVI fino 10m, multiespectral limpio)
# ---------------------------------------------------------------------------
def _imerg_clim(lat, lon, start="2001-01-01", end="2025-12-31"):
    """Lluvia mensual (mm/mes) de GPM IMERG mensual. 'precipitation' viene en mm/hr -> x24 x dias."""
    pt = ee.Geometry.Point([lon, lat])
    c = ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V07").select("precipitation").filterDate(start, end)

    def f(img):
        s = img.date()
        days = s.advance(1, "month").difference(s, "day")
        total = img.multiply(24).multiply(days)
        v = total.reduceRegion(ee.Reducer.first(), pt, 11132).get("precipitation")
        return ee.Feature(None, {"moy": s.get("month"), "v": v})

    fc = ee.FeatureCollection(c.map(f)).filter(ee.Filter.notNull(["v"]))
    groups = fc.reduceColumns(ee.Reducer.mean().group(groupField=1, groupName="moy"), ["v", "moy"]).get("groups").getInfo()
    out = [None] * 12
    for g in groups:
        out[int(g["moy"]) - 1] = round(float(g["mean"]), 1)
    return out


def _s2_ndvi_zonal(geom, start="2023-01-01", end="2025-12-31"):
    """NDVI de Sentinel-2 a 10m, estadistica dentro del poligono.

    Mascara estricta pensada para los Andes (muy nubosos): se queda SOLO con
    pixeles de vegetacion (SCL=4) o suelo desnudo (SCL=5) y con baja probabilidad
    de nube (MSK_CLDPRB<15). El prefiltro de escena es laxo (CLOUDY<60) para no
    perder fechas; la limpieza real es por pixel. Evita que nube/sombra/agua
    hundan el promedio.
    """
    def mask(img):
        scl = img.select("SCL")
        cld = img.select("MSK_CLDPRB")
        good = scl.eq(4).Or(scl.eq(5)).And(cld.lt(15))
        return img.updateMask(good)

    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geom).filterDate(start, end)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(mask))
    ndvi = col.map(lambda i: i.normalizedDifference(["B8", "B4"]).rename("NDVI")).median().rename("NDVI")
    return _zonal(ndvi, "NDVI", geom, 10)

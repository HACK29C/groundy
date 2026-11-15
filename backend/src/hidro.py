"""Funciones de clima y balance hídrico reutilizables (notebooks hoy, backend de la app después).

Metodología: FAO Irrigation and Drainage Paper 56 (Allen et al., 1998).
Entradas esperadas: DataFrame diario con columnas de NASA POWER
(T2M_MAX, T2M_MIN, T2M, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN) e índice de fechas.
"""
import numpy as np
import pandas as pd


def es(T):
    """Presión de vapor de saturación (kPa) a temperatura T (°C)."""
    return 0.6108 * np.exp(17.27 * T / (T + 237.3))


def radiacion_extraterrestre(lat, doy):
    """Ra (MJ/m²/día), FAO-56 ec. 21."""
    phi = np.radians(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws)
    )


def et0_fao56(df, lat, elev):
    """ET0 diaria (mm/día) Penman-Monteith FAO-56 con variables de POWER.

    Humedad: POWER da RH media diaria; ea = RH/100 · (es(Tmax)+es(Tmin))/2 (ec. 19 con RHmedia).
    Radiación: ALLSKY_SFC_SW_DWN ya incluye nubes (Rs).
    """
    tmax, tmin, tmed = df["T2M_MAX"], df["T2M_MIN"], df["T2M"]
    rs, u2, rh = df["ALLSKY_SFC_SW_DWN"], df["WS2M"], df["RH2M"]
    doy = df.index.dayofyear.values

    P = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
    gamma = 0.000665 * P
    delta = 4098 * es(tmed) / (tmed + 237.3) ** 2
    e_s = (es(tmax) + es(tmin)) / 2
    e_a = rh / 100 * e_s

    ra = radiacion_extraterrestre(lat, doy)
    rso = (0.75 + 2e-5 * elev) * ra
    rns = (1 - 0.23) * rs
    ratio = np.clip(rs / rso, 0.3, 1.0)
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 \
        * (0.34 - 0.14 * np.sqrt(e_a)) * (1.35 * ratio - 0.35)
    rn = rns - rnl

    num = 0.408 * delta * rn + gamma * 900 / (tmed + 273) * u2 * (e_s - e_a)
    den = delta + gamma * (1 + 0.34 * u2)
    return (num / den).clip(lower=0).rename("ET0")


def climatologia_diaria(s, ventana=15):
    """Ciclo estacional medio por día del año, suavizado circularmente."""
    c = s.groupby(s.index.dayofyear).mean().reindex(range(1, 367)).interpolate()
    ext = pd.concat([c.iloc[-ventana:], c, c.iloc[:ventana]])
    suave = ext.rolling(2 * ventana + 1, center=True).mean().iloc[ventana:-ventana]
    suave.index = range(1, 367)
    return suave


def anomalias(df):
    """Resta el ciclo estacional a cada columna (quita lo predecible por época del año)."""
    out = {}
    for c in df.columns:
        clim = climatologia_diaria(df[c])
        out[c] = df[c] - clim.reindex(df.index.dayofyear).values
    return pd.DataFrame(out, index=df.index)


def fraccion_estacional(df):
    """Parte de la varianza diaria que explica solo el ciclo del año (R² del ciclo estacional)."""
    an = anomalias(df)
    return (1 - an.var() / df.var()).rename("varianza_estacional")


def racha_seca_max(lluvia, umbral=1.0):
    """Racha máxima de días consecutivos con lluvia < umbral, por año."""
    seco = (lluvia < umbral).astype(int)
    res = {}
    for y, g in seco.groupby(seco.index.year):
        mx = run = 0
        for v in g.values:
            run = run + 1 if v else 0
            mx = max(mx, run)
        res[y] = mx
    return pd.Series(res, name="racha_seca_max")


def resumen_sitio(df, lat, elev, umbral_helada=2.0):
    """Indicadores comparables entre sitios del mundo."""
    et0 = et0_fao56(df, lat, elev)
    anual_p = df["PRECTOTCORR"].groupby(df.index.year).sum()
    anual_e = et0.groupby(et0.index.year).sum()
    mens = df["PRECTOTCORR"].resample("MS").sum()
    fr = fraccion_estacional(df)
    return {
        "lluvia_mm_ano": anual_p.mean(),
        "lluvia_CV_%": 100 * anual_p.std() / anual_p.mean(),
        "ET0_mm_ano": anual_e.mean(),
        "aridez_P/ET0": anual_p.mean() / anual_e.mean(),
        "Tmed_C": df["T2M"].mean(),
        "amplitud_anual_C": (df["T2M"].resample("MS").mean().groupby(lambda d: d.month).mean().max()
                             - df["T2M"].resample("MS").mean().groupby(lambda d: d.month).mean().min()),
        "dias_Tmin<=2C_ano": (df["T2M_MIN"] <= umbral_helada).groupby(df.index.year).sum().mean(),
        "racha_seca_max_dias": racha_seca_max(df["PRECTOTCORR"]).mean(),
        "estacionalidad_lluvia_R2": fr["PRECTOTCORR"],
        "estacionalidad_Tmin_R2": fr["T2M_MIN"],
    }

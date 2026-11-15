"""Cliente mínimo para descargar datos diarios de NASA POWER.

Uso:
    from power_client import descargar_power
    df = descargar_power(lat=0.83, lon=-77.64)
"""
import requests
import pandas as pd
from pathlib import Path

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMS = [
    "T2M_MAX", "T2M_MIN", "T2M",        # temperatura (C)
    "PRECTOTCORR",                       # precipitación (mm/día)
    "RH2M",                              # humedad relativa (%)
    "WS2M",                              # viento a 2m (m/s)
    "ALLSKY_SFC_SW_DWN",                 # radiación solar (MJ/m2/día)
]

def descargar_power(lat: float, lon: float,
                    inicio: str = "20010101",
                    fin: str = "20251231",
                    cache_dir: str = "data") -> pd.DataFrame:
    """Descarga datos diarios de POWER. Cachea en CSV para no repetir llamadas."""
    cache = Path(cache_dir) / f"power_{lat}_{lon}_{inicio}_{fin}.csv"
    if cache.exists():
        print(f"[cache] {cache}")
        return pd.read_csv(cache, parse_dates=["fecha"], index_col="fecha")

    params = {
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": inicio,
        "end": fin,
        "format": "JSON",
    }
    print(f"[POWER] descargando {lat},{lon} ...")
    r = requests.get(POWER_URL, params=params, timeout=120)
    r.raise_for_status()
    data = r.json()["properties"]["parameter"]

    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "fecha"
    df = df.replace(-999, float("nan")).astype(float)

    cache.parent.mkdir(exist_ok=True)
    df.to_csv(cache)
    print(f"[OK] {df.shape[0]} días, guardado en {cache}")
    return df


if __name__ == "__main__":
    df = descargar_power(lat=0.83, lon=-77.64)
    print(df.tail())
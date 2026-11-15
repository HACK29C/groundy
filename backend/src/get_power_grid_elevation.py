"""Reads the elevation of the NASA POWER model grid cell for each reference site (printed in the API header)
and compares it with the SRTM elevation. The difference explains temperature bias in mountains and feeds
rotation_score.lapse_adjust(). Run from the project root:

    .venv\\Scripts\\python.exe src\\get_power_grid_elevation.py

Writes data/power_grid_elevation.csv. No login needed (POWER is public).
"""
import re
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
SITES = {"Ipiales": (0.83, -77.64), "Nairobi": (-1.29, 36.82), "Sorriso": (-12.54, -55.71), "Des Moines": (41.60, -93.61),
         "Ludhiana": (30.90, 75.85), "Niamey": (13.51, 2.11), "Can Tho": (10.03, 105.78), "Mendoza": (-32.89, -68.84),
         "Fallon": (39.47, -118.78), "Ventaquemada": (5.37, -73.52), "Huancayo": (-12.07, -75.21), "Puno": (-15.84, -70.02)}

topo = pd.read_csv(ROOT / "data" / "appeears_topo.csv")
col = [c for c in topo.columns if "DEM" in c.upper()][0]
srtm = topo.groupby("ID")[col].first()

rows, shown = [], False
for n, (la, lo) in SITES.items():
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M&community=AG"
           f"&longitude={lo}&latitude={la}&start=20240101&end=20240102&format=CSV")
    txt = requests.get(url, timeout=60).text
    head = [l for l in txt.splitlines()[:40] if "levation" in l]
    # the line reads like "Elevation from MERRA-2: Average for ... region = 3993.24 meters": take the number before "meters"
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*meters", " ".join(head))
    if not shown:
        print("Header line used:", head); shown = True
    rows.append((n, float(m.group(1)) if m else None, float(srtm[n])))

df = pd.DataFrame(rows, columns=["site", "power_grid_elev_m", "srtm_m"]).set_index("site")
df["grid_minus_site_m"] = df["power_grid_elev_m"] - df["srtm_m"]
df["temp_correction_C"] = 0.0065 * df["grid_minus_site_m"]
df.to_csv(ROOT / "data" / "power_grid_elevation.csv")
print(df.round(1).to_string())

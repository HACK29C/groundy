"""Upload the platform tables in ../data to Supabase (BD_Potatonauts).

Usage (from the repo root, with the project's python):
    python db/upload_to_supabase.py --dry-run      # only checks the files, needs no key
    python db/upload_to_supabase.py                # asks for the secret key (hidden) and uploads

The secret key is read from the SUPABASE_SECRET_KEY environment variable if set, otherwise typed
hidden at run time. It is never printed or written to disk. Do NOT commit it.
Re-running is safe: rows are upserted by primary key.
"""
import sys, os, re, json, getpass, argparse
from pathlib import Path
import numpy as np, pandas as pd, requests

URL = "https://svaksbawrhndxyzugjjr.supabase.co"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SITES = {  # name: (group, zone, lat, lon, approx elevation m)
 "Ipiales": ("Global reference", "Andean highland, Colombia", 0.83, -77.64, 2900),
 "Nairobi": ("Global reference", "Tropical highland, Kenya", -1.29, 36.82, 1795),
 "Sorriso": ("Global reference", "Tropical cropland (soy), Brazil", -12.54, -55.71, 380),
 "Des Moines": ("Global reference", "Humid temperate (maize), USA", 41.60, -93.61, 290),
 "Ludhiana": ("Global reference", "Irrigated semi-arid, India", 30.90, 75.85, 247),
 "Niamey": ("Global reference", "Sahel, Niger", 13.51, 2.11, 220),
 "Can Tho": ("Global reference", "Tropical delta (rice), Vietnam", 10.03, 105.78, 2),
 "Mendoza": ("Global reference", "Arid irrigated (vineyards), Argentina", -32.89, -68.84, 750),
 "Fallon": ("Global reference", "Irrigated desert, USA", 39.47, -118.78, 1240),
 "Ventaquemada": ("Andean potato zone", "Andean potato zone, Boyaca (Colombia)", 5.37, -73.52, 2650),
 "Huancayo": ("Andean potato zone", "Andean potato zone, Junin (Peru)", -12.07, -75.21, 3260),
 "Puno": ("Andean potato zone", "Altiplano potato zone, Puno (Peru)", -15.84, -70.02, 3830),
}

def clean(df):
    """NaN/inf -> None so the JSON is valid."""
    df = df.replace([np.inf, -np.inf], np.nan)
    return df.astype(object).where(df.notna(), None)

def site_of(lat, lon):
    for n, v in SITES.items():
        if abs(v[2] - lat) < 0.01 and abs(v[3] - lon) < 0.01: return n
    raise ValueError(f"no site at {lat},{lon}")

def build():
    T = {}
    elev = {}
    p = DATA / "appeears_topo.csv"
    if p.exists():
        tp = pd.read_csv(p); c = [x for x in tp.columns if "DEM" in x.upper()][0]
        elev = tp.groupby("ID")[c].first().to_dict()
    T["sites"] = (pd.DataFrame([{"site": n, "grp": v[0], "zone": v[1], "lat": v[2], "lon": v[3], "elev_approx_m": v[4],
                                 "elev_srtm_m": elev.get(n)} for n, v in SITES.items()]), ["site"])
    rows = []
    for f in sorted(DATA.glob("power_*_20010101_20251231.csv")):
        m = re.match(r"power_(-?[\d.]+)_(-?[\d.]+)_", f.name)
        n = site_of(float(m.group(1)), float(m.group(2)))
        d = pd.read_csv(f, parse_dates=["fecha"]).rename(columns={"fecha": "date"})
        d.columns = [c.lower() for c in d.columns]; d.insert(0, "site", n); rows.append(d)
    T["power_daily"] = (pd.concat(rows), ["site", "date"])
    im = pd.read_csv(DATA / "imerg_final_daily_allvars.csv", parse_dates=["date"]); im.columns = [c.lower() for c in im.columns]
    T["imerg_daily"] = (im, ["site", "date"])
    rm = pd.read_csv(DATA / "platform_rain_monthly.csv", parse_dates=["month"]); rm.columns = [c.lower() for c in rm.columns]
    T["rain_monthly"] = (rm, ["site", "month"])
    rs = pd.read_csv(DATA / "platform_rain_sites.csv").rename(columns={"Unnamed: 0": "site"})
    rs.columns = [re.sub(r"[^a-z0-9]+", "_", c.lower().replace("%", "pct").replace("(", "_").replace("|", "_").replace("<", "lt")).strip("_") for c in rs.columns]
    rs = rs.rename(columns={"p_wet_wet": "p_wet_wet"})
    T["rain_sites"] = (rs, ["site"])
    mp = DATA / "master_monthly.csv"
    if mp.exists():
        mm = pd.read_csv(mp, parse_dates=["month"]); mm.columns = [c.lower() for c in mm.columns]
        T["master_monthly"] = (mm, ["site", "month"])
    for k, (df, _) in T.items():
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]): df[c] = df[c].dt.strftime("%Y-%m-%d")
    return T

def post(table, df, key_cols, key, batch=1000):
    h = {"apikey": key, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}
    if key.startswith("eyJ"): h["Authorization"] = f"Bearer {key}"     # legacy JWT keys also need this header
    url = f"{URL}/rest/v1/{table}?on_conflict={','.join(key_cols)}"
    recs = clean(df).to_dict("records")
    for i in range(0, len(recs), batch):
        r = requests.post(url, headers=h, data=json.dumps(recs[i:i + batch], allow_nan=False), timeout=120)
        if not r.ok: raise RuntimeError(f"{table}: HTTP {r.status_code} {r.text[:300]}")
    print(f"  {table}: {len(recs)} rows uploaded")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    T = build()
    print("Tables ready:"); [print(f"  {k}: {len(v[0])} rows, {len(v[0].columns)} columns") for k, v in T.items()]
    if a.dry_run: sys.exit(0)
    key = os.environ.get("SUPABASE_SECRET_KEY") or getpass.getpass("Supabase secret key (hidden): ").strip()
    for k in ["sites", "power_daily", "imerg_daily", "rain_monthly", "rain_sites", "master_monthly"]:   # sites first (foreign keys)
        if k in T: post(k, T[k][0], T[k][1], key)
    print("done")

"""Climate similarity to the 12 reference sites and a confidence flag for any point.

Why: our findings and models are built on 12 reference sites. For a new point we can only trust them
as far as its climate resembles one of those sites. This module turns that into a visible flag.

How: a point is described by its POWER monthly climatology (12 months of mean temperature, rainfall,
ET0, plus the annual values). Distance to each reference site is a standardized Euclidean distance over
those features (z-scored with the spread across the 12 sites), so that temperature and rainfall weigh
the same. The nearest site is the "sister site"; the distance gives the confidence flag.

Thresholds (alta / media / baja) are assumptions chosen so that each reference site is 'alta' with itself
and typically 'media' with its nearest neighbour: see calibrate() and adjust if the sample changes.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import climate_tools as ct

ROOT = Path(__file__).resolve().parent.parent
REF = {"Ipiales": (0.83, -77.64), "Nairobi": (-1.29, 36.82), "Sorriso": (-12.54, -55.71), "Des Moines": (41.60, -93.61),
       "Ludhiana": (30.90, 75.85), "Niamey": (13.51, 2.11), "Can Tho": (10.03, 105.78), "Mendoza": (-32.89, -68.84),
       "Fallon": (39.47, -118.78), "Ventaquemada": (5.37, -73.52), "Huancayo": (-12.07, -75.21), "Puno": (-15.84, -70.02)}
THRESH = {"alta": 0.4, "media": 0.8}     # standardized distance; above 'media' -> 'baja'
# Calibration with the 12 sites (2001-2025): the same site seen through a different decade scores ~0.2;
# Huancayo-Puno 0.14 (both altiplano), Mendoza-Fallon 0.49 (both arid irrigated), Ipiales-Ventaquemada 0.75,
# Des Moines-Fallon 0.95 (different climates). Nairobi-Mendoza 0.70 is a known weak spot of a 12-site sample.


def features(pw, lat, elev):
    """Climate fingerprint of a point from a POWER daily table (any length >= 1 year)."""
    et0 = ct.et0_fao56(pw, lat, elev)
    m = pd.DataFrame({"t": pw["T2M"], "r": pw["PRECTOTCORR"], "e": et0}).resample("MS").agg({"t": "mean", "r": "sum", "e": "sum"})
    clim = m.groupby(m.index.month).mean()                       # 12 x 3 climatology
    if lat < 0:                                                  # align seasons: start the year in July for the south
        clim = pd.concat([clim.loc[7:], clim.loc[:6]])
    f = {}
    for i, (_, row) in enumerate(clim.iterrows()):
        f[f"t{i:02d}"], f[f"r{i:02d}"] = row.t, row.r
    f["t_year"], f["t_range"] = clim.t.mean(), clim.t.max() - clim.t.min()
    f["r_year"], f["aridity"] = clim.r.sum(), clim.r.sum() / max(clim.e.sum(), 1)
    f["dry_months"] = int((clim.r < 0.5 * clim.e / 1.0).sum())   # months with rain < half of ET0
    return pd.Series(f)


def reference_table(data_dirs=("data", "../data"), elev=None):
    """Fingerprints of the 12 reference sites (elev: dict site -> metres, else approximate)."""
    el = elev or {"Ipiales": 2891, "Nairobi": 1666, "Sorriso": 350, "Des Moines": 271, "Ludhiana": 247, "Niamey": 201,
                  "Can Tho": 2, "Mendoza": 765, "Fallon": 1214, "Ventaquemada": 2618, "Huancayo": 3248, "Puno": 3823}
    rows = {}
    for n, (la, lo) in REF.items():
        pw = ct.load_csv(ct.find_csv(la, lo, list(data_dirs)))
        rows[n] = features(pw, la, el[n])
    return pd.DataFrame(rows).T


class Similarity:
    def __init__(self, ref):
        self.ref = ref
        self.mu, self.sd = ref.mean(), ref.std(ddof=0).replace(0, 1)
        self.z = (ref - self.mu) / self.sd

    def rank(self, f):
        zf = (f - self.mu) / self.sd
        d = np.sqrt(((self.z - zf) ** 2).mean(axis=1))            # mean over features -> comparable across feature counts
        return d.sort_values()

    def flag(self, f):
        d = self.rank(f)
        best, dist = d.index[0], float(d.iloc[0])
        level = "alta" if dist <= THRESH["alta"] else ("media" if dist <= THRESH["media"] else "baja")
        return {"sister_site": best, "distance": round(dist, 2), "confidence": level,
                "second": d.index[1], "second_distance": round(float(d.iloc[1]), 2),
                "note": {"alta": "Clima muy parecido a un sitio de referencia: los hallazgos aplican.",
                         "media": "Clima parcialmente parecido: usar los resultados como orientacion.",
                         "baja": "Ningun sitio de referencia se parece: los resultados no estan validados aqui."}[level]}


def calibrate(sim):
    """Leave-one-out: distance from each reference site to its nearest *other* site. Guides THRESH."""
    out = {}
    for n in sim.ref.index:
        d = sim.rank(sim.ref.loc[n]).drop(n)
        out[n] = (d.index[0], round(float(d.iloc[0]), 2))
    return pd.DataFrame(out, index=["nearest_other", "distance"]).T

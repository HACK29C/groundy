"""Crop suitability and rotation comparison -- transparent, rule-based (NOT machine learning).

What it does
  1. Crop suitability from monthly NASA POWER climate, with the FAO EcoCrop method:
     for every possible planting month, the growing season (cycle length) must stay inside the crop's
     temperature range (trapezoid: 0 outside the absolute limits, 1 inside the optimum) and its seasonal
     rainfall inside the rainfall range. suitability = temperature score x rainfall score (0..1).
  2. Reliability = share of years (2001-2025) in which the best planting month reaches suitability >= 0.5.
  3. Rotation strategies (3-year sequences) are compared on climate feasibility, reliability and simple
     agronomic rules (no repeated botanical family, legume present, family diversity).

Deliberate limits (shown to the user, never hidden)
  * Soil (pH, texture, drainage), pests, markets and irrigation are NOT evaluated: pH ranges are in the
    crop table so the farmer can compare them with a soil test.
  * EcoCrop gives broad, generic ranges. Its altitude limit is NOT used (potato: 2800 m in EcoCrop, but it is
    grown above 3800 m in the altiplano with native varieties); temperature already carries that information.
  * POWER is a ~50 km model grid, so frost days are an indicator only and are reported, not scored.
  * The weights of the final score are assumptions: ranking_robustness() shows how stable the ranking is.

Data: data/crop_requirements.csv (FAO EcoCrop). Climate: NASA POWER daily CSV (columns of climate_tools.VARS).
"""
from pathlib import Path
import numpy as np
import pandas as pd

import climate_tools as ct

CROPS_CSV = Path(__file__).resolve().parent.parent / "data" / "crop_requirements.csv"

STRATEGIES = {   # 3-year sequences (editable). A = the usual practice used as baseline.
    "A. Papa continua (practica comun)": ["papa", "papa", "papa"],
    "B. Papa - cebada - haba":           ["papa", "cebada", "haba"],
    "C. Papa - oca - quinua":            ["papa", "oca", "quinua"],
    "D. Papa - arveja - trebol rojo":    ["papa", "arveja", "trebol"],
    "E. Papa - maiz - frijol":           ["papa", "maiz", "frijol"],
}
WEIGHTS = {"climate": 0.40, "reliability": 0.20, "family_break": 0.20, "legume": 0.10, "diversity": 0.10}
MONTHS_ES = ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def load_crops(path=None):
    return pd.read_csv(path or CROPS_CSV).set_index("crop_id")


def trap(x, a, b, c, d):
    """Trapezoid score: 0 at or beyond a and d (absolute limits), 1 between b and c (optimum), linear in between."""
    x = np.asarray(x, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where((x <= a) | (x >= d), 0.0, np.nan)
        out = np.where((x > a) & (x < b), (x - a) / (b - a), out)
        out = np.where((x >= b) & (x <= c), 1.0, out)
        out = np.where((x > c) & (x < d), (d - x) / (d - c), out)
    return out


LAPSE = 6.5 / 1000      # deg C per metre (standard atmosphere); an approximation, valid for free-air cooling


def lapse_adjust(pw, elev_grid, elev_site):
    """Shift POWER temperatures from the model-grid elevation to the site elevation.

    POWER is a coarse grid whose mean elevation can be far above a valley floor (or below a peak), so its
    temperatures are biased in mountains. elev_grid is printed in the header of the POWER API response
    ("Elevation"); elev_site is the SRTM elevation. Rainfall is NOT corrected (no simple rule exists).
    """
    d = LAPSE * (elev_grid - elev_site)
    out = pw.copy()
    for c in ["T2M", "T2M_MAX", "T2M_MIN"]:
        out[c] = out[c] + d
    return out


def monthly_from_power(pw, lat, elev):
    """Monthly climate table from a POWER daily DataFrame."""
    et0 = ct.et0_fao56(pw, lat, elev)
    return pd.DataFrame({
        "tmean": pw["T2M"].resample("MS").mean(),
        "tmin_mean": pw["T2M_MIN"].resample("MS").mean(),
        "rain": pw["PRECTOTCORR"].resample("MS").sum(min_count=20),
        "et0": et0.resample("MS").sum(min_count=20)})


def _window_sums(v, M):
    n = len(v) - M + 1
    return np.array([v[i:i + M].sum() for i in range(n)])


def _window_min(v, M):
    n = len(v) - M + 1
    return np.array([v[i:i + M].min() for i in range(n)])


def season_series(crop, clim, pw=None, rainfed=True):
    """Suitability of one crop for every possible planting month of the record (index = planting month)."""
    M = max(1, int(round(crop["cycle_used_d"] / 30)))
    sT = _window_min(trap(clim["tmean"].values, crop.t_abs_min, crop.t_opt_min, crop.t_opt_max, crop.t_abs_max), M)
    rain_season = _window_sums(clim["rain"].values, M)
    sR = trap(rain_season, crop.rain_abs_min, crop.rain_opt_min, crop.rain_opt_max, crop.rain_abs_max) if rainfed else np.ones_like(sT)
    out = pd.DataFrame({"suit": sT * sR, "sT": sT, "sR": sR, "rain_season": rain_season}, index=clim.index[:len(sT)])
    if pw is not None and pd.notna(crop.t_kill):
        fm = (pw["T2M_MIN"] <= crop.t_kill).resample("MS").sum().reindex(clim.index).fillna(0).values
        out["frost_days"] = _window_sums(fm, M)
    return out


def summarize_crop(crop, series):
    """Best planting month, mean suitability, reliability across years, limiting factor."""
    s = series.assign(m=series.index.month)
    g = s.groupby("m").agg(suit=("suit", "mean"), sT=("sT", "mean"), sR=("sR", "mean"),
                           reliab=("suit", lambda x: float((x.dropna() >= 0.5).mean())),
                           rain=("rain_season", "mean"),
                           frost=("frost_days", "mean") if "frost_days" in s else ("suit", lambda x: np.nan))
    best = int(g["suit"].idxmax()); r = g.loc[best]
    limiting = "ninguno" if r.suit >= 0.8 else ("temperatura" if r.sT <= r.sR else "lluvia")
    return {"best_month": best, "best_month_es": MONTHS_ES[best], "suit": float(r.suit), "reliability": float(r.reliab),
            "temp_score": float(r.sT), "rain_score": float(r.sR), "limiting": limiting,
            "season_rain_mm": float(r.rain), "frost_days_season": float(r.frost), "cycle_months": int(round(crop["cycle_used_d"] / 30))}


def crop_table(clim, crops, pw=None, rainfed=True):
    rows = {cid: summarize_crop(c, season_series(c, clim, pw, rainfed)) for cid, c in crops.iterrows()}
    return pd.DataFrame(rows).T.astype({"suit": float, "reliability": float}).sort_values("suit", ascending=False)


def _components(seq, summ, crops):
    fam = [crops.loc[c, "family"] for c in seq]
    pairs = [(fam[i], fam[(i + 1) % len(fam)]) for i in range(len(fam))]     # cyclic: year 3 is followed by year 1
    return {"climate": float(np.mean([summ.loc[c, "suit"] for c in seq])),
            "reliability": float(np.mean([summ.loc[c, "reliability"] for c in seq])),
            "family_break": float(np.mean([a != b for a, b in pairs])),
            "legume": float(any(bool(crops.loc[c, "is_legume"]) for c in seq)),
            "diversity": len(set(fam)) / len(fam)}


def compare_strategies(summ, crops, strategies=None, weights=None):
    """Score and explain each rotation. Returns (table, notes). All numbers 0..100 except where stated."""
    strategies, weights = strategies or STRATEGIES, weights or WEIGHTS
    rows, notes = {}, {}
    for name, seq in strategies.items():
        c = _components(seq, summ, crops)
        score = 100 * sum(weights[k] * c[k] for k in weights)
        weakest = min(seq, key=lambda x: summ.loc[x, "suit"])
        rows[name] = {**{k: round(v, 2) for k, v in c.items()}, "score": round(score, 1),
                      "weakest_crop": weakest, "weakest_suit": round(float(summ.loc[weakest, "suit"]), 2)}
        n = []
        fams = [crops.loc[x, "family"] for x in seq]
        if c["family_break"] < 1: n.append(f"Repite la familia {max(set(fams), key=fams.count)} en anos consecutivos: mas presion de plagas y enfermedades del suelo (FAO recomienda rotar 3 o mas anos)")
        else: n.append("No repite familia botanica en anos consecutivos: corta ciclos de plagas y enfermedades")
        n.append("Incluye una leguminosa (fija nitrogeno)" if c["legume"] else "Sin leguminosa: depende mas de fertilizacion nitrogenada")
        s_w = float(summ.loc[weakest, "suit"])
        if s_w < 0.5: n.append(f"Cultivo limitante: {weakest} (aptitud {s_w:.2f}, limita {summ.loc[weakest, 'limiting']})")
        low = [x for x in seq if summ.loc[x, "reliability"] < 0.6]
        if low: n.append("Poco confiable entre anos: " + ", ".join(sorted(set(low))))
        n.append("No evalua suelo (pH, textura, drenaje), plagas locales, mercado ni riego")
        notes[name] = n
    return pd.DataFrame(rows).T.sort_values("score", ascending=False), notes


def ranking_robustness(summ, crops, strategies=None, n=2000, seed=0):
    """Share of random weightings (Dirichlet) under which each strategy ranks first. Tests the weight assumption."""
    strategies = strategies or STRATEGIES
    comp = {k: _components(v, summ, crops) for k, v in strategies.items()}
    keys = list(WEIGHTS); rng = np.random.default_rng(seed)
    wins = dict.fromkeys(strategies, 0)
    for w in rng.dirichlet(np.ones(len(keys)), n):
        sc = {k: sum(wi * comp[k][c] for wi, c in zip(w, keys)) for k in strategies}
        wins[max(sc, key=sc.get)] += 1
    return pd.Series(wins).div(n).sort_values(ascending=False).rename("share_first")

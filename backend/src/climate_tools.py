"""Climate statistics and water-balance tools for NASA POWER daily data.

Reusable by notebooks now and by the application back end later.
Input: daily DataFrame with the POWER columns
T2M_MAX, T2M_MIN, T2M, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN and a DatetimeIndex.
ET0 follows FAO Irrigation and Drainage Paper 56 (Allen et al., 1998).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

VARS = ["T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]


# ------------------------------------------------------------------ loading
def find_csv(lat, lon, dirs, start="20010101", end="20251231"):
    name = f"power_{lat}_{lon}_{start}_{end}.csv"
    for d in dirs:
        p = Path(d) / name
        if p.exists():
            return p
    return None


def load_csv(path):
    return pd.read_csv(path, parse_dates=["fecha"], index_col="fecha").rename_axis("date")


# ------------------------------------------------------------------ ET0 (FAO-56)
def es(T):
    """Saturation vapour pressure (kPa) at temperature T (deg C)."""
    return 0.6108 * np.exp(17.27 * T / (T + 237.3))


def extraterrestrial_radiation(lat, doy):
    """Ra (MJ/m2/day), FAO-56 eq. 21."""
    phi = np.radians(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def et0_fao56(df, lat, elev):
    """Daily reference evapotranspiration (mm/day), Penman-Monteith FAO-56.

    ea = RHmean/100 * (es(Tmax)+es(Tmin))/2 (eq. 19 with mean RH). Rs = ALLSKY_SFC_SW_DWN.
    """
    tmax, tmin, tmed = df["T2M_MAX"], df["T2M_MIN"], df["T2M"]
    rs, u2, rh = df["ALLSKY_SFC_SW_DWN"], df["WS2M"], df["RH2M"]
    doy = df.index.dayofyear.values
    P = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
    gamma = 0.000665 * P
    delta = 4098 * es(tmed) / (tmed + 237.3) ** 2
    e_s = (es(tmax) + es(tmin)) / 2
    e_a = rh / 100 * e_s
    ra = extraterrestrial_radiation(lat, doy)
    rso = (0.75 + 2e-5 * elev) * ra
    rns = (1 - 0.23) * rs
    ratio = np.clip(rs / rso, 0.3, 1.0)
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 \
        * (0.34 - 0.14 * np.sqrt(e_a)) * (1.35 * ratio - 0.35)
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * 900 / (tmed + 273) * u2 * (e_s - e_a)
    den = delta + gamma * (1 + 0.34 * u2)
    return (num / den).clip(lower=0).rename("ET0")


def aridity_class(pet_ratio):
    """UNEP aridity classes from P/ET0."""
    if pet_ratio < 0.05: return "hyper-arid"
    if pet_ratio < 0.20: return "arid"
    if pet_ratio < 0.50: return "semi-arid"
    if pet_ratio < 0.65: return "dry sub-humid"
    return "humid"


# ------------------------------------------------------------------ seasonality / anomalies
def daily_climatology(s, window=15):
    """Smoothed (circular) mean annual cycle by day of year."""
    c = s.groupby(s.index.dayofyear).mean().reindex(range(1, 367)).interpolate()
    ext = pd.concat([c.iloc[-window:], c, c.iloc[:window]])
    out = ext.rolling(2 * window + 1, center=True).mean().iloc[window:-window]
    out.index = range(1, 367)
    return out


def anomalies(df):
    out = {}
    for c in df.columns:
        clim = daily_climatology(df[c])
        out[c] = df[c] - clim.reindex(df.index.dayofyear).values
    return pd.DataFrame(out, index=df.index)


def seasonal_share(s_or_df, freq=None):
    """Share of variance explained by the mean annual cycle (daily, or monthly if freq='MS')."""
    df = s_or_df.to_frame() if isinstance(s_or_df, pd.Series) else s_or_df
    if freq:
        agg = {c: ("sum" if c == "PRECTOTCORR" else "mean") for c in df.columns}
        df = df.resample(freq).agg(agg)
        res = {}
        for c in df.columns:
            clim = df[c].groupby(df.index.month).transform("mean")
            res[c] = 1 - ((df[c] - clim).var() / df[c].var())
        return pd.Series(res)
    an = anomalies(df)
    return 1 - an.var() / df.var()


def kruskal_by_month(s):
    """Kruskal-Wallis test of equal distribution across calendar months; returns H, p, eta2_H."""
    groups = [g.values for _, g in s.groupby(s.index.month)]
    H, p = stats.kruskal(*groups)
    n, k = len(s), len(groups)
    return H, p, (H - k + 1) / (n - k)


# ------------------------------------------------------------------ dependence / persistence
def acf(x, nlags):
    x = np.asarray(x, float)
    x = x - x.mean()
    d = (x * x).sum()
    return np.array([1.0] + [(x[:-k] * x[k:]).sum() / d for k in range(1, nlags + 1)])


def ljung_box(x, lags):
    x = np.asarray(x, float)
    n = len(x)
    r = acf(x, lags)[1:]
    Q = n * (n + 2) * np.sum(r ** 2 / (n - np.arange(1, lags + 1)))
    return Q, stats.chi2.sf(Q, lags)


def block_bootstrap_corr(x, y, block=30, B=1000, seed=0, method="pearson"):
    """Moving-block bootstrap CI of a correlation, valid under serial dependence."""
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x), np.asarray(y)
    n = len(x)
    nb = int(np.ceil(n / block))
    out = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, n - block, nb)
        idx = (starts[:, None] + np.arange(block)).ravel()[:n]
        xs, ys = x[idx], y[idx]
        if method == "spearman":
            xs, ys = stats.rankdata(xs), stats.rankdata(ys)
        out[b] = np.corrcoef(xs, ys)[0, 1]
    return np.percentile(out, [2.5, 97.5])


# ------------------------------------------------------------------ trends / change
def trend_test(years, values):
    """Mann-Kendall (via Kendall tau vs time) and Theil-Sen slope with 95% CI."""
    tau, p = stats.kendalltau(years, values)
    slope, intercept, lo, hi = stats.theilslopes(values, years, 0.95)
    return {"tau": tau, "p": p, "sen_slope_per_yr": slope, "ci_lo": lo, "ci_hi": hi, "intercept": intercept}


def period_shift(values, split_year):
    """Mann-Whitney U test between early and late periods and median difference."""
    a = values[values.index < split_year]
    b = values[values.index >= split_year]
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"median_early": a.median(), "median_late": b.median(),
            "diff": b.median() - a.median(), "p": p, "n_early": len(a), "n_late": len(b)}


# ------------------------------------------------------------------ rainfall regime
def wet_day_stats(rain, thr=1.0):
    wet = rain[rain >= thr]
    shape, loc, scale = stats.gamma.fit(wet, floc=0)
    ks = stats.kstest(wet, "gamma", args=(shape, 0, scale))
    return {"wet_day_freq": len(wet) / len(rain), "mean_wet_intensity": wet.mean(),
            "median_wet_intensity": wet.median(), "p95_wet": wet.quantile(.95),
            "gamma_shape": shape, "gamma_scale": scale, "ks_stat": ks.statistic}


def spell_lengths(rain, thr=1.0):
    """Lengths of all runs of consecutive days with rain < thr."""
    dry = (rain.values < thr).astype(int)
    runs, c = [], 0
    for v in dry:
        if v: c += 1
        elif c: runs.append(c); c = 0
    if c: runs.append(c)
    return np.array(runs)


def annual_max_return_levels(ann_max, periods=(5, 10, 25), B=1000, seed=0):
    """Gumbel fit to annual maxima, return levels with parametric-bootstrap 95% CI."""
    loc, scale = stats.gumbel_r.fit(ann_max)
    rng = np.random.default_rng(seed)
    res = {}
    boots = []
    for _ in range(B):
        sample = stats.gumbel_r.rvs(loc, scale, size=len(ann_max), random_state=rng)
        l, s = stats.gumbel_r.fit(sample)
        boots.append([stats.gumbel_r.ppf(1 - 1 / T, l, s) for T in periods])
    boots = np.array(boots)
    for i, T in enumerate(periods):
        res[T] = (stats.gumbel_r.ppf(1 - 1 / T, loc, scale),
                  np.percentile(boots[:, i], 2.5), np.percentile(boots[:, i], 97.5))
    return res, (loc, scale)


# ------------------------------------------------------------------ predictability baselines
def monthly_series(df, col):
    how = "sum" if col == "PRECTOTCORR" else "mean"
    return df[col].resample("MS").agg(how)


def loyo_skill(m):
    """Leave-one-year-out comparison on a monthly series.

    climatology: calendar-month mean from the other years
    persistence: last month's value
    clim+AR1   : climatology + beta * previous-month anomaly (beta fitted on training years)
    Skill = 1 - MSE_model / MSE_climatology (positive = better than climatology).
    """
    m = m.copy()
    years = sorted(set(m.index.year))
    preds = {"climatology": [], "persistence": [], "clim+AR1": []}
    obs = []
    for y in years:
        train = m[m.index.year != y]
        clim = train.groupby(train.index.month).mean()
        tr_anom = train - clim.reindex(train.index.month).values
        prev = tr_anom.shift(1)
        ok = prev.notna() & ((train.index - pd.offsets.MonthBegin(1)).isin(train.index))
        beta = (tr_anom[ok] * prev[ok]).sum() / (prev[ok] ** 2).sum()
        test = m[m.index.year == y]
        for t, v in test.items():
            tprev = t - pd.offsets.MonthBegin(1)
            if tprev not in m.index:
                continue
            c = clim[t.month]
            cprev = clim[tprev.month]
            obs.append(v)
            preds["climatology"].append(c)
            preds["persistence"].append(m[tprev])
            preds["clim+AR1"].append(c + beta * (m[tprev] - cprev))
    obs = np.array(obs)
    rows = {}
    mse_c = np.mean((obs - np.array(preds["climatology"])) ** 2)
    for k, v in preds.items():
        v = np.array(v)
        rows[k] = {"MAE": np.mean(np.abs(obs - v)), "RMSE": np.sqrt(np.mean((obs - v) ** 2)),
                   "R2": 1 - np.sum((obs - v) ** 2) / np.sum((obs - obs.mean()) ** 2),
                   "skill_vs_clim": 1 - np.mean((obs - v) ** 2) / mse_c}
    return pd.DataFrame(rows).T


def q1_vs_rest(rain, B=5000, seed=1):
    """Does Jan-Mar rainfall relate to Apr-Dec rainfall? Pearson/Spearman, bootstrap CI, permutation p."""
    q1 = rain[rain.index.month <= 3]
    rest = rain[rain.index.month > 3]
    q1 = q1.groupby(q1.index.year).sum()
    rest = rest.groupby(rest.index.year).sum()
    r, p = stats.pearsonr(q1, rest)
    rho, ps = stats.spearmanr(q1, rest)
    rng = np.random.default_rng(seed)
    n = len(q1)
    boot = [np.corrcoef(q1.values[i], rest.values[i])[0, 1]
            for i in (rng.integers(0, n, n) for _ in range(B))]
    perm = [np.corrcoef(rng.permutation(q1.values), rest.values)[0, 1] for _ in range(B)]
    p_perm = (np.sum(np.abs(perm) >= abs(r)) + 1) / (B + 1)
    return {"pearson_r": r, "pearson_p": p, "spearman_rho": rho, "spearman_p": ps,
            "boot_lo": np.percentile(boot, 2.5), "boot_hi": np.percentile(boot, 97.5),
            "perm_p": p_perm, "r2": r ** 2, "n": n}


# ------------------------------------------------------------------ site summary
def annual_table(df, lat, elev):
    et0 = et0_fao56(df, lat, elev)
    y = df.index.year
    rain = df["PRECTOTCORR"]
    t = pd.DataFrame({
        "rain_mm": rain.groupby(y).sum(),
        "ET0_mm": et0.groupby(y).sum(),
        "Tmean_C": df["T2M"].groupby(y).mean(),
        "Tmax_C": df["T2M_MAX"].groupby(y).mean(),
        "Tmin_C": df["T2M_MIN"].groupby(y).mean(),
        "RH_%": df["RH2M"].groupby(y).mean(),
        "wind_ms": df["WS2M"].groupby(y).mean(),
        "SW_MJ": df["ALLSKY_SFC_SW_DWN"].groupby(y).mean(),
        "wet_days": (rain >= 1).groupby(y).sum(),
        "heavy_days_>12.7mm": (rain > 12.7).groupby(y).sum(),
        "max_daily_rain_mm": rain.groupby(y).max(),
        "frost_days_Tmin<=2C": (df["T2M_MIN"] <= 2).groupby(y).sum(),
        "frost_days_Tmin<=0C": (df["T2M_MIN"] <= 0).groupby(y).sum(),
        "longest_dry_spell_d": [spell_lengths(rain[y == k]).max() if (rain[y == k] < 1).any() else 0
                                for k in sorted(set(y))],
    })
    t["P/ET0"] = t.rain_mm / t.ET0_mm
    t["P-ET0_mm"] = t.rain_mm - t.ET0_mm
    return t, et0


def site_summary(df, lat, elev):
    at, et0 = annual_table(df, lat, elev)
    an = anomalies(df[VARS])
    monthly_share = seasonal_share(df[VARS], "MS")
    P, E = at["rain_mm"], at["ET0_mm"]
    var_pe = (P - E).var()
    lag1 = lambda c: an[c].autocorr(1)
    return {
        "rain_mm_yr": P.mean(), "rain_CV_%": 100 * P.std() / P.mean(),
        "ET0_mm_yr": E.mean(), "ET0_CV_%": 100 * E.std() / E.mean(),
        "P/ET0": P.mean() / E.mean(), "aridity_class": aridity_class(P.mean() / E.mean()),
        "share_Var(P-ET0)_from_P_%": 100 * P.var() / var_pe if var_pe > 0 else np.nan,
        "Tmean_C": df["T2M"].mean(),
        "seasonal_range_Tmean_C": (lambda m: m.max() - m.min())(df["T2M"].groupby(df.index.month).mean()),
        "frost_days_Tmin<=2C_yr": at["frost_days_Tmin<=2C"].mean(),
        "min_Tmin_C": df["T2M_MIN"].min(),
        "wet_day_freq_%": 100 * (df["PRECTOTCORR"] >= 1).mean(),
        "longest_dry_spell_mean_d": at["longest_dry_spell_d"].mean(),
        "monthly_seasonal_share_rain": monthly_share["PRECTOTCORR"],
        "monthly_seasonal_share_Tmin": monthly_share["T2M_MIN"],
        "lag1_anom_rain": lag1("PRECTOTCORR"), "lag1_anom_Tmean": lag1("T2M"),
        "corr_anom_rain_SW": an["PRECTOTCORR"].corr(an["ALLSKY_SFC_SW_DWN"]),
        "corr_anom_rain_RH": an["PRECTOTCORR"].corr(an["RH2M"]),
        "corr_anom_Tmax_Tmin": an["T2M_MAX"].corr(an["T2M_MIN"]),
    }

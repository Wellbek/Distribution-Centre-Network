"""Calendar, generated demand history, Poisson-Gamma model with exposure (Lecture 2), day sampler."""
from datetime import date, timedelta

import numpy as np

from . import config as C
from .world import HIST_DAYS, HIST_START

PLAN_START = date(2026, 11, 1)
PLAN_DAYS = 365

# Korean public holidays (approximate, fictional world); big = Seollal and Chuseok blocks
HOLIDAYS = {
    "2025-10-03": 0, "2025-10-05": 1, "2025-10-06": 1, "2025-10-07": 1, "2025-10-08": 1, "2025-10-09": 0,
    "2025-12-25": 0, "2026-01-01": 0, "2026-02-16": 1, "2026-02-17": 1, "2026-02-18": 1, "2026-03-01": 0,
    "2026-03-02": 0, "2026-05-05": 0, "2026-05-24": 0, "2026-05-25": 0, "2026-06-03": 0, "2026-06-06": 0,
    "2026-08-15": 0, "2026-08-17": 0, "2026-09-24": 1, "2026-09-25": 1, "2026-09-26": 1, "2026-10-03": 0,
    "2026-10-09": 0, "2026-12-25": 0, "2027-01-01": 0, "2027-02-06": 1, "2027-02-07": 1, "2027-02-08": 1,
    "2027-02-09": 1, "2027-03-01": 0, "2027-05-05": 0, "2027-05-13": 0, "2027-06-06": 0, "2027-08-15": 0,
    "2027-08-16": 0, "2027-09-14": 1, "2027-09-15": 1, "2027-09-16": 1, "2027-10-03": 0, "2027-10-04": 0,
}

# Truth: weekday profile per type (Mon..Sun), holiday response per type
DOW = np.array([
    [0.95, 0.95, 0.97, 0.98, 1.03, 1.12, 1.10],  # residential
    [1.08, 1.08, 1.08, 1.07, 1.05, 0.70, 0.62],  # office
    [1.00, 1.00, 1.00, 1.00, 1.04, 1.02, 0.98],  # mixed
    [0.95, 0.95, 0.95, 0.97, 1.05, 1.12, 1.10],  # roadside
])
EVE = np.array([1.30, 1.10, 1.25, 1.35])
HOLI = np.array([1.12, 0.55, 1.00, 1.40])
SUMMER = np.array([0.12, 0.08, 0.12, 0.20])


def calendar(start, n):
    # Day features: weekday, day of year, holiday, eve, big
    days = [start + timedelta(i) for i in range(n)]
    iso = [d.isoformat() for d in days]
    hol = np.array([s in HOLIDAYS for s in iso])
    big = np.array([HOLIDAYS.get(s, 0) == 1 for s in iso])
    nxt = [(d + timedelta(1)).isoformat() for d in days]
    eve = np.array([(s not in HOLIDAYS) and (x in HOLIDAYS) for s, x in zip(iso, nxt)])
    eve_big = np.array([e and HOLIDAYS.get(x, 0) == 1 for e, x in zip(eve, nxt)])
    return dict(date=iso, dow=np.array([d.weekday() for d in days]), doy=np.array([d.timetuple().tm_yday for d in days]),
                hol=hol, big=big, eve=eve, eve_big=eve_big)


def true_multiplier(cal):
    # Type x day multiplier of the generator (the truth the planner never sees)
    season = 1 + SUMMER[:, None] * np.exp(-((cal["doy"][None, :] - 205) / 30.0) ** 2) - 0.04 * np.cos(2 * np.pi * (cal["doy"][None, :] - 15) / 365)
    m = DOW[:, cal["dow"]] * season
    eve_f = np.where(cal["eve_big"], EVE[:, None] ** 1.5, EVE[:, None])
    m = np.where(cal["eve"][None, :], m * eve_f, m)
    hol_f = np.where(cal["big"], HOLI[:, None] ** 1.3, HOLI[:, None])
    return np.where(cal["hol"][None, :], m * hol_f, m)


def chain_shocks(n, rng, phi=0.6, sigma=0.06):
    # Chain-wide AR(1) factor on the log scale (weather, mood), plus rare storm days
    z = np.zeros(n)
    for i in range(1, n):
        z[i] = phi * z[i - 1] + rng.normal(0, sigma)
    storm = rng.random(n) < 0.015
    return np.exp(z) * np.where(storm, 0.85, 1.0)


def make_history(world, rng):
    """Generate demand_history: cages per store and day, -1 where the store was not open."""
    st = world["stores"]
    cal = calendar(HIST_START, HIST_DAYS)
    mult = true_multiplier(cal)[st["type"]]
    shock = chain_shocks(HIST_DAYS, rng)
    noise = rng.gamma(8.0, 1 / 8.0, size=mult.shape)  # store-day overdispersion: the model is mildly misspecified
    lam = st["rate_true"][:, None] * mult * shock[None, :] * noise
    y = rng.poisson(lam).astype(np.int16)
    t = np.arange(HIST_DAYS)[None, :]
    open_ = (t >= st["opened"][:, None]) & (t < st["closed"][:, None])
    y[~open_] = -1
    return dict(y=y, cal=cal, shock_true=shock)


def _design(cal):
    # Calendar regression basis: weekday dummies, two annual harmonics, holiday terms
    doy = cal["doy"] / 365.0
    cols = [cal["dow"] == d for d in range(7)]
    cols += [np.sin(2 * np.pi * doy), np.cos(2 * np.pi * doy), np.sin(4 * np.pi * doy), np.cos(4 * np.pi * doy)]
    cols += [cal["eve"], cal["eve_big"], cal["hol"], cal["big"]]
    return np.column_stack(cols).astype(float)


def fit(world, hist):
    """Fit exposure per type and day, the chain-shock AR(1), and each store's Gamma posterior."""
    st, y = world["stores"], hist["y"]
    obs = y >= 0
    yy = np.where(obs, y, 0).astype(float)
    n_types = 4
    # Store means and type-day exposure by ratio estimation
    ybar = yy.sum(1) / np.maximum(obs.sum(1), 1)
    e = np.ones((n_types, y.shape[1]))
    for k in range(n_types):
        m = st["type"] == k
        num = yy[m].sum(0)
        den = (obs[m] * ybar[m][:, None]).sum(0)
        e[k] = num / np.maximum(den, 1e-9)
    # Split log exposure into calendar part and a shared chain shock
    X = _design(hist["cal"])
    beta = np.linalg.lstsq(X, np.log(e).T, rcond=None)[0]
    resid = np.log(e) - (X @ beta).T
    w = np.bincount(st["type"], minlength=n_types) / len(st["type"])
    shock = (w[:, None] * resid).sum(0)
    phi = float(np.corrcoef(shock[:-1], shock[1:])[0, 1])
    sig = float(np.std(shock[1:] - phi * shock[:-1]))
    # Exposure seen by each store; Gamma prior per type by empirical Bayes (moments of long-history stores)
    expo = e[st["type"]] * obs
    E_s, Y_s = expo.sum(1), yy.sum(1)
    a0, b0 = np.zeros(len(Y_s)), np.zeros(n_types)
    m_type = np.zeros(n_types)
    for k in range(n_types):
        m = (st["type"] == k)
        lng = m & (obs.sum(1) >= 300)
        r = Y_s[lng] / E_s[lng]
        mu = r.mean()
        var_true = max(r.var() - (r / E_s[lng]).mean(), 1e-3)
        m_type[k], b0[k] = mu, mu / var_true
        a0[m] = mu * b0[k]
    b0s = b0[st["type"]]
    # Store-day overdispersion beyond Poisson, as a Gamma multiplier with shape kappa
    fit_mu = (Y_s / np.maximum(E_s, 1e-9))[:, None] * e[st["type"]]
    res2 = ((yy - fit_mu) ** 2 - fit_mu)[obs].sum()
    kappa = float(max((fit_mu[obs] ** 2).sum() / max(res2, 1e-9), 1.0))
    return dict(beta=beta, phi=phi, sigma=sig, shock_hist=shock, e_hist=e, m_type=m_type,
                a0=a0, b0=b0s, b0_type=b0, a=a0 + Y_s, b=b0s + E_s, days_obs=obs.sum(1), kappa=kappa)


def calendar_multiplier(model, cal):
    # Fitted type x day calendar exposure for planning days
    return np.exp((_design(cal) @ model["beta"]).T)


def _classes(cal):
    # Calendar strata: holiday or eve, weekend, weekday
    return np.where(cal["hol"] | cal["eve"], 0, np.where(cal["dow"] >= 5, 1, 2))


LABELS = ["holiday or eve", "weekend", "weekday"]


def sample_days(model, world, n, seed, mask, exclude=()):
    """Draw n planning days from the posterior predictive, stratified by calendar class with weights.

    One posterior draw of the store rates per scenario set; chain shock, overdispersion and counts per day.
    """
    rng = np.random.default_rng(seed)
    cal = calendar(PLAN_START, PLAN_DAYS)
    cm = calendar_multiplier(model, cal)
    cls = _classes(cal)
    ok = np.array([d not in set(exclude) for d in cal["date"]])
    share = np.bincount(cls, minlength=3) / PLAN_DAYS
    alloc = np.maximum(1, np.round(share * n)).astype(int)
    alloc[2] = n - alloc[:2].sum()
    sd = model["sigma"] / np.sqrt(max(1 - model["phi"] ** 2, 1e-3))
    types = world["stores"]["type"][mask]
    a, b = model["a"][mask], model["b"][mask]
    lam = rng.gamma(a, 1 / b)
    days = []
    for c in range(3):
        pool = np.flatnonzero((cls == c) & ok)
        for i in np.sort(rng.choice(pool, size=alloc[c], replace=False)):
            shock = float(np.exp(rng.normal(0, sd)))
            mult = cm[types, i] * shock * rng.gamma(model["kappa"], 1 / model["kappa"], size=len(lam))
            q = rng.poisson(lam * mult)
            days.append(dict(date=cal["date"][i], label=LABELS[c], w=float(share[c] / alloc[c]), shock=shock,
                             chain=float(cm[:, i].mean() * shock), q=q.astype(float), q_mean=lam * cm[types, i] * shock))
    days.sort(key=lambda d: d["date"])
    return days


def average_day(model, world, mask):
    # One annual-average day: posterior mean rate times mean calendar exposure, no shock, no count noise
    cal = calendar(PLAN_START, PLAN_DAYS)
    cm = calendar_multiplier(model, cal).mean(1)
    types = world["stores"]["type"][mask]
    q = model["a"][mask] / model["b"][mask] * cm[types]
    return dict(date="average", label="annual average", w=1.0, shock=1.0, chain=1.0, q=q)


def peak_day(model, world, mask, seed):
    # The busiest calendar day of the planning year, drawn like any other day
    rng = np.random.default_rng(seed)
    cal = calendar(PLAN_START, PLAN_DAYS)
    cm = calendar_multiplier(model, cal)
    i = int(cm.mean(0).argmax())
    types = world["stores"]["type"][mask]
    lam = rng.gamma(model["a"][mask], 1 / model["b"][mask])
    q = rng.poisson(lam * cm[types, i] * rng.gamma(model["kappa"], 1 / model["kappa"], size=len(lam)))
    lab = "holiday eve" if cal["eve"][i] else "holiday" if cal["hol"][i] else "busiest day"
    return dict(date=cal["date"][i], label=f"peak ({lab})", w=1.0, shock=1.0, chain=float(cm[:, i].mean()), q=q.astype(float))


def replicate_history(model, world, hist, seed):
    # Posterior predictive check: replicated chain totals for the history calendar
    rng = np.random.default_rng(seed)
    st = world["stores"]
    obs = hist["y"] >= 0
    lam = rng.gamma(model["a"], 1 / model["b"])
    e = model["e_hist"][st["type"]]
    mult = rng.gamma(model["kappa"], 1 / model["kappa"], size=e.shape)
    y = rng.poisson(lam[:, None] * e * mult) * obs
    return y.sum(0)

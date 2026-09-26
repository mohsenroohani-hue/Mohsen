"""Count-model engine.

* NB2 (negative binomial) maximum likelihood for adequately populated outcomes.
* Firth-penalised Poisson (Jeffreys-prior bias reduction) for sparse outcomes such as
  fatal or type-specific KSI crashes, where ordinary ML is biased / separates.
* Moran eigenvector spatial filtering (ESF): eigenvectors of the doubly-centred
  k-nearest-neighbour connectivity matrix are added as synthetic covariates to soak
  up residual spatial autocorrelation (Griffith 2003; Chun 2008).
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from scipy.special import gammaln
from libpysal.weights import KNN
import esda

warnings.filterwarnings("ignore")


# --------------------------------------------------------------------- estimators
def fit_nb(y, X):
    """NB2 via statsmodels; returns dict or None if it fails."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    try:
        pois = sm.GLM(y, X, family=sm.families.Poisson()).fit()
        start = np.append(pois.params, 0.2)
    except Exception:
        start = None
    for method in ("newton", "bfgs", "nm"):
        try:
            r = sm.NegativeBinomial(y, X, loglike_method="nb2").fit(
                start_params=start, method=method, maxiter=2000, disp=0)
            bse = np.asarray(r.bse)
            if np.all(np.isfinite(bse[:-1])) and np.isfinite(r.llf):
                k = X.shape[1]
                mu = np.exp(X @ r.params[:k])
                alpha = r.params[-1]
                pear = (y - mu) / np.sqrt(mu + alpha * mu ** 2)
                return {"params": np.asarray(r.params[:k]), "bse": bse[:k], "llf": r.llf,
                        "k": k + 1, "alpha": alpha, "mu": mu, "pearson": pear, "est": "NB2"}
        except Exception:
            continue
    return None


def fit_firth_poisson(y, X, maxiter=200, tol=1e-8):
    """Firth (1993) bias-reduced Poisson regression, log link."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    b = np.zeros(k)
    b[0] = np.log(max(y.mean(), 1e-3))

    def pll(beta):
        eta = X @ beta
        mu = np.exp(np.clip(eta, -30, 30))
        info = X.T @ (X * mu[:, None])
        sign, logdet = np.linalg.slogdet(info)
        return np.sum(y * eta - mu - gammaln(y + 1)) + 0.5 * logdet, mu, info

    cur, mu, info = pll(b)
    for _ in range(maxiter):
        inv = np.linalg.pinv(info)
        h = mu * np.einsum("ij,jk,ik->i", X, inv, X)
        step = inv @ (X.T @ (y - mu + h / 2.0))
        t = 1.0
        while True:
            new, mu_n, info_n = pll(b + t * step)
            if new >= cur - 1e-10 or t < 1e-4:
                break
            t /= 2
        b = b + t * step
        conv = np.max(np.abs(t * step)) < tol
        cur, mu, info = new, mu_n, info_n
        if conv:
            break
    inv = np.linalg.pinv(info)
    llf = np.sum(y * (X @ b) - mu - gammaln(y + 1))
    pear = (y - mu) / np.sqrt(mu)
    # quasi-Poisson correction: inflate SEs when Pearson dispersion > 1
    phi = max(1.0, float(np.sum(pear ** 2) / max(n - k, 1)))
    se = np.sqrt(np.clip(np.diag(inv), 1e-12, None) * phi)
    return {"params": b, "bse": se, "llf": llf, "pll": cur, "k": k, "alpha": 0.0, "mu": mu,
            "pearson": pear, "phi": phi, "est": "Firth-Poisson"}


def fit(y, X, estimator):
    if estimator == "NB2":
        r = fit_nb(y, X)
        if r is not None:
            return r
    return fit_firth_poisson(y, X)


def aic(r):
    return -2 * r["llf"] + 2 * r["k"]


def term(r, j):
    b, se = r["params"][j], r["bse"][j]
    z = b / se
    p = 2 * stats.norm.sf(abs(z))
    return {"beta": b, "se": se, "IRR": np.exp(b), "lo": np.exp(b - 1.96 * se),
            "hi": np.exp(b + 1.96 * se), "z": z, "p": p}


# --------------------------------------------------------------------- spatial filter
class SpatialFilter:
    def __init__(self, coords, k=6, thresh=0.25):
        w = KNN.from_array(coords, k=k)
        n = len(coords)
        Cm = np.zeros((n, n))
        for i, nb in w.neighbors.items():
            Cm[i, nb] = 1
        Cm = np.maximum(Cm, Cm.T)
        M = np.eye(n) - np.ones((n, n)) / n
        vals, vecs = np.linalg.eigh(M @ Cm @ M)
        order = np.argsort(vals)[::-1]
        vals, vecs = vals[order], vecs[:, order]
        keep = vals / vals[0] > thresh
        self.E = vecs[:, keep] * np.sqrt(n)  # scaled so coefficients are readable
        self.vals = vals[keep]
        self.w = KNN.from_array(coords, k=k)
        self.w.transform = "r"

    def moran(self, resid, perm=0):
        """Moran's I of residuals with the analytical (normality) p-value, so that
        eigenvector selection is deterministic and reproducible."""
        m = esda.Moran(np.asarray(resid, float), self.w, permutations=0)
        return m.I, m.p_norm

    def select(self, resid, max_ev=10, alpha=0.05):
        """Forward selection of eigenvectors on model residuals (Griffith-style):
        add the eigenvector most correlated with the current residuals until the
        residual Moran's I is no longer significant."""
        r = np.asarray(resid, float).copy()
        chosen = []
        I, p = self.moran(r)
        while p < alpha and len(chosen) < max_ev:
            E = self.E
            cors = np.abs(E.T @ (r - r.mean())) / (np.linalg.norm(E, axis=0) * np.linalg.norm(r - r.mean()))
            cors[chosen] = -1
            j = int(np.argmax(cors))
            chosen.append(j)
            Z = np.column_stack([np.ones(len(r)), self.E[:, chosen]])
            coef, *_ = np.linalg.lstsq(Z, resid, rcond=None)
            r = resid - Z @ coef
            I, p = self.moran(r)
        return chosen


def bh_fdr(p):
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    pv = p[ok]
    n = len(pv)
    if n == 0:
        return q
    order = np.argsort(pv)
    ranked = pv[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1)
    q[ok] = out
    return q

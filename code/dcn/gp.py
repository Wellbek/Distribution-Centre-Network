"""Gaussian process with a Matern-5/2 ARD kernel, hyperparameters by marginal likelihood (Lecture 4)."""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def _kern(A, B, ls, sf2):
    r = np.sqrt(np.maximum(((A[:, None, :] - B[None, :, :]) / ls) ** 2, 0).sum(-1))
    s5 = np.sqrt(5) * r
    return sf2 * (1 + s5 + s5 ** 2 / 3) * np.exp(-s5)


class GP:
    def fit(self, X, y):
        self.mx, self.sx = X.mean(0), X.std(0) + 1e-9
        self.my, self.sy = y.mean(), y.std() + 1e-9
        Xs, ys = (X - self.mx) / self.sx, (y - self.my) / self.sy
        d = X.shape[1]

        def nll(th):
            ls, sf2, sn2 = np.exp(th[:d]), np.exp(th[d]), np.exp(th[d + 1]) + 1e-6
            K = _kern(Xs, Xs, ls, sf2) + sn2 * np.eye(len(ys))
            try:
                L = np.linalg.cholesky(K)
            except np.linalg.LinAlgError:
                return 1e10
            a = np.linalg.solve(L.T, np.linalg.solve(L, ys))
            return 0.5 * ys @ a + np.log(np.diag(L)).sum()  # data fit + complexity, constant dropped

        best = None
        for start in (0.0, 1.0, -1.0):
            th0 = np.r_[np.full(d, start), 0.0, -2.0]
            r = minimize(nll, th0, method="L-BFGS-B", bounds=[(-3, 3)] * d + [(-3, 3), (-8, 1)])
            if best is None or r.fun < best.fun:
                best = r
        th = best.x
        self.ls, self.sf2, self.sn2 = np.exp(th[:d]), np.exp(th[d]), np.exp(th[d + 1]) + 1e-6
        self.Xs = Xs
        K = _kern(Xs, Xs, self.ls, self.sf2) + self.sn2 * np.eye(len(ys))
        self.L = np.linalg.cholesky(K)
        self.alpha = np.linalg.solve(self.L.T, np.linalg.solve(self.L, ys))
        return self

    def predict(self, X):
        Xs = (X - self.mx) / self.sx
        k = _kern(Xs, self.Xs, self.ls, self.sf2)
        mu = k @ self.alpha
        v = np.linalg.solve(self.L, k.T)
        var = np.maximum(self.sf2 - (v ** 2).sum(0), 1e-12)
        return mu * self.sy + self.my, np.sqrt(var) * self.sy


def expected_improvement(mu, sd, best):
    # EI for minimisation
    z = (best - mu) / sd
    return (best - mu) * norm.cdf(z) + sd * norm.pdf(z)

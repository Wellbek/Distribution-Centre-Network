// Live budgeted search in the browser: the GP of dcn/gp.py (Matern-5/2 ARD, marginal likelihood) and the EI rule of dcn/search.run_search, on precomputed E values.
const LIVE_SEARCH = (() => {
  const SQ5 = Math.sqrt(5);

  function chol(A, n) {
    const L = new Float64Array(n * n);
    for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) {
      let s = A[i * n + j];
      for (let k = 0; k < j; k++) s -= L[i * n + k] * L[j * n + k];
      if (i === j) { if (!(s > 0)) return null; L[i * n + i] = Math.sqrt(s); } else L[i * n + j] = s / L[j * n + j];
    }
    return L;
  }
  function solveL(L, n, b) { const x = Float64Array.from(b); for (let i = 0; i < n; i++) { let s = x[i]; for (let k = 0; k < i; k++) s -= L[i * n + k] * x[k]; x[i] = s / L[i * n + i]; } return x; }
  function solveLT(L, n, b) { const x = Float64Array.from(b); for (let i = n - 1; i >= 0; i--) { let s = x[i]; for (let k = i + 1; k < n; k++) s -= L[k * n + i] * x[k]; x[i] = s / L[i * n + i]; } return x; }

  // Negative log marginal likelihood and its gradient in theta = [log ls (d), log sf2, log(sn2 - 1e-6)]
  function nllGrad(th, X, y, n, d) {
    const ls = th.slice(0, d).map(Math.exp), sf2 = Math.exp(th[d]), sn2 = Math.exp(th[d + 1]) + 1e-6;
    const K = new Float64Array(n * n), E5 = new Float64Array(n * n), D2 = [];
    for (let k = 0; k < d; k++) D2.push(new Float64Array(n * n));
    for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) {
      let r2 = 0;
      for (let k = 0; k < d; k++) { const q = (X[i][k] - X[j][k]) / ls[k], q2 = q * q; r2 += q2; D2[k][i * n + j] = D2[k][j * n + i] = q2; }
      const s = SQ5 * Math.sqrt(r2), e = Math.exp(-s), v = sf2 * (1 + s + s * s / 3) * e;
      K[i * n + j] = K[j * n + i] = v; E5[i * n + j] = E5[j * n + i] = (5 / 3) * sf2 * (1 + s) * e;
    }
    const Kn = Float64Array.from(K); for (let i = 0; i < n; i++) Kn[i * n + i] += sn2;
    const L = chol(Kn, n);
    if (!L) return [1e10, new Array(d + 2).fill(0)];
    const a = solveLT(L, n, solveL(L, n, y));
    let f = 0; for (let i = 0; i < n; i++) f += 0.5 * y[i] * a[i] + Math.log(L[i * n + i]);
    // W = K^-1 - a a^T; grad_t = 0.5 tr(W dK_t)
    const Ki = new Float64Array(n * n);
    for (let c = 0; c < n; c++) { const e = new Float64Array(n); e[c] = 1; const col = solveLT(L, n, solveL(L, n, e)); for (let r = 0; r < n; r++) Ki[r * n + c] = col[r]; }
    const g = new Array(d + 2).fill(0);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const w = Ki[i * n + j] - a[i] * a[j];
      for (let k = 0; k < d; k++) g[k] += 0.5 * w * E5[i * n + j] * D2[k][i * n + j];
      g[d] += 0.5 * w * K[i * n + j];
      if (i === j) g[d + 1] += 0.5 * w * (sn2 - 1e-6);
    }
    return [f, g];
  }

  // Projected quasi-Newton (BFGS) with backtracking inside the bounds of dcn/gp.py
  function minimise(fg, th0, lo, hi, iters = 150) {
    const m = th0.length, clip = t => t.map((v, i) => Math.min(hi[i], Math.max(lo[i], v)));
    let x = clip(th0), [f, g] = fg(x), H = Array.from({ length: m }, (_, i) => Array.from({ length: m }, (_, j) => +(i === j)));
    for (let it = 0; it < iters; it++) {
      const free = x.map((v, i) => !((v <= lo[i] && g[i] > 0) || (v >= hi[i] && g[i] < 0)));
      let p = H.map(row => -row.reduce((s, h, j) => s + (free[j] ? h * g[j] : 0), 0)).map((v, i) => (free[i] ? v : 0));
      if (p.reduce((s, v, i) => s + v * g[i], 0) >= 0) { p = g.map((v, i) => (free[i] ? -v : 0)); H = H.map((r, i) => r.map((_, j) => +(i === j))); }
      let step = 1, xn, fn, gn;
      for (let k = 0; k < 30; k++, step *= 0.5) { xn = clip(x.map((v, i) => v + step * p[i])); [fn, gn] = fg(xn); if (fn <= f + 1e-4 * xn.reduce((s, v, i) => s + (v - x[i]) * g[i], 0)) break; }
      if (!(fn < f) || Math.abs(f - fn) < 1e-9 * Math.max(1, Math.abs(f))) { if (fn < f) { x = xn; f = fn; g = gn; } break; }
      const s = xn.map((v, i) => v - x[i]), yv = gn.map((v, i) => v - g[i]), sy = s.reduce((a, v, i) => a + v * yv[i], 0);
      if (sy > 1e-10) {
        const Hy = H.map(r => r.reduce((a, h, j) => a + h * yv[j], 0)), yHy = yv.reduce((a, v, i) => a + v * Hy[i], 0);
        H = H.map((r, i) => r.map((h, j) => h + ((sy + yHy) * s[i] * s[j]) / (sy * sy) - (Hy[i] * s[j] + s[i] * Hy[j]) / sy));
      }
      x = xn; f = fn; g = gn;
    }
    return [x, f];
  }

  function fit(Xraw, yraw) {
    const n = Xraw.length, d = Xraw[0].length;
    const mx = [], sx = [];
    for (let k = 0; k < d; k++) { const c = Xraw.map(r => r[k]), m = c.reduce((a, b) => a + b, 0) / n; mx.push(m); sx.push(Math.sqrt(c.reduce((a, b) => a + (b - m) ** 2, 0) / n) + 1e-9); }
    const my = yraw.reduce((a, b) => a + b, 0) / n, sy = Math.sqrt(yraw.reduce((a, b) => a + (b - my) ** 2, 0) / n) + 1e-9;
    const X = Xraw.map(r => r.map((v, k) => (v - mx[k]) / sx[k])), y = Float64Array.from(yraw.map(v => (v - my) / sy));
    const lo = [...new Array(d + 1).fill(-3), -8], hi = [...new Array(d + 1).fill(3), 1];
    let best = null;
    for (const st of [0, 1, -1]) { const r = minimise(t => nllGrad(t, X, y, n, d), [...new Array(d).fill(st), 0, -2], lo, hi); if (!best || r[1] < best[1]) best = r; }
    const th = best[0], ls = th.slice(0, d).map(Math.exp), sf2 = Math.exp(th[d]), sn2 = Math.exp(th[d + 1]) + 1e-6;
    const kern = (A, B) => { let r2 = 0; for (let k = 0; k < d; k++) r2 += ((A[k] - B[k]) / ls[k]) ** 2; const s = SQ5 * Math.sqrt(r2); return sf2 * (1 + s + s * s / 3) * Math.exp(-s); };
    const K = new Float64Array(n * n); for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) K[i * n + j] = kern(X[i], X[j]) + (i === j ? sn2 : 0);
    const L = chol(K, n), alpha = solveLT(L, n, solveL(L, n, y));
    return Xq => Xq.map(r => {
      const z = r.map((v, k) => (v - mx[k]) / sx[k]), kv = X.map(x => kern(z, x));
      const mu = kv.reduce((a, v, i) => a + v * alpha[i], 0), v = solveL(L, n, kv);
      return [mu * sy + my, Math.sqrt(Math.max(sf2 - v.reduce((a, b) => a + b * b, 0), 1e-12)) * sy];
    });
  }

  // Normal cdf via erfc (Numerical Recipes erfcc, relative error below 1.2e-7)
  function ncdf(z) { const x = Math.abs(z) / Math.SQRT2, t = 1 / (1 + 0.5 * x), r = t * Math.exp(-x * x - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277))))))))); return z >= 0 ? 1 - r / 2 : r / 2; }
  const npdf = z => Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
  const ei = (mu, sd, best) => { const z = (best - mu) / sd; return (best - mu) * ncdf(z) + sd * npdf(z); };

  // Seeded generator for random selection (mulberry32)
  const rng = seed => () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

  // One budgeted search as a generator: yields after every evaluation, so a page can draw progress
  function* run(pool, starts, budget, rule, seed) {
    const done = [], log = [], draw = rng(seed), G = pool.map(p => p.G2 / 1e6);
    const evaluate = (i, why, eiv) => { done.push(i); log.push({ step: log.length + 1, cand: i, rule: why, E: pool[i].E, ok98: pool[i].ok98, ei: eiv }); };
    for (const i of starts.slice(0, budget)) { evaluate(i, "start"); yield log; }
    while (log.length < budget) {
      const rest = pool.map((_, i) => i).filter(i => !done.includes(i));
      if (!rest.length) break;
      if (rule === "random") { evaluate(rest[Math.floor(draw() * rest.length)], "random"); yield log; continue; }
      const ev = [...done].sort((a, b) => a - b), gp = fit(ev.map(i => pool[i].features), ev.map(i => pool[i].E / 1e6 - G[i]));
      const pr = gp(rest.map(i => pool[i].features)), pe = gp(ev.map(i => pool[i].features));
      const bestEv = Math.min(...ev.map((i, k) => G[i] + pe[k][0]));
      let bi = 0, bs = -Infinity;
      pr.forEach(([m, s], k) => { const v = ei(G[rest[k]] + m, s, bestEv); if (v > bs) { bs = v; bi = k; } });
      evaluate(rest[bi], "EI", bs); yield log;
    }
    return log;
  }

  return { run, fit, rng };
})();
if (typeof module !== "undefined") module.exports = LIVE_SEARCH;

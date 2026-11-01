// Check the browser search against the Python run: node tools/qa/test_search_live.cjs
const L = require("../../code/static/search_live.js");
const R = require("../../code/results/full/registry.json");
const pool = R.pool, seeds = pool.map((p, i) => (p.origin === "G2-best" ? i : -1)).filter(i => i >= 0);
let t = Date.now(), log;
for (const l of L.run(pool, seeds, 40, "ei", 1)) log = l;
const py = R.log_bo.map(r => r.cand), js = log.map(r => r.cand);
const first = js.findIndex((c, i) => c !== py[i]);
const bestAt = a => a.findIndex(c => Math.abs(pool[c].E - R.pool_best) < 1) + 1;
console.log(`replay ${((Date.now() - t) / 1000).toFixed(1)} s; same picks: ${first < 0 ? "all 40" : `first ${first}`}; shared ${js.filter(c => py.includes(c)).length}/40; pool best at evaluation js ${bestAt(js)} / py ${bestAt(py)}`);
console.log("py", py.join(" ")); console.log("js", js.join(" "));

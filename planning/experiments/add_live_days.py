"""Add every store's demand on the four live days (q_all) to run 8's registry, sampled exactly as dcn/pipeline.py does: python add_live_days.py."""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate  # noqa: E402
from dcn.world import make_world  # noqa: E402

f = CODE / "results" / "full" / "registry.json"
R = json.loads(f.read_text())
seed = C.SEED
world = make_world(C.FULL["fraction"], seed)
model = demand.fit(world, demand.make_history(world, np.random.default_rng(seed + 1)))
m = evaluate.context(world, model)["mask"]
d_final = demand.sample_days(model, world, C.FINAL_DAYS, seed + 12, m)
d_avg, d_peak = demand.average_day(model, world, m), demand.peak_day(model, world, m, seed + 14)
show_day = next((d for d in d_final if d["label"] == "weekday"), d_final[0])
weekend = next((d for d in d_final if d["label"] == "weekend"), d_final[1])
days = [show_day, weekend, d_peak, d_avg]
idx = np.array(R["live"]["stores"])
for rec, d in zip(R["live"]["days"], days):
    q = np.round(d["q"], 2)
    assert np.allclose(q[idx], rec["q"]), f"{rec['name']}: the sampler does not reproduce the registry"
    rec["q_all"] = q.tolist()
f.write_text(json.dumps(R))
print("q_all added for", [r["name"] for r in R["live"]["days"]], len(R["live"]["days"][0]["q_all"]), "stores")

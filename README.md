# Dasol network lab: how many distribution centres, and where

[![Trailer: the Dasol distribution-centre redesign in 80 seconds](media/trailer-preview.gif)](media/trailer.mp4)

**[Watch the full trailer (80 s, MP4)](media/trailer.mp4)**

A convenience-store chain of 9,718 stores runs 12 distribution centres, and their leases expire one by one from 2027 to 2029.
This project decides how many DCs to run, at which sites, which stores each serves and how many vehicles each owns, with every delivery before noon.
Every candidate network is priced the same full way: road distances from OpenStreetMap, each store's demand as a Bayesian belief, every DC routed on sampled demand days, and a budgeted Bayesian-optimisation search over the site choice; every method comes from the course (Lectures 0-6).

**The answer in the fictional instance:** run 10 DCs instead of 12, keeping 3 sites and opening 7, which saves about 524 M KRW a month (535 M on days the search never saw).
The quick estimate that ignores the noon clock would have picked 8 DCs and cost 412 M KRW a month more.
The saving rests on how far the real network has drifted from a good design, so the first step is a check against Dasol's real delivery records.
All figures come from the reported run (`code/results/full/registry.json`); Dasol Retail is fictional, the geography and road distances are real.

## What is here

| File | What it is |
|---|---|
| `demo.html` | Interactive demonstration: the answer, a delivery day on real roads, the method lecture by lecture, the data, the checks and the extensions; opens offline |
| `proposal.html` | The proposal to management, 17 slides in project-management order |
| `problem-definition.md` | The full problem definition: formulation, data, method, evidence, proposal and the review of the AI assistance |
| `code/` | Everything that produces the numbers; three commands (see `code/README.md`) |
| `media/` | The trailer and its preview |
| `video/` | The trailer's source (Remotion) |

## Reproduce

```sh
cd code
pip install -r requirements.txt
python run_full.py      # the reported run
python run_reduced.py   # one store in five, about 8 minutes on two cores
```

## Rebuild the trailer

The trailer is built with [Remotion](https://www.remotion.dev) from footage captured frame by frame in `demo.html` and from numbers read out of the registry, so no figure in it is typed by hand.

```sh
python video/scripts/capture.py   # footage and stills from demo.html and proposal.html (Playwright)
python video/scripts/data.py      # the trailer's numbers and map geometry from the registry
cd video && npm install && npm run render
```

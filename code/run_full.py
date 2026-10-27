"""Full run (all 10,000 stores, run on a large machine): python run_full.py"""
from dcn import config as C
from dcn import extensions
from dcn.pipeline import run

from build_demo import build

if __name__ == "__main__":
    run(C.FULL)
    extensions.run(C.FULL)
    if C.DEMO_PROFILE == "full":
        build("full")

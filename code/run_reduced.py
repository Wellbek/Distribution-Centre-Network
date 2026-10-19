"""Reduced run (1 store in 5, a few minutes): python run_reduced.py"""
from dcn import config as C
from dcn.pipeline import run

from build_demo import build

if __name__ == "__main__":
    run(C.REDUCED)
    if C.DEMO_PROFILE == "reduced":
        build("reduced")

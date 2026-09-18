import sys
from pathlib import Path


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

BACKEND_PATH = (
    REPO_ROOT
    / "backend"
)

sys.path.insert(
    0,
    str(BACKEND_PATH),
)

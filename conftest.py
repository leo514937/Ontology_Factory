from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
PYTHONPATH_ENTRIES = (
    REPO_ROOT,
    REPO_ROOT / "WIKI_MG" / "src",
    REPO_ROOT / "storage" / "src",
    REPO_ROOT / "wiki_agent" / "src",
    REPO_ROOT / "ontology_core" / "src",
    REPO_ROOT / "evolution" / "src",
    REPO_ROOT / "relation" / "src",
    REPO_ROOT / "ner" / "src",
    REPO_ROOT / "dls" / "src",
    REPO_ROOT / "preprocess",
    REPO_ROOT / "pipeline" / "src",
    REPO_ROOT / "aft" / "aft-main" / "src",
)

for entry in reversed(PYTHONPATH_ENTRIES):
    rendered = str(entry)
    if rendered not in sys.path:
        sys.path.insert(0, rendered)

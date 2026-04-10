from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for relative in (
    ".",
    "storage/src",
    "wiki_agent/src",
    "ner/src",
    "relation/src",
    "ontology_core/src",
    "dls/src",
    "evolution/src",
    "WIKI_MG/src",
    "preprocess",
    "pipeline/src",
):
    candidate = str((ROOT / relative).resolve())
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

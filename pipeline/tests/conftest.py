from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
(ROOT / ".test-artifacts" / "pipeline").mkdir(parents=True, exist_ok=True)

for relative in (
    ".",
    "pipeline/src",
    "ner/src",
    "relation/src",
    "storage/src",
    "ontology_core/src",
    "evolution/src",
    "dls/src",
    "preprocess",
    "wiki_agent/src",
    "WIKI_MG/src",
):
    candidate = str((ROOT / relative).resolve())
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

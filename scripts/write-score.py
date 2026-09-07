#!/usr/bin/env python3
"""Legacy declared-metrics calculator, NOT verification evidence or promotion.

The production runner binds proofs and scores in its own result.json. This
standalone helper can check metric consistency only, not comparator success.
"""

import json
from pathlib import Path
import sys
from benchmark_contract import metrics

if len(sys.argv) != 3:
    raise SystemExit("usage: write-score.py SUBMISSION_DIR RENDERED_SNAPSHOT")
snapshot = json.loads(Path(sys.argv[2]).read_text())
sigma, hverify, bound = metrics(Path(sys.argv[1]))
if snapshot != {"sigma": sigma, "hverify": hverify, "bound": bound}:
    raise SystemExit("declared metrics changed after rendering; no score issued")
print(json.dumps({
    "profile": "declared-metrics-only", "ranked": False, "verified": False,
    "sigma": sigma, "hverify": hverify, "bound": bound,
    "score": str(sigma * hverify), "direction": "minimize", "tie_break": sigma,
}))

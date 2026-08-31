# ruff: noqa
"""B0.3 four-metric aggregate parity (registered H1): our runner's
scoring/aggregation vs the pinned upstream evaluator (lm_eval==0.4.8,
the source of our vendored copy) on a FIXED, PROGRAMMATIC response set
over the 541 — built without any per-prompt inspection (single-use
invariant): response cycles by key among (prompt echo, uppercased echo,
fixed JSON) purely mechanically. PASS: all four aggregates exactly
equal AND all 541 per-prompt dicts equal."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil.bench import aggregate, load_ifeval, score_response

rows = load_ifeval(ROOT / "data" / "bench" / "ifeval_input_data.jsonl")


def fixed_response(row):
    k = row["key"] % 3
    if k == 0:
        return row["prompt"]
    if k == 1:
        return row["prompt"].upper()
    return '{"answer": "yes", "detail": "a fixed mechanical response"}'


responses = [fixed_response(r) for r in rows]
ours_pp = [score_response(r, resp) for r, resp in zip(rows, responses)]
ours = aggregate(ours_pp)

WORKER = r"""
import json, sys, importlib.util
import langdetect
langdetect.DetectorFactory.seed = 0
# load the ifeval task package directly by path: lm_eval's top-level
# __init__ drags in model backends irrelevant to scoring
spec_pkg = importlib.util.find_spec("lm_eval")
pkg_dir = spec_pkg.submodule_search_locations[0]
import types
for name in ["lm_eval", "lm_eval.tasks", "lm_eval.tasks.ifeval"]:
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [pkg_dir + "/" + "/".join(name.split(".")[1:])] if "." in name else [pkg_dir]
        sys.modules[name] = mod
spec = importlib.util.spec_from_file_location(
    "lm_eval.tasks.ifeval.utils", pkg_dir + "/tasks/ifeval/utils.py")
utils = importlib.util.module_from_spec(spec)
sys.modules["lm_eval.tasks.ifeval.utils"] = utils
spec.loader.exec_module(utils)
rows = [json.loads(l) for l in open(sys.argv[1])]
responses = json.load(open(sys.argv[2]))
import random
pp = []
for r, resp in zip(rows, responses):
    random.seed(r["key"])  # registered pin, mirrored from stencil.bench
    pp.append(utils.process_results(r, [resp]))
agg = {
 "prompt_level_strict_acc": sum(p["prompt_level_strict_acc"] for p in pp) / len(pp),
 "inst_level_strict_acc": utils.agg_inst_level_acc([p["inst_level_strict_acc"] for p in pp]),
 "prompt_level_loose_acc": sum(p["prompt_level_loose_acc"] for p in pp) / len(pp),
 "inst_level_loose_acc": utils.agg_inst_level_acc([p["inst_level_loose_acc"] for p in pp]),
}
print(json.dumps({"agg": agg, "pp": pp}))
"""

scratch = Path("/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad")
(scratch / "score_worker.py").write_text(WORKER)
(scratch / "responses.json").write_text(json.dumps(responses))
r = subprocess.run(
    ["uv", "run", "--isolated", "--no-project", "--with", "lm_eval==0.4.8",
     "--with", "langdetect", "--with", "immutabledict", "--with", "nltk>=3.9",
     "python", str(scratch / "score_worker.py"),
     str(ROOT / "data" / "bench" / "ifeval_input_data.jsonl"),
     str(scratch / "responses.json")],
    capture_output=True, text=True, timeout=3600,
    env={**os.environ, "NLTK_DATA": str(ROOT / "vendor" / "nltk_data")},
)
if r.returncode != 0:
    sys.exit(f"upstream worker failed: {r.stderr[-1500:]}")
up = json.loads(r.stdout.strip().split("\n")[-1])

pp_equal = ours_pp == up["pp"]
agg_equal = ours == up["agg"]
rec = {"ours": ours, "upstream": up["agg"], "upstream_pin": "lm_eval==0.4.8",
       "per_prompt_all_equal": pp_equal, "n": len(rows),
       "PASS": bool(pp_equal and agg_equal)}
print(json.dumps(rec, indent=1))
(ROOT / "results" / "qwen" / "b0-score-parity.json").write_text(json.dumps(rec, indent=1))

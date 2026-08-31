# ruff: noqa
"""EVF Phase E0 — the registered kill-fast pilot (EVF-PLAN.md).
Extracts the registered feature set at each discordant divergence point
(15 repairs / 12 regressions from the t30-b3 calibration anatomy),
fits the deterministic logistic probe, and evaluates the REGISTERED
GATE under BOTH fold schemes: leave-one-TOPIC-out and leave-one-
FAMILY-out (family = first-listed constraint's family; disclosed).
GATE: r+ >= 0.60 AND r- <= 0.25 in BOTH schemes. Per-item features
saved (playbook)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
from stencil.evf import extract_features, gate_eval, load_anatomy, load_model

FAMILY = {"caps": "change_case", "lower": "change_case", "kw_exist": "keywords",
          "kw_freq": "keywords", "kw_forbid": "keywords", "n_words_min": "length",
          "n_words_max": "length", "n_sent": "length", "bullets": "format",
          "title": "format", "json_fmt": "format", "placeholders": "content",
          "postscript": "content", "two_resp": "combination"}

m, tok, ctrl = load_model(ROOT)
anat = load_anatomy(ROOT, arm="t30-b3")
feats, labels, topics, families, items = [], [], [], [], []
for it in anat:
    f = extract_features(m, tok, ctrl, it)
    feats.append(f); labels.append(it["label"])
    topics.append(it["row"]["topic"])
    families.append(FAMILY[it["row"]["combo"][0]])
    items.append({"i": it["i"], "label": it["label"], "topic": it["row"]["topic"],
                  "family": FAMILY[it["row"]["combo"][0]], "features": f})
    print(f"{it['i']}: label {it['label']} kl {f['kl_focus']:.4f} ob {f['obligation_shift']:.4f}", flush=True)

res_topic = gate_eval(feats, labels, topics)
res_family = gate_eval(feats, labels, families)
gate = {"topic_folds": res_topic, "family_folds": res_family,
        "PASS": bool(res_topic["r_plus"] >= 0.60 and res_topic["r_minus"] <= 0.25
                     and res_family["r_plus"] >= 0.60 and res_family["r_minus"] <= 0.25)}
out = {"items": items, "gate": gate}
(ROOT / "results" / "qwen" / "e0-pilot.json").write_text(json.dumps(out, indent=1))
print(json.dumps(gate, indent=1))

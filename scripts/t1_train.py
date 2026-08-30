# ruff: noqa
"""T1 training (prereg v3 + amendment A1, frozen recipe).

Data: t1-train-features.pt (48 s0x2 sessions) + t1-trace0-features.pt
(48 s0 sessions, recomputed). Rows: per event, typed candidate set
(pred_type restriction); label = typed index of the authoritative
same-type candidate iff type_active and one exists, else NULL.
No-candidate rows: zero loss, excluded from NULL metrics.

Loss: CE over [NULL]+typed + decision-aligned hinge margins (t1_head).
Optimizer frozen: Adam(1e-3, 0.9/0.999, 1e-8, no wd), 30 epochs,
batch 256, shuffle seed 0. Warm start from pinned legacy Wq/Wk.

Gates on t1-calib-features.pt (screens): conditional address >= 90%;
active recall >= 0.41640866873065013; ZERO NULL-error sessions
conditioned on hazard-facing sessions (n_h >= 12 required); full-0.1
decision margins on >= 90% of active and >= 90% of inactive
hard-negative rows. Saves results/qwen/t1-head.pt + gate report.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F

from stencil.t1_head import T1Head, decide, margin_loss
from stencil.t2_trace import load_trace


def rows_from(path):
    tr = load_trace(path)
    rows = []
    for e in tr["events"]:
        typed = [i for i, c in enumerate(e["candidates"]) if c["type"] == e["pred_type"]]
        if not typed:
            continue  # structural abstention: no loss, no NULL metric
        cand_feats = e["cand_feats"].float()[typed]
        label = None
        if e["type_active"]:
            auth = [k for k, i in enumerate(typed) if e["candidates"][i]["authoritative"]]
            if auth:
                label = auth[0]
        # hazard-facing marker for the calib gate
        tgt = e["s0x_target"]
        hazard = (tgt.get("type") is not None and e["work_turn"] == tgt["work_turn"]
                  and e["pred_type"] == tgt["type"]
                  and not any(e["candidates"][i]["authoritative"] for i in typed))
        rows.append({"seed": e["seed"], "h20": e["h20"].float(), "cand": cand_feats,
                     "label": label, "hazard": hazard, "inactive": not e["type_active"]})
    return rows


def train(rows):
    head = T1Head()
    head.warm_start(torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu"))
    opt = torch.optim.Adam(head.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    g = torch.Generator().manual_seed(0)
    for ep in range(30):
        perm = torch.randperm(len(rows), generator=g)
        for i in range(0, len(rows), 256):
            loss = torch.tensor(0.0)
            for j in perm[i:i + 256].tolist():
                r = rows[j]
                logits = head(r["h20"], r["cand"])
                target = 0 if r["label"] is None else r["label"] + 1
                loss = loss + F.cross_entropy(logits[None], torch.tensor([target]))
                loss = loss + margin_loss(logits, r["label"])
            opt.zero_grad(); loss.backward(); opt.step()
    return head


def gates(head, calib_rows):
    with torch.no_grad():
        active = [r for r in calib_rows if r["label"] is not None]
        inactive = [r for r in calib_rows if r["inactive"]]
        addr_ok = rec_ok = 0
        act_margin_ok = inact_margin_ok = 0
        null_err_sessions = set()
        hazard_sessions = {r["seed"] for r in calib_rows if r["hazard"]}
        for r in calib_rows:
            logits = head(r["h20"], r["cand"])
            d = decide(logits)
            if r["label"] is not None:
                if d == r["label"]:
                    rec_ok += 1
                if int(logits[1:].argmax()) == r["label"]:
                    addr_ok += 1
                if float(margin_loss(logits, r["label"])) == 0.0:
                    act_margin_ok += 1
            if r["inactive"]:
                if d is not None:
                    null_err_sessions.add(r["seed"])
                if float(margin_loss(logits, None)) == 0.0:
                    inact_margin_ok += 1
        n_h = len(hazard_sessions)
        rep = {
            "n_active_rows": len(active), "n_inactive_rows": len(inactive),
            "conditional_address": round(addr_ok / max(1, len(active)), 4),
            "active_recall": round(rec_ok / max(1, len(active)), 4),
            "null_error_sessions": sorted(null_err_sessions),
            "n_hazard_sessions": n_h,
            "active_margin_frac": round(act_margin_ok / max(1, len(active)), 4),
            "inactive_margin_frac": round(inact_margin_ok / max(1, len(inactive)), 4),
        }
        rep["gate_address"] = rep["conditional_address"] >= 0.90
        rep["gate_recall"] = rep["active_recall"] >= 0.41640866873065013
        rep["gate_null"] = (n_h >= 12) and not null_err_sessions
        rep["gate_null_countable"] = n_h >= 12
        rep["gate_margins"] = rep["active_margin_frac"] >= 0.90 and rep["inactive_margin_frac"] >= 0.90
        rep["ALL_GATES"] = all(rep[k] for k in ("gate_address", "gate_recall", "gate_null", "gate_margins"))
        return rep


def main():
    rows = rows_from(ROOT / "results" / "qwen" / "t1-train-features.pt") + \
           rows_from(ROOT / "results" / "qwen" / "t1-trace0-features.pt")
    print(f"{len(rows)} training rows "
          f"({sum(1 for r in rows if r['label'] is not None)} active, "
          f"{sum(1 for r in rows if r['inactive'])} inactive)", flush=True)
    head = train(rows)
    torch.save(head.state_dict(), ROOT / "results" / "qwen" / "t1-head.pt")
    calib_rows = rows_from(ROOT / "results" / "qwen" / "t1-calib-features.pt")
    rep = gates(head, calib_rows)
    print(json.dumps(rep, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "t1-gates.json").write_text(json.dumps(rep, indent=1))
    print("saved results/qwen/t1-head.pt + t1-gates.json", flush=True)


if __name__ == "__main__":
    main()

# ruff: noqa
"""T2 controller-state bakeoff (t2t3 prereg v3.1; frozen contract).

Five contenders, identical shared T1 head (warm from t1-head.pt),
per-session state on the D-clock (step gaps; inter-turn D=32), score
from z_pre then write, whole-session batches of 8, CE + A1 margins
normalized per event, Adam(1e-3), 30 epochs, shuffle seed 0.

Eval (calib-hard): PRIMARY = target-hazard leaking sessions; tie-breaks
leaking events, recall, controller params. PILOT ELIGIBILITY = zero
false-selection sessions across ALL inactive candidate-bearing events
(off-target leaks reported). Screens: address >= 0.90, recall >=
0.41640866873065013, margins 90/90. CPU-only (cached features).
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
from stencil.t2_state import CONTROLLERS, make_controller
from stencil.t2_sessions import TYPES
from stencil.t2_trace import load_trace

INTER_TURN_D = 32


def sessions_from(paths):
    rows = []
    for p in paths:
        tr = load_trace(p)
        for e in tr["events"]:
            typed = [i for i, c in enumerate(e["candidates"]) if c["type"] == e["pred_type"]]
            if not typed:
                continue
            label = None
            if e["type_active"]:
                auth = [k for k, i in enumerate(typed) if e["candidates"][i]["authoritative"]]
                if auth:
                    label = auth[0]
            tgt = e["s0x_target"]
            hazard = (tgt.get("type") is not None and e["work_turn"] == tgt["work_turn"]
                      and e["pred_type"] == tgt["type"]
                      and not any(e["candidates"][i]["authoritative"] for i in typed))
            rows.append({"seed": e["seed"], "wt": e["work_turn"], "step": e["step"],
                         "h20": e["h20"].float(), "cand": e["cand_feats"].float()[typed],
                         "label": label, "hazard": hazard, "inactive": not e["type_active"],
                         "type_idx": TYPES.index(e["pred_type"])})
    by = {}
    for r in rows:
        by.setdefault(r["seed"], []).append(r)
    return [sorted(v, key=lambda r: (r["wt"], r["step"])) for _, v in sorted(by.items())]


def run_session_seq(head, ctrl, seq, collect=None):
    z = ctrl.init_state()
    loss = torch.tensor(0.0)
    prev_wt, prev_step = None, None
    for r in seq:
        D = INTER_TURN_D if r["wt"] != prev_wt else max(1, r["step"] - prev_step)
        prev_wt, prev_step = r["wt"], r["step"]
        z_pre = ctrl.transition(z, D)
        null_add, q_add = ctrl.score_aug(z_pre)
        logits = head(r["h20"], r["cand"], null_add=null_add, q_add=q_add)
        target = 0 if r["label"] is None else r["label"] + 1
        loss = loss + F.cross_entropy(logits[None], torch.tensor([target])) + margin_loss(logits, r["label"])
        if collect is not None:
            collect.append((r, logits.detach()))
        z = ctrl.write(z_pre, r["h20"], r["type_idx"])
    return loss / max(1, len(seq))


def evaluate(head, ctrl, sessions):
    leak_hazard_sessions, leak_hazard_events = set(), 0
    offtarget_sessions = set()
    addr_ok = rec_ok = n_active = act_m = inact_m = n_inact = 0
    with torch.no_grad():
        for seq in sessions:
            coll = []
            run_session_seq(head, ctrl, seq, collect=coll)
            for r, logits in coll:
                d = decide(logits)
                if r["label"] is not None:
                    n_active += 1
                    rec_ok += d == r["label"]
                    addr_ok += int(logits[1:].argmax()) == r["label"]
                    act_m += float(margin_loss(logits, r["label"])) == 0.0
                if r["inactive"]:
                    n_inact += 1
                    inact_m += float(margin_loss(logits, None)) == 0.0
                    if d is not None:
                        if r["hazard"]:
                            leak_hazard_sessions.add(r["seed"])
                            leak_hazard_events += 1
                        else:
                            offtarget_sessions.add(r["seed"])
    return {
        "hazard_leak_sessions": len(leak_hazard_sessions),
        "hazard_leak_events": leak_hazard_events,
        "offtarget_leak_sessions": len(offtarget_sessions),
        "all_inactive_clean": not leak_hazard_sessions and not offtarget_sessions,
        "recall": round(rec_ok / max(1, n_active), 4),
        "address": round(addr_ok / max(1, n_active), 4),
        "margins": [round(act_m / max(1, n_active), 4), round(inact_m / max(1, n_inact), 4)],
    }


def main():
    train_sessions = sessions_from([ROOT / "results" / "qwen" / "t1-train-features.pt",
                                    ROOT / "results" / "qwen" / "t1-trace0-features.pt"])
    calib_sessions = sessions_from([ROOT / "results" / "qwen" / "t1-calib-features.pt"])
    print(f"{len(train_sessions)} train sessions, {len(calib_sessions)} calib sessions", flush=True)
    legacy = torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu")
    t1_state = torch.load(ROOT / "results" / "qwen" / "t1-head.pt", map_location="cpu")
    report = {}
    for name in CONTROLLERS:
        head = T1Head()
        head.warm_start(legacy)
        head.load_state_dict(t1_state)
        ctrl = make_controller(name)
        params = list(head.parameters()) + list(ctrl.parameters())
        opt = torch.optim.Adam(params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
        g = torch.Generator().manual_seed(0)
        for ep in range(30):
            perm = torch.randperm(len(train_sessions), generator=g)
            for i in range(0, len(train_sessions), 8):
                loss = torch.tensor(0.0)
                for j in perm[i:i + 8].tolist():
                    loss = loss + run_session_seq(head, ctrl, train_sessions[j])
                opt.zero_grad(); loss.backward(); opt.step()
        rep = evaluate(head, ctrl, calib_sessions)
        rep["controller_params"] = sum(p.numel() for p in ctrl.parameters())
        report[name] = rep
        torch.save({"head": head.state_dict(), "ctrl": ctrl.state_dict()},
                   ROOT / "results" / "qwen" / f"t2-ctrl-{name}.pt")
        print(name, json.dumps(rep), flush=True)
    (ROOT / "results" / "qwen" / "t2-bakeoff.json").write_text(json.dumps(report, indent=1))
    print("saved results/qwen/t2-bakeoff.json", flush=True)


if __name__ == "__main__":
    main()

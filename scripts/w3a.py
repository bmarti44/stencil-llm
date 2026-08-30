# ruff: noqa
"""W3a SEALED clean-format validation (w3 prereg v3; ONE attempt,
fail-closed). Seeds 13,800,000..95, interference s0c (trained prefix
format appears NOWHERE — enforced by a per-arm zero-occurrence
assertion on build_arm_prompt output immediately before tokenization,
counted as a session failure if tripped, never silently dropped),
split "dev", feedback_mode=none, frozen w0-ce.pt. Arms: base, wave,
proxy, oracle, reinsertion. PASS = headroom >= 0.10 (miss ->
INCONCLUSIVE close) AND wave closure >= 0.50 AND T0.3 validity;
causal re-test wave > proxy raw gain, both valid. Full per-work
records + full-length sha256 from the start.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen_task import CODE_PREFIXES
from stencil.qwen3 import Qwen3
from stencil.t2_runner import LAYERS, _oracle_moment, build_arm_prompt, ledger_sentence_spans, score_work
from stencil.t2_sessions import SENT, generate_t2
from stencil.wave import WaveController

NEUTRAL = "[checker] (no feedback available this session)"
SEEDS = [13_800_000 + i for i in range(96)]
PINNED = {
    "results/qwen/w0-ce.pt": "eab4831f2bcb80f8e2e1147414cc2c0cad30d33466e85890ed995ff666743099",
    "results/qwen/w0-proxy.pt": "91a7aab8f227646d8b381f9ae0e9b0c87b7aa4a8aa29af9f83dd7dab6319f586",
    "models/qwen3-1.7b.pt": "13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829",
    "models/qwen3-1.7b-hf/tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
}


def contaminated(ptxt):
    return any(SENT["prefix"].format(v=v) in ptxt for v in CODE_PREFIXES)


def run_arm(m, tok, ctrl, sess, arm):
    results, hashes, dirty = [], {}, 0
    for wt in sess.work_turns:
        ptxt = build_arm_prompt(sess, wt, "dev", arm).replace(
            "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
        if contaminated(ptxt):
            dirty += 1
        enc = tok.encode(ptxt)
        P = len(enc.ids)
        spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok) if arm == "oracle" else {}
        toks = torch.tensor([enc.ids], device="cuda")
        K = None
        gen, text = [], ""
        with torch.no_grad():
            if arm in ("wave", "proxy"):
                K = m(toks, return_hidden=20)[0].float()[:P]
            for _ in range(120):
                ab = None
                if arm == "oracle" and spans:
                    key = _oracle_moment(text[-80:])
                    if key is not None and key in spans:
                        e = torch.full((P,), -6.0)
                        e[spans[key][0]:spans[key][1]] = 6.0
                        sm = torch.softmax(e, dim=-1)
                        t = toks.shape[1]
                        bias = torch.zeros(t, t)
                        bias[-1, :P] = 2.0 * sm / sm.max()
                        ab = {L: bias.cuda() for L in LAYERS}
                elif arm in ("wave", "proxy"):
                    h_t = m(toks, return_hidden=20)[0, -1].float()
                    row = ctrl(h_t, K)
                    t = toks.shape[1]
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1, :P] = row
                    ab = {L: bias for L in LAYERS}
                nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                gen.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(gen)
                if "```" in text[-6:]:
                    break
        code = text.split("```")[0]
        hashes[wt] = hashlib.sha256(code.encode()).hexdigest()
        results.append(score_work(code, sess, wt))
    return results, hashes, dirty


def main():
    out_path = ROOT / "results" / "qwen" / "w3a.json"
    marker = ROOT / "results" / "qwen" / "w3a.started"
    if out_path.exists() or marker.exists():
        sys.exit("REFUSED: W3a already started/finished")
    for rel, want in PINNED.items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != want:
            sys.exit(f"REFUSED: hash mismatch {rel}")
    marker.write_text("started")

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrls = {}
    for name in ("wave", "proxy"):
        c = WaveController().cuda()
        c.load_state_dict(torch.load(ROOT / "results" / "qwen" / f"w0-{'ce' if name == 'wave' else 'proxy'}.pt", map_location="cpu"))
        ctrls[name] = c.eval()

    arms = ["base", "wave", "proxy", "oracle", "reinsertion"]
    agg = {a: {"adh": 0, "n": 0, "parse": 0, "works": 0, "paired": {}, "hashes": {}, "dirty": 0} for a in arms}
    for k, seed in enumerate(SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0c")
        for arm in arms:
            rs, hs, dirty = run_arm(m, tok, ctrls.get(arm), sess, arm)
            agg[arm]["dirty"] += dirty
            for r in rs:
                a = agg[arm]
                a["works"] += 1
                a["parse"] += r.parse
                a["hashes"][f"{seed}:{r.turn}"] = hs[r.turn]
                a["paired"][f"{seed}:{r.turn}"] = {"parse": r.parse, "exec": r.exec_ok}
                for o in sess.opportunities:
                    if o.turn == r.turn and o.cell == "active":
                        a["n"] += 1
                        a["adh"] += bool(r.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
        if k % 12 == 0:
            print(f"  {k}/{len(SEEDS)}", flush=True)

    base = agg["base"]
    out = {"mode": "s0c", "n_sessions": len(SEEDS), "pinned": PINNED,
           "contaminated_prompts": {a: agg[a]["dirty"] for a in arms}}
    for arm in arms:
        a = agg[arm]
        rec = {"adh_raw": a["adh"], "n_active": a["n"],
               "adherence": round(a["adh"] / max(1, a["n"]), 4),
               "parse_rate": round(a["parse"] / max(1, a["works"]), 4)}
        if arm != "base":
            broken = sum(1 for kk in a["paired"] if
                         (base["paired"][kk]["parse"] and not a["paired"][kk]["parse"]) or
                         (base["paired"][kk]["exec"] and not a["paired"][kk]["exec"]))
            gain = a["adh"] - base["adh"]
            rec |= {"paired_broken": broken, "adh_gain_raw": gain, "dU_total": gain - 2 * broken,
                    "valid": bool(gain - 2 * broken > 0 and gain - 2 * broken >= 0.8 * gain)}
        out[arm] = rec
    hr = agg["oracle"]["adh"] - base["adh"]
    out["headroom"] = round(hr / max(1, base["n"]), 4)
    out["precondition_binds"] = out["headroom"] >= 0.10
    for arm in ("wave", "proxy"):
        out[arm]["closure"] = round((agg[arm]["adh"] - base["adh"]) / hr, 4) if hr else None
    if any(out["contaminated_prompts"].values()):
        out["VERDICT"] = "VOID — contamination assertion tripped"
    elif not out["precondition_binds"]:
        out["VERDICT"] = "INCONCLUSIVE — headroom does not bind"
    else:
        w = out["wave"]
        passed = w["closure"] >= 0.50 and w["valid"]
        causal = w["adh_gain_raw"] > out["proxy"]["adh_gain_raw"] and w["valid"] and out["proxy"]["valid"]
        out["VERDICT"] = ("CLEAN-FORMAT WIN" if passed else "CLEAN-FORMAT MISS") + \
            ("; causal HOLDS" if causal else "; causal NOT supported")
    out["work_hashes"] = {a: agg[a]["hashes"] for a in arms}
    tmp = str(out_path) + ".partial"
    Path(tmp).write_text(json.dumps(out, indent=1))
    os.replace(tmp, out_path)
    print("VERDICT:", out["VERDICT"], flush=True)
    print(json.dumps({k: v for k, v in out.items() if k not in ("work_hashes", "pinned")}, indent=1), flush=True)


if __name__ == "__main__":
    main()

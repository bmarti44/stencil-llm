"""Exp 3 MemoryCode-derived screen: items, auto adapter, GPU runs, summary.

Contract: results/memorycode-derived/CONTRACT.md (every scientific choice lives there).
Phases (all write under results/memorycode-derived/):
  items      CPU: enumerate eligible items, split by dialogue -> items.json
  auto       CPU: run the frozen FOCUS-3 adapter on SETUP+SCREEN items -> auto/*.json,
             auto/summary.json with the non-vacuous check and the error table
  run        GPU: --split setup|screen, four arms per item -> <split>/item-*.json
  summarize  CPU: <split>/summary.json (eligibility line or screen reading)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "memorycode-derived"
MAX_NEW = 512
DEADLINE = 300.0
ARMS = ["history", "restate_all", "auto", "oracle"]


def _write_atomic(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1))
    os.replace(tmp, path)


def _tokenizer():
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()


# ------------------------------------------------------------------------------ items


def phase_items(args) -> dict:
    from stencil import memorycode as mc

    tokenizer = _tokenizer()
    items = mc.enumerate_items(tokenizer)
    split = mc.split_items(items, n_setup=args.n_setup, n_screen=args.n_screen)
    for name in ("setup", "screen"):
        for item in split[name]:
            item["id"] = f"{item['dialogue']}-{item['session']}"
            item["split"] = name
    payload = {
        "contract": "results/memorycode-derived/CONTRACT.md",
        "vendor_sha": "1ab87e119b2f9a498de8075219e1c07f6041b394",
        "max_prompt_tokens": mc.MAX_PROMPT_TOKENS,
        "n_eligible_items": split["n_eligible_items"],
        "n_eligible_dialogues": split["n_eligible_dialogues"],
        "items": split["setup"] + split["screen"],
    }
    _write_atomic(OUT / "items.json", payload)
    print(
        f"eligible items {split['n_eligible_items']} over "
        f"{split['n_eligible_dialogues']} dialogues; setup {len(split['setup'])}, "
        f"screen {len(split['screen'])}"
    )
    return payload


def load_items(split: str | None = None) -> list[dict]:
    items = json.loads((OUT / "items.json").read_text())["items"]
    return [it for it in items if split is None or it["split"] == split]


# ------------------------------------------------------------------------------- auto


def _introduced(dialogue: dict, i: int, mc) -> list[tuple[int, int]]:
    before = set(mc.instruction_ids(dialogue, i - 1)) if i else set()
    return [p for p in mc.instruction_ids(dialogue, i) if p not in before]


def _head(text: str, n: int = 6) -> str:
    return " ".join(text.lower().split()[:n])


def topic_keys(topic: dict, u: int) -> list[str]:
    """Key literals a mentor line must mention to count as stating instruction
    (topic, u): the affix of a `.*_m$`-style regex, the decorator/import name of a
    list regex, or the object words of a boolean regex (CONTRACT.md amendment 1)."""
    obj, regex = topic["regex"][u]
    if isinstance(regex, list):
        return [str(regex[0]).lower()]
    if isinstance(regex, bool):
        words = str(obj).lower().split()
        return [words[-1]]  # annotation / docstring / assert / try / comment / ...
    literal = str(regex).replace(".*", "").replace("$", "").replace("^", "")
    if "\\d" in literal:
        return ["digit", "number"]
    if literal.startswith("[") or literal.startswith("\\b"):
        return ["upper", "lower", "camel", "snake", "capital"]
    return [literal.lower()] if literal else []


def _states_topic(line_text: str, topic: dict, u: int) -> bool:
    if _head(topic["text"][u]) in line_text:
        return True
    return any(key in line_text for key in topic_keys(topic, u))


def error_table(dialogue: dict, s: int, auto: dict, topics: dict, mc) -> dict:
    """Label-derived error table for one item (CONTRACT.md, 'Error table')."""
    by_id = {int(t["id"]): t for t in topics["instructions"]}
    turns = {int(k): v for k, v in auto["turns"].items()}
    rows = auto["rows"]
    session_of = {r["id"]: turns[r["provenance_turn"]]["session"] for r in rows}
    lines = {i: mc.speaker_lines(dialogue, i) for i in range(s)}
    false_admissions = []
    for r in rows:
        i = session_of[r["id"]]
        line_text = lines[i][turns[r["provenance_turn"]]["line"]][1].lower()
        if not any("instruction" in t for t in dialogue["sessions"][i]["type"]):
            false_admissions.append({"row": r["id"], "reason": "filler-session"})
            continue
        if not any(
            _states_topic(line_text, by_id[p], u)
            for p, u in _introduced(dialogue, i, mc)
        ):
            false_admissions.append({"row": r["id"], "reason": "no-topic-in-line"})
    admitted_sessions = set(session_of.values())
    missed_instructions = [
        i
        for i in range(s)
        if any(
            t in ("instruction-add", "instruction-update")
            for t in dialogue["sessions"][i]["type"]
        )
        and i not in admitted_sessions
    ]
    live = [r for r in rows if r["status"] == "live"]
    missed_updates = []
    for i in range(1, s):
        if "instruction-update" not in dialogue["sessions"][i]["type"]:
            continue
        for p, u in _introduced(dialogue, i, mc):
            older = [v for q, v in mc.instruction_ids(dialogue, i - 1) if q == p]
            if not older:
                continue
            old_head = _head(by_id[p]["text"][older[0]])
            new_head = _head(by_id[p]["text"][u])
            new_live = any(
                session_of[r["id"]] == i and new_head in r["text"].lower() for r in live
            )
            old_live = any(
                session_of[r["id"]] < i and old_head in r["text"].lower() for r in live
            )
            if new_live and old_live:
                missed_updates.append({"session": i, "pivot": p})
    return {
        "false_admissions": false_admissions,
        "missed_instructions": missed_instructions,
        "missed_updates": missed_updates,
        "overflow_events": auto["overflow"],
        "admitted": auto["admitted"],
        "relations_applied": auto["relations_applied"],
        "live_rows": len(live),
    }


def phase_auto(args) -> dict:
    from stencil import memorycode as mc
    from stencil.focus3 import Runtime

    topics = mc.load_topics()
    classifier = mc.frozen_classifier()
    items = load_items()
    if args.limit:
        items = items[: args.limit]
    totals = {"admitted": 0, "relations_applied": 0, "overflow": 0, "items": 0}
    for item in items:
        path = OUT / "auto" / f"item-{item['id']}.json"
        if path.exists() and not args.force:
            saved = json.loads(path.read_text())
            # The error table is label-derived and cheap: recompute it from the
            # saved rows so a detector amendment never needs a classifier rerun.
            dialogue = mc.load_dialogue(item["dialogue"])
            saved["errors"] = error_table(dialogue, item["session"], saved, topics, mc)
            _write_atomic(path, saved)
        else:
            dialogue = mc.load_dialogue(item["dialogue"])
            auto = mc.auto_live(dialogue, item["session"], Runtime(classifier))
            saved = {
                "id": item["id"],
                "split": item["split"],
                "sentences": auto["sentences"],
                "admitted": auto["admitted"],
                "relations_applied": auto["relations_applied"],
                "overflow": auto["overflow"],
                "update_calls": auto["update_calls"],
                "rows": auto["rows"],
                "turns": auto["turns"],
                "errors": error_table(dialogue, item["session"], auto, topics, mc),
            }
            _write_atomic(path, saved)
        totals["admitted"] += saved["admitted"]
        totals["relations_applied"] += saved["relations_applied"]
        totals["overflow"] += saved["overflow"]
        totals["items"] += 1
        print(
            f"{item['id']}: live {len(saved['sentences'])} admitted "
            f"{saved['admitted']} relations {saved['relations_applied']} "
            f"overflow {saved['overflow']}",
            flush=True,
        )
    setup_paths = [OUT / "auto" / f"item-{it['id']}.json" for it in load_items("setup")]
    setup = [json.loads(p.read_text()) for p in setup_paths if p.exists()]
    non_vacuous = {
        "setup_items": len(setup),
        "setup_admitted": sum(a["admitted"] for a in setup),
        "setup_relations_applied": sum(a["relations_applied"] for a in setup),
    }
    non_vacuous["active"] = (
        len(setup) == len(setup_paths)
        and non_vacuous["setup_admitted"] >= 1
        and non_vacuous["setup_relations_applied"] >= 1
    )
    summary = {"totals": totals, "non_vacuous_check": non_vacuous}
    _write_atomic(OUT / "auto" / "summary.json", summary)
    print(json.dumps(summary, indent=1))
    return summary


# -------------------------------------------------------------------------------- run


def load_model(size: str):
    import torch

    from stencil import determinism
    from stencil.qwen3 import Qwen3, Qwen3Config

    determinism.assert_gpu_free_or_owned()
    if size == "1.7b":
        model = Qwen3()
        weights = ROOT / "models/qwen3-1.7b.pt"
    else:
        model = Qwen3(Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json"))
        weights = ROOT / "models/qwen3-4b.pt"
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
    return model.to(torch.bfloat16).cuda().eval()


def generate(model, tokenizer, prompt: str, max_new: int, deadline: float) -> dict:
    """Greedy generation from the full prompt (no eviction, no bias)."""
    import torch

    from stencil.bench import EOS
    from stencil.qwen3 import KVCache

    ids = tokenizer.encode(prompt).ids
    device = next(model.parameters()).device
    cache = KVCache(model.cfg)
    generated: list[int] = []
    started = time.monotonic()
    timed_out = False
    with torch.no_grad():
        logits = model(torch.tensor([ids], device=device), cache=cache)
        next_token = int(logits[0, -1].argmax())
        while next_token not in EOS and len(generated) < max_new:
            if time.monotonic() - started > deadline:
                timed_out = True
                break
            generated.append(next_token)
            logits = model(torch.tensor([[next_token]], device=device), cache=cache)
            next_token = int(logits[0, -1].argmax())
    return {
        "text": tokenizer.decode(generated, skip_special_tokens=False),
        "generated_token_ids": generated,
        "prompt_tokens": len(ids),
        "n_generated": len(generated),
        "timed_out": timed_out,
        "truncated": len(generated) >= max_new,
        "seconds": time.monotonic() - started,
    }


def arm_sentences(item: dict, arm: str, dialogue: dict, topics: dict, mc) -> list[str]:
    s = item["session"]
    if arm == "history":
        return []
    if arm == "restate_all":
        return [c["text"] for c in mc.mentor_sentences(dialogue, s)]
    if arm == "auto":
        path = OUT / "auto" / f"item-{item['id']}.json"
        return json.loads(path.read_text())["sentences"]
    if arm == "oracle":
        return mc.oracle_sentences(dialogue, s, topics)
    raise ValueError(arm)


def _out_dir(args) -> Path:
    return OUT / (args.split if args.model == "1.7b" else f"{args.split}-{args.model}")


def phase_run(args) -> None:
    from stencil import memorycode as mc

    topics = mc.load_topics()
    compute_score = mc.vendored_checker()
    tokenizer = _tokenizer()
    items = load_items(args.split)[args.start :]
    if args.limit:
        items = items[: args.limit]
    out_dir = _out_dir(args)
    started = time.monotonic()
    model = None
    for item in items:
        path = out_dir / f"item-{item['id']}.json"
        if path.exists() and not args.force:
            continue
        elapsed_min = (time.monotonic() - started) / 60
        if args.budget_minutes and elapsed_min > args.budget_minutes - 5:
            print(f"stopping: {elapsed_min:.1f} min elapsed of {args.budget_minutes}")
            break
        if model is None:
            model = load_model(args.model)
        dialogue = mc.load_dialogue(item["dialogue"])
        record = {
            "id": item["id"],
            "split": item["split"],
            "model": args.model,
            "session": item["session"],
            "queries": item["queries"],
            "history_regex": item["history_regex"],
            "arms": {},
        }
        for arm in args.arms:
            selected = arm_sentences(item, arm, dialogue, topics, mc)
            kept, reminder_tokens = mc.pack_newest_first(selected, tokenizer)
            reminder = mc.render_reminder(kept)
            generations = []
            for query in item["queries"]:
                prompt = mc.chat_prompt(
                    mc.user_message(dialogue, item["session"], query, arm, reminder)
                )
                gen = generate(model, tokenizer, prompt, args.max_new, args.deadline)
                gen["query"] = query
                gen["scores"] = mc.score_generation(
                    gen["text"],
                    item["history_regex"],
                    compute_score,
                    required=item["required"][query],
                    structure=item["structure"][query],
                )
                generations.append(gen)
            stricts = [g["scores"]["strict"] for g in generations]
            stricts = [x for x in stricts if x is not None]
            fractions = [g["scores"]["fraction"] for g in generations]
            fractions = [x for x in fractions if x is not None]
            record["arms"][arm] = {
                "selected_sentences": len(selected),
                "kept_sentences": len(kept),
                "reminder_tokens": reminder_tokens,
                "reminder_empty": not kept,
                "generations": generations,
                "strict": all(stricts) if stricts else None,
                "fraction": sum(fractions) / len(fractions) if fractions else None,
            }
            print(
                f"{item['id']} {arm}: strict={record['arms'][arm]['strict']} "
                f"frac={record['arms'][arm]['fraction']} "
                f"kept={len(kept)}/{len(selected)} tokens={reminder_tokens}",
                flush=True,
            )
        _write_atomic(path, record)


# ---------------------------------------------------------------------------- summary


def _mcnemar(pairs: list[tuple[bool, bool]]) -> dict:
    from scipy.stats import binomtest

    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    n = b + c
    return {
        "first_only": b,
        "second_only": c,
        "discordant": n,
        "p_two_sided": float(binomtest(b, n, 0.5).pvalue) if n else 1.0,
    }


def _clopper_pearson(k: int, n: int, conf: float = 0.975) -> tuple[float, float]:
    from scipy.stats import beta

    if n == 0:
        return 0.0, 1.0
    alpha = 1 - conf
    lo = float(beta.ppf(alpha / 2, k, n - k + 1)) if k > 0 else 0.0
    hi = float(beta.ppf(1 - alpha / 2, k + 1, n - k)) if k < n else 1.0
    return lo, hi


def _paired_interval(pairs: list[tuple[bool, bool]]) -> dict:
    """Conservative paired interval (results/astra-research-blockers.md:199):
    separate 97.5% Clopper-Pearson intervals for b/N and c/N; difference by union
    bound. Difference = first − second, in points of N."""
    n = len(pairs)
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    b_lo, b_hi = _clopper_pearson(b, n)
    c_lo, c_hi = _clopper_pearson(c, n)
    return {
        "n": n,
        "difference_points": 100 * (b - c) / n if n else None,
        "lower_points": 100 * (b_lo - c_hi),
        "upper_points": 100 * (b_hi - c_lo),
    }


def phase_summarize(args) -> dict:
    out_dir = _out_dir(args)
    records = [json.loads(p.read_text()) for p in sorted(out_dir.glob("item-*.json"))]
    expected = len(load_items(args.split))
    strict = {arm: {} for arm in ARMS}
    fraction = {arm: {} for arm in ARMS}
    inapplicable = 0
    items_by_id = {it["id"]: it for it in load_items(args.split)}
    for rec in records:
        # Primary cohort frozen BEFORE generation (CONTRACT.md amendment 3): an item
        # is inapplicable only when no query requires any of its families.
        item = items_by_id[rec["id"]]
        if not any(item["required"].get(q) for q in item["queries"]):
            inapplicable += 1
            continue
        for arm in ARMS:
            value = rec["arms"][arm]["strict"]
            strict[arm][rec["id"]] = bool(value) if value is not None else False
            fraction[arm][rec["id"]] = rec["arms"][arm]["fraction"] or 0.0
    ids = sorted(strict["history"])
    n = len(ids)
    summary = {
        "split": args.split,
        "model": args.model,
        "items_expected": expected,
        "items_complete": len(records),
        "items_scored": n,
        "items_inapplicable": inapplicable,
        "complete": len(records) == expected,
        "strict_compliance": {arm: sum(strict[arm].values()) for arm in ARMS},
        "mean_fraction": {
            arm: (sum(fraction[arm].values()) / n if n else None) for arm in ARMS
        },
        "reminder": {
            arm: {
                "empty": sum(1 for r in records if r["arms"][arm]["reminder_empty"]),
                "mean_tokens": (
                    sum(r["arms"][arm]["reminder_tokens"] for r in records)
                    / len(records)
                    if records
                    else None
                ),
            }
            for arm in ARMS
        },
    }

    def pairs(a, b):
        return [(strict[a][i], strict[b][i]) for i in ids]

    contrasts = {}
    for a, b in [
        ("auto", "restate_all"),
        ("auto", "oracle"),
        ("oracle", "history"),
        ("restate_all", "history"),
        ("auto", "history"),
    ]:
        contrasts[f"{a}_vs_{b}"] = {
            "mcnemar": _mcnemar(pairs(a, b)),
            "paired_interval": _paired_interval(pairs(a, b)),
        }
    summary["contrasts"] = contrasts
    if args.split == "setup":
        h = summary["strict_compliance"]["history"]
        summary["eligibility"] = {
            "history_strict": h,
            "threshold": 6,
            "eligible": h >= 6 and summary["complete"],
            "retention_headroom_oracle_minus_history": (
                summary["strict_compliance"]["oracle"] - h
            ),
        }
    else:
        lower = contrasts["auto_vs_restate_all"]["paired_interval"]["lower_points"]
        summary["reading"] = {
            "primary": "auto vs restate_all, exact McNemar two-sided",
            "lower_bound_points": lower,
            "ship_auto_screen_level": lower > -2,
            "note": (
                "N=64 is a SCREEN; a positive triggers a registered N=256 follow-up; "
                "a null is 'not demonstrated at N=64'."
            ),
        }
    auto_summary = OUT / "auto" / "summary.json"
    if auto_summary.exists():
        summary["auto_non_vacuous_check"] = json.loads(auto_summary.read_text())[
            "non_vacuous_check"
        ]
        errors = {
            "false_admissions": 0,
            "missed_instructions": 0,
            "missed_updates": 0,
            "overflow_events": 0,
        }
        for rec in records:
            e = json.loads((OUT / "auto" / f"item-{rec['id']}.json").read_text())[
                "errors"
            ]
            errors["false_admissions"] += len(e["false_admissions"])
            errors["missed_instructions"] += len(e["missed_instructions"])
            errors["missed_updates"] += len(e["missed_updates"])
            errors["overflow_events"] += e["overflow_events"]
        summary["auto_error_table"] = errors
    summary["git_sha"] = _git_sha()
    _write_atomic(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=1))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("phase", choices=["items", "auto", "run", "summarize"])
    parser.add_argument("--split", choices=["setup", "screen"], default="setup")
    parser.add_argument("--model", choices=["1.7b", "4b"], default="1.7b")
    parser.add_argument("--arms", nargs="+", default=ARMS)
    parser.add_argument("--n-setup", type=int, default=16)
    parser.add_argument("--n-screen", type=int, default=64)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-new", type=int, default=MAX_NEW)
    parser.add_argument("--deadline", type=float, default=DEADLINE)
    parser.add_argument("--budget-minutes", type=float, default=0.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    {
        "items": phase_items,
        "auto": phase_auto,
        "run": phase_run,
        "summarize": phase_summarize,
    }[args.phase](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

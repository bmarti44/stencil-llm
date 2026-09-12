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
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "memorycode-derived"
OUT_LONG = ROOT / "results" / "memorycode-long"
MAX_NEW = 512
DEADLINE = 300.0
ARMS = ["history", "restate_all", "auto", "oracle"]
ARMS_LONG = ["base", "focus", "oracle"]


def out_root(args) -> Path:
    return OUT_LONG if getattr(args, "cohort", "short") == "long" else OUT


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
    split = mc.split_items(items, n_setup=args.n_setup, n_screen=args.n_screen or 64)
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


def load_items(split: str | None = None, root: Path = OUT) -> list[dict]:
    items = json.loads((root / "items.json").read_text())["items"]
    return [it for it in items if split is None or it["split"] == split]


def phase_long_items(args) -> dict:
    from stencil import memorycode as mc

    tokenizer = _tokenizer()
    items = mc.long_items(tokenizer)
    split = mc.split_long(items, n_setup=args.n_setup, n_screen=args.n_screen or 128)
    for name in ("setup_long", "screen_long"):
        for item in split[name]:
            item["id"] = f"{item['dialogue']}-{item['session']}"
            item["split"] = name
    payload = {
        "registration": "results/memorycode-long/REGISTRATION.md",
        "vendor_sha": "1ab87e119b2f9a498de8075219e1c07f6041b394",
        "window_tokens": mc.WINDOW,
        "reminder_budget_tokens": mc.BUDGET,
        "n_long_items": split["n_long_items"],
        "n_reserve": split["reserve"],
        "items": split["setup_long"] + split["screen_long"],
    }
    _write_atomic(OUT_LONG / "items.json", payload)
    print(
        f"long items {split['n_long_items']}; setup_long {len(split['setup_long'])}, "
        f"screen_long {len(split['screen_long'])}, reserve {split['reserve']}"
    )
    return payload


# ------------------------------------------------------------------------------- auto


def _introduced(dialogue: dict, i: int, mc) -> list[tuple[int, int]]:
    """Pairs introduced or updated in session ``i`` (per-session events)."""
    return mc.instruction_events(dialogue, i)


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
            older = [v for q, v in mc.live_instructions(dialogue, i - 1) if q == p]
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
    root = out_root(args)
    items = load_items(root=root)
    if args.limit:
        items = items[: args.limit]
    if args.ids:
        items = [it for it in items if it["id"] in set(args.ids)]
    totals = {"admitted": 0, "relations_applied": 0, "overflow": 0, "items": 0}
    for item in items:
        path = root / "auto" / f"item-{item['id']}.json"
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
    setup_split = "setup_long" if root == OUT_LONG else "setup"
    setup_paths = [
        root / "auto" / f"item-{it['id']}.json"
        for it in load_items(setup_split, root=root)
    ]
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
    _write_atomic(root / "auto" / "summary.json", summary)
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
    seconds = time.monotonic() - started
    # Exp 4 amendment 2: an overrun is a timeout even when the loop ended at EOS or
    # the cap on the same step; the reason is recorded unambiguously.
    timed_out = timed_out or seconds > deadline
    truncated = len(generated) >= max_new
    if timed_out:
        termination = "timeout"
    elif truncated:
        termination = "cap"
    else:
        termination = "eos"
    return {
        "text": tokenizer.decode(generated, skip_special_tokens=False),
        "generated_token_ids": generated,
        "prompt_tokens": len(ids),
        "n_generated": len(generated),
        "timed_out": timed_out,
        "truncated": truncated,
        "termination": termination,
        "seconds": seconds,
    }


def arm_sentences(
    item: dict,
    arm: str,
    dialogue: dict,
    topics: dict,
    mc,
    root: Path = OUT,
    policy: str = "register",
    thread_kept: int | None = None,
) -> list[str]:
    """Reminder candidates per arm; for ``focus``/``role_evicted`` ``thread_kept``
    is the base window's cut offset in characters (``cut_chars``)."""
    s = item["session"]
    if arm in ("history", "base"):
        return []
    if arm == "focus":
        if policy == "role_evicted":
            assert thread_kept is not None
            return mc.evicted_mentor_sentences(dialogue, s, cut=thread_kept)
        path = root / "auto" / f"item-{item['id']}.json"
        return json.loads(path.read_text())["sentences"]
    if arm == "restate_all":
        return [c["text"] for c in mc.mentor_sentences(dialogue, s)]
    if arm == "auto":
        path = root / "auto" / f"item-{item['id']}.json"
        return json.loads(path.read_text())["sentences"]
    if arm == "oracle":
        return mc.oracle_sentences(dialogue, s, topics)
    raise ValueError(arm)


def _out_dir(args) -> Path:
    root = out_root(args)
    name = args.split if args.model == "1.7b" else f"{args.split}-{args.model}"
    if getattr(args, "policy", "register") != "register":
        name = f"{name}-{args.policy}"
    return root / name


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_manifest(args, root: Path) -> dict:
    """Generation-time identities stored in every record (Exp 4 amendment 2)."""
    weights = ROOT / (
        "models/qwen3-1.7b.pt" if args.model == "1.7b" else "models/qwen3-4b.pt"
    )
    return {
        "git_sha": _git_sha(),
        "items_sha256": _sha256(root / "items.json"),
        "tokenizer_sha256": _sha256(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"),
        "weights_sha256": _sha256(weights),
        "model": args.model,
        "policy": args.policy,
        "decoding": {
            "greedy": True,
            "max_new": args.max_new,
            "deadline": args.deadline,
        },
        "window": getattr(args, "window", None),
        "budget_tokens": None,
    }


def _record_matches(record: dict, manifest: dict) -> bool:
    m = record.get("manifest")
    if not m:
        # Legacy record (written before amendment 2 added manifests): the only
        # configuration it carries is the model; accept it when that matches and the
        # caller adds the current manifest on the next write (disclosed in the ledger).
        return record.get("model") == manifest.get("model")
    keys = (
        "items_sha256",
        "tokenizer_sha256",
        "weights_sha256",
        "model",
        "policy",
        "decoding",
        "window",
        "budget_tokens",
    )
    return all(m.get(k) == manifest.get(k) for k in keys)


def _generation_seconds(out_dir: Path, arms=None) -> float:
    """Cumulative generation seconds over every terminal generation saved under
    ``out_dir`` (all chunks), restricted to ``arms`` when given (Exp 4B review
    finding 6: the registered ceiling is enforced across resumptions)."""
    total = 0.0
    for p in out_dir.glob("item-*.json"):
        rec = json.loads(p.read_text())
        for arm, data in rec["arms"].items():
            if arms and arm not in arms:
                continue
            for gen in data.get("generations", []):
                total += float(gen.get("seconds", 0.0))
    return total


def _ceiling_marker(out_dir: Path) -> Path:
    return out_dir / "BUDGET_EXHAUSTED.json"


def phase_run(args) -> None:
    from stencil import memorycode as mc

    topics = mc.load_topics()
    compute_score = mc.vendored_checker()
    tokenizer = _tokenizer()
    root = out_root(args)
    long = args.cohort == "long"
    if long and args.budget_minutes <= 0:
        raise SystemExit("--budget-minutes must be positive for the LONG cohort")
    args.window = mc.WINDOW if long else mc.MAX_PROMPT_TOKENS
    manifest = run_manifest(args, root)
    manifest["budget_tokens"] = mc.BUDGET
    items = load_items(args.split, root=root)[args.start :]
    if args.limit:
        items = items[: args.limit]
    if args.ids:
        items = [it for it in items if it["id"] in set(args.ids)]
    out_dir = _out_dir(args)
    started = args.started_at or time.monotonic()
    model = None
    for item in items:
        path = out_dir / f"item-{item['id']}.json"
        record = None
        if path.exists() and not args.force:
            record = json.loads(path.read_text())
            if not _record_matches(record, manifest):
                raise SystemExit(
                    f"{path}: existing record was made under another configuration"
                )
            record.setdefault("manifest", manifest)
        missing = [
            a
            for a in args.arms
            if not record or a not in record["arms"] or a in (args.redo_arms or [])
        ]
        if not missing:
            continue
        # Registered cumulative ceiling across chunks (Exp 4B): reconstruct the spend
        # from every saved terminal generation; exhaustion is INCOMPLETE, never rescued.
        if args.ceiling_seconds:
            spent = _generation_seconds(out_dir, args.arms)
            if spent >= args.ceiling_seconds or _ceiling_marker(out_dir).exists():
                _write_atomic(
                    _ceiling_marker(out_dir),
                    {
                        "cumulative_generation_seconds": spent,
                        "ceiling_seconds": args.ceiling_seconds,
                        "arms": list(args.arms),
                        "stopped_before_item": item["id"],
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    },
                )
                print(
                    f"stopping: ceiling {args.ceiling_seconds:.1f} s "
                    f"reached ({spent:.1f} s)"
                )
                break
        # Stop STARTING items when the remaining required arms cannot finish inside
        # the budget (each arm may spend the full deadline), amendment 2.
        elapsed_min = (time.monotonic() - started) / 60
        needed_min = len(missing) * args.deadline / 60
        if args.budget_minutes and elapsed_min >= args.budget_minutes - needed_min:
            print(
                f"stopping: {elapsed_min:.1f} min elapsed of {args.budget_minutes}; "
                f"next item needs up to {needed_min:.1f} min"
            )
            break
        if model is None:
            model = load_model(args.model)
        dialogue = mc.load_dialogue(item["dialogue"])
        if record is None:
            record = {
                "id": item["id"],
                "split": item["split"],
                "model": args.model,
                "session": item["session"],
                "queries": item["queries"],
                "history_regex": item["history_regex"],
                "manifest": manifest,
                "arms": {},
            }
        thread_kept = None
        base_tokens = None
        if long:
            base_built = mc.build_long_prompt(
                dialogue, item["session"], item["queries"][0], tokenizer, ""
            )
            thread_kept = base_built["cut_chars"]
            base_tokens = base_built["prompt_tokens"]
        for arm in missing:
            selected = arm_sentences(
                item,
                arm,
                dialogue,
                topics,
                mc,
                root=root,
                policy=args.policy,
                thread_kept=thread_kept,
            )
            if long:
                kept, reminder_tokens = mc.pack_long(selected, tokenizer)
                reminder = mc.render_long_reminder(kept)
            else:
                kept, reminder_tokens = mc.pack_newest_first(selected, tokenizer)
                reminder = mc.render_reminder(kept)
            generations = []
            for query in item["queries"]:
                if long:
                    built = mc.build_long_prompt(
                        dialogue, item["session"], query, tokenizer, reminder
                    )
                    prompt = built["prompt"]
                    # Paired equality asserted BEFORE generation (amendment 2).
                    if built["prompt_tokens"] != base_tokens:
                        raise SystemExit(
                            f"item {item['id']} arm {arm}: prompt "
                            f"{built['prompt_tokens']} tokens != base {base_tokens}"
                        )
                else:
                    built = None
                    prompt = mc.chat_prompt(
                        mc.user_message(dialogue, item["session"], query, arm, reminder)
                    )
                gen = generate(model, tokenizer, prompt, args.max_new, args.deadline)
                gen["query"] = query
                gen["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
                if built is not None:
                    gen["window"] = {
                        k: v
                        for k, v in built.items()
                        if k not in ("prompt", "thread_text_kept")
                    }
                gen["failures"] = mc.output_failures(
                    gen["text"],
                    gen["generated_token_ids"],
                    gen["truncated"],
                    gen["timed_out"],
                )
                gen["scores"] = mc.score_generation(
                    gen["text"],
                    item["history_regex"],
                    compute_score,
                    required=item["required"][query],
                    structure=item["structure"][query],
                )
                if gen["timed_out"]:
                    # Registered timeout rule: a terminal strict failure, never rerun;
                    # 0.0 on the Exp 4B per-constraint primary when anything is
                    # required.
                    gen["scores"]["strict"] = False
                    if gen["scores"].get("fraction_required") is not None:
                        gen["scores"]["fraction_required"] = 0.0
                generations.append(gen)
            stricts = [g["scores"]["strict"] for g in generations]
            stricts = [x for x in stricts if x is not None]
            fractions = [g["scores"]["fraction"] for g in generations]
            fractions = [x for x in fractions if x is not None]
            record["arms"][arm] = {
                "policy": args.policy if arm == "focus" else None,
                "selected_sentences": len(selected),
                "kept_sentences": len(kept),
                "reminder": reminder,
                "reminder_tokens": reminder_tokens,
                "reminder_empty": not kept,
                "generations": generations,
                "strict": all(stricts) if stricts else None,
                "fraction": sum(fractions) / len(fractions) if fractions else None,
            }
            print(
                f"{item['id']} {arm}: strict={record['arms'][arm]['strict']} "
                f"frac={record['arms'][arm]['fraction']} "
                f"kept={len(kept)}/{len(selected)} tokens={reminder_tokens} "
                f"end={generations[0]['termination']}",
                flush=True,
            )
            # Checkpoint after every terminal arm (amendment 2).
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


def _paired_mean_bootstrap(
    a: list[float], b: list[float], draws: int = 10_000, seed: int = 0
) -> dict:
    """Paired mean difference a − b (points of 100) with a 95% percentile bootstrap
    over items (rng seed 0, 10,000 draws) and an exact sign test on discordant items
    (Exp 4B registration)."""
    import random

    from scipy.stats import binomtest

    if len(a) != len(b):
        raise ValueError(f"paired inputs of unequal length: {len(a)} vs {len(b)}")
    diffs = [100 * (x - y) for x, y in zip(a, b)]
    n = len(diffs)
    if n == 0:
        return {
            "n": 0,
            "mean_points": None,
            "lower_points": None,
            "upper_points": None,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "sign_p_two_sided": 1.0,
            "draws": draws,
            "seed": seed,
        }
    rng = random.Random(seed)
    means = []
    for _ in range(draws):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    return {
        "n": n,
        "mean_points": sum(diffs) / n,
        # order statistics 251 and 9750 of 10,000 sorted bootstrap means (registered
        # central-order-statistic convention; 250 draws trimmed from either end)
        "lower_points": means[int(0.025 * draws)],
        "upper_points": means[int(0.975 * draws) - 1],
        "wins": wins,
        "losses": losses,
        "ties": n - wins - losses,
        "sign_p_two_sided": (
            float(binomtest(wins, wins + losses, 0.5).pvalue) if wins + losses else 1.0
        ),
        "draws": draws,
        "seed": seed,
    }


def fraction_reading(summary: dict) -> dict:
    """Exhaustive readings of the Exp 4B registration (per-constraint primary)."""
    ci = summary["contrasts"]["focus_vs_base"]["fraction_required_bootstrap"]
    lower, upper = ci["lower_points"], ci["upper_points"]
    excess = summary["output_failure_excess_over_base"]["focus"]["excess_fraction"]
    # Exp 4B confirmatory reading: SCREEN-LONG, role_evicted, Qwen3-4B only.
    confirmatory = (
        summary["split"] == "screen_long"
        and summary["policy"] == "role_evicted"
        and summary["model"] == "4b"
    )
    if not summary["primary_complete"] or lower is None:
        verdict = "INCOMPLETE"
    elif not confirmatory:
        verdict = "DESCRIPTIVE"
    elif lower > 0 and excess <= 0.05:
        verdict = "PROVEN"
    elif lower > 0:
        verdict = "POSITIVE-WITH-OUTPUT-FAILURE-EXCESS"
    elif upper < 0:
        verdict = "HARM"
    else:
        verdict = "NOT PROVEN"
    return {
        "verdict": verdict,
        "primary": "fraction_required (frozen denominator), focus − base",
        "confirmatory": confirmatory and summary["primary_complete"],
        "n_primary": ci["n"],
        "mean_points": ci["mean_points"],
        "lower_points": lower,
        "upper_points": upper,
        "focus_excess_failure_fraction": excess,
        "budget_exhausted": summary.get("budget", {}).get("exhausted", False),
        "invalid_records": summary.get("invalid_record_ids", []),
        "note": (
            f"N={ci['n']} of {summary['items_expected']} frozen items; 95% percentile "
            "bootstrap over items (order statistics 251/9750 of 10,000); the sign test "
            "is a descriptive directional companion; strict reported alongside; "
            "NOT PROVEN is final."
        ),
    }


def _record_invalid_reason(rec: dict, arms, manifest_expect: dict) -> str | None:
    """Why a record cannot enter a confirmatory summary (Exp 4B review finding 4):
    missing or mismatching manifest (model / window / reminder budget), or a primary
    arm whose first generation is not a terminal, scored generation."""
    m = rec.get("manifest")
    if not m:
        return "no manifest"
    for key, want in manifest_expect.items():
        if m.get(key) != want:
            return f"manifest {key}={m.get(key)!r} != {want!r}"
    for arm in arms:
        if arm not in rec["arms"]:
            continue
        gens = rec["arms"][arm].get("generations") or []
        if not gens:
            return f"{arm}: no generation"
        gen = gens[0]
        if gen.get("termination") not in ("eos", "cap", "timeout"):
            return f"{arm}: non-terminal generation"
        scores = gen.get("scores")
        if not scores or "per_family" not in scores:
            return f"{arm}: unscored generation"
    return None


def qualification_reading(summary: dict, records: list[dict], frozen_ids) -> dict:
    """Exp 4B registration item 3: the SCREEN launches only when every frozen
    SETUP-LONG item has valid terminal base/focus/oracle records AND (a) oracle mean
    fraction_required ≥ 0.20, (b) focus-only output-failure discordance ≤ 5%,
    (c) the focus − base bootstrap upper bound > 0. Missing records = INCOMPLETE,
    never a pass or a fail. upper == 0 fails (c) without demonstrating harm."""
    three = {r["id"] for r in records if all(a in r["arms"] for a in ARMS_LONG)}
    complete = (
        three == set(frozen_ids)
        and summary["primary_complete"]
        and summary["items_scored"] == len(frozen_ids)
    )
    oracle_mean = summary["mean_fraction_required"].get("oracle")
    excess = summary["output_failure_excess_over_base"]["focus"]["excess_fraction"]
    upper = summary["contrasts"]["focus_vs_base"]["fraction_required_bootstrap"][
        "upper_points"
    ]
    conditions = {
        "oracle_mean_fraction_required_ge_0.20": (
            oracle_mean is not None and oracle_mean >= 0.20
        ),
        "focus_only_failure_excess_le_0.05": excess <= 0.05,
        "focus_minus_base_upper_gt_0": upper is not None and upper > 0,
    }
    if not complete:
        status = "INCOMPLETE"
    elif all(conditions.values()):
        status = "PASSED"
    else:
        status = "FAILED"
    return {
        "status": status,
        "complete": complete,
        "passed": all(conditions.values()) if complete else None,
        "conditions": conditions,
        "values": {
            "oracle_mean_fraction_required": oracle_mean,
            "focus_excess_failure_fraction": excess,
            "focus_minus_base_upper_points": upper,
        },
        "items_with_three_arms": len(three),
        "missing_three_arm_ids": sorted(set(frozen_ids) - three),
        "note": (
            "SCREEN-LONG launches only on PASSED; FAILED publishes SETUP-LONG as the "
            "negative and the program stops; INCOMPLETE is neither."
        ),
    }


def _required_fraction_of(rec: dict, arm: str, item: dict) -> float:
    """fraction_required of the first generation, recomputed from the saved
    per-family scores when the record predates the field. A terminal timeout scores
    0.0 on the primary (Exp 4B BUDGET line), also on recomputation."""
    gen = rec["arms"][arm]["generations"][0]
    if gen.get("timed_out"):
        return 0.0
    if "scores" not in gen:  # record without per-family scores (never confirmatory)
        return rec["arms"][arm].get("fraction") or 0.0
    value = gen["scores"].get("fraction_required")
    if value is None and "fraction_required" not in gen["scores"]:
        from stencil.memorycode import fraction_required

        value = fraction_required(
            gen["scores"]["per_family"],
            item["history_regex"],
            item["required"][gen["query"]],
            gen["scores"]["structure_present"],
        )
    return value if value is not None else 0.0


def _failure_excess(records: list[dict], arms: list[str], reference: str) -> dict:
    """Per-arm output failures relative to the reference arm (Exp 4 amendment 2).
    The registered guard is the ARM-ONLY DISCORDANCE RATE: items where the arm fails
    (any of invalid/truncated/degenerate/timed_out) and the reference does not,
    divided by all items. Both discordance directions, the net rate difference and
    the per-category counts are published alongside."""
    from stencil.memorycode import FAILURE_COLUMNS, any_failure

    def fails(rec, a):
        return any_failure(rec["arms"][a]["generations"][0]["failures"])

    out = {}
    for arm in arms:
        recs = [r for r in records if arm in r["arms"] and reference in r["arms"]]
        n = len(recs)
        arm_only = sum(int(fails(r, arm) and not fails(r, reference)) for r in recs)
        ref_only = sum(int(fails(r, reference) and not fails(r, arm)) for r in recs)
        out[arm] = {
            "n": n,
            "excess_items": arm_only,
            "excess_fraction": arm_only / n if n else 0.0,
            "reference_only_items": ref_only,
            "net_rate_difference": (arm_only - ref_only) / n if n else 0.0,
            "categories": {
                k: sum(
                    int(r["arms"][arm]["generations"][0]["failures"].get(k, False))
                    for r in recs
                )
                for k in FAILURE_COLUMNS
            },
        }
    return out


def long_reading(summary: dict) -> dict:
    """Exhaustive readings of plan rev 7.1 section H, amended: confirmatory only for
    the complete SCREEN-LONG run under the registered primary policy; INCOMPLETE
    whenever a frozen primary item lacks a terminal base or focus record;
    DESCRIPTIVE for every other split/policy."""
    ci = summary["contrasts"]["focus_vs_base"]["paired_interval"]
    lower, upper = ci["lower_points"], ci["upper_points"]
    excess = summary["output_failure_excess_over_base"]["focus"]["excess_fraction"]
    confirmatory = (
        summary["split"] == "screen_long" and summary["policy"] == "role_evicted"
    )
    if not summary["primary_complete"]:
        verdict = "INCOMPLETE"
    elif not confirmatory:
        verdict = "DESCRIPTIVE"
    elif lower > 0 and excess <= 0.05:
        verdict = "PROVEN"
    elif lower > 0:
        verdict = "POSITIVE-WITH-OUTPUT-FAILURE-EXCESS"
    elif upper < 0:
        verdict = "HARM"
    else:
        verdict = "NOT PROVEN"
    return {
        "verdict": verdict,
        "confirmatory": confirmatory and summary["primary_complete"],
        "n_primary": ci["n"],
        "lower_points": lower,
        "upper_points": upper,
        "focus_excess_failure_fraction": excess,
        "note": (
            f"N={ci['n']} of {summary['items_expected']} frozen items; union-bound "
            "paired interval; one primary policy (role_evicted, Exp 4 registration "
            "amendment 1); NOT PROVEN is final; oracle is descriptive."
        ),
    }


def phase_summarize(args) -> dict:
    out_dir = _out_dir(args)
    root = out_root(args)
    long = args.cohort == "long"
    arms = ARMS_LONG if long else ARMS
    primary_arms = ("base", "focus") if long else tuple(ARMS)
    reference = "base" if long else "history"
    frozen = load_items(args.split, root=root)
    items_by_id = {it["id"]: it for it in frozen}
    expected = len(frozen)
    records = [json.loads(p.read_text()) for p in sorted(out_dir.glob("item-*.json"))]
    # Primary completeness = every frozen item has a terminal record for every
    # PRIMARY arm; ancillary arms (oracle) are descriptive on their own subset.
    records = [
        r
        for r in records
        if r["id"] in items_by_id and all(a in r["arms"] for a in primary_arms)
    ]
    # Record validity (Exp 4B review finding 4): the summary trusts no CLI label; a
    # record enters only when its manifest names this model, the registered window
    # and reminder budget, and every arm's first generation is terminal and scored.
    invalid = {}
    if long:
        from stencil import memorycode as mc

        expect = {"model": args.model, "window": mc.WINDOW, "budget_tokens": mc.BUDGET}
        for r in records:
            why = _record_invalid_reason(r, arms, expect)
            if why:
                invalid[r["id"]] = why
        records = [r for r in records if r["id"] not in invalid]
    primary_ids = {r["id"] for r in records}
    primary_complete = primary_ids == set(items_by_id) and not invalid
    strict = {arm: {} for arm in arms}
    fraction = {arm: {} for arm in arms}
    required_fraction = {arm: {} for arm in arms}
    inapplicable = 0
    for rec in records:
        # Primary cohort frozen BEFORE generation (CONTRACT.md amendment 3): an item
        # is inapplicable only when no query requires any of its families.
        item = items_by_id[rec["id"]]
        if not any(item["required"].get(q) for q in item["queries"]):
            inapplicable += 1
            continue
        for arm in arms:
            if arm not in rec["arms"]:
                continue
            value = rec["arms"][arm]["strict"]
            strict[arm][rec["id"]] = bool(value) if value is not None else False
            fraction[arm][rec["id"]] = rec["arms"][arm]["fraction"] or 0.0
            required_fraction[arm][rec["id"]] = _required_fraction_of(rec, arm, item)
    ids = sorted(strict[reference])
    n = len(ids)
    # The registered N is the whole frozen cohort: an inapplicable item breaks
    # completeness instead of silently shrinking the primary (finding 4).
    primary_complete = primary_complete and n == expected
    # Cumulative budget (finding 6): exhaustion is INCOMPLETE even when the last
    # generation that crossed the ceiling completed.
    spent = _generation_seconds(out_dir, primary_arms)
    ceiling = float(getattr(args, "ceiling_seconds", 0.0) or 0.0)
    marker = _ceiling_marker(out_dir)
    budget = {
        "cumulative_generation_seconds_primary_arms": spent,
        "ceiling_seconds": ceiling or None,
        "marker": json.loads(marker.read_text()) if marker.exists() else None,
        "exhausted": marker.exists() or bool(ceiling and spent > ceiling),
    }
    primary_complete = primary_complete and not budget["exhausted"]

    def with_arm(arm):
        return [r for r in records if arm in r["arms"]]

    summary = {
        "split": args.split,
        "model": args.model,
        "policy": getattr(args, "policy", "register"),
        "items_expected": expected,
        "items_complete": len(records),
        "items_scored": n,
        "items_inapplicable": inapplicable,
        "complete": primary_complete,
        "primary_complete": primary_complete,
        "primary_arms": list(primary_arms),
        "missing_primary_ids": sorted(set(items_by_id) - primary_ids),
        "invalid_record_ids": invalid,
        "budget": budget,
        "items_with_arm": {arm: len(with_arm(arm)) for arm in arms},
        "strict_compliance": {arm: sum(strict[arm].values()) for arm in arms},
        "mean_fraction": {
            arm: (
                sum(fraction[arm].values()) / len(fraction[arm])
                if fraction[arm]
                else None
            )
            for arm in arms
        },
        "mean_fraction_required": {
            arm: (
                sum(required_fraction[arm].values()) / len(required_fraction[arm])
                if required_fraction[arm]
                else None
            )
            for arm in arms
        },
        "reminder": {
            arm: {
                "empty": sum(
                    1 for r in with_arm(arm) if r["arms"][arm]["reminder_empty"]
                ),
                "mean_tokens": (
                    sum(r["arms"][arm]["reminder_tokens"] for r in with_arm(arm))
                    / len(with_arm(arm))
                    if with_arm(arm)
                    else None
                ),
            }
            for arm in arms
        },
    }

    def pairs(a, b):
        common = [i for i in ids if i in strict[a] and i in strict[b]]
        return [(strict[a][i], strict[b][i]) for i in common]

    contrasts = {}
    contrast_list = (
        [("focus", "base"), ("oracle", "focus"), ("oracle", "base")]
        if args.cohort == "long"
        else [
            ("auto", "restate_all"),
            ("auto", "oracle"),
            ("oracle", "history"),
            ("restate_all", "history"),
            ("auto", "history"),
        ]
    )
    for a, b in contrast_list:
        common = [i for i in ids if i in strict[a] and i in strict[b]]
        contrasts[f"{a}_vs_{b}"] = {
            "mcnemar": _mcnemar(pairs(a, b)),
            "paired_interval": _paired_interval(pairs(a, b)),
            "fraction_required_bootstrap": _paired_mean_bootstrap(
                [required_fraction[a][i] for i in common],
                [required_fraction[b][i] for i in common],
            ),
        }
    summary["contrasts"] = contrasts
    if args.cohort == "long":
        lengths = [
            (
                r["arms"]["focus"]["generations"][0]["window"]["prompt_tokens"],
                r["arms"]["base"]["generations"][0]["window"]["prompt_tokens"],
            )
            for r in records
        ]
        summary["timeouts"] = {
            arm: sum(
                int(r["arms"][arm]["generations"][0].get("timed_out", False))
                for r in with_arm(arm)
            )
            for arm in arms
        }
        summary["prompt_length_match"] = {
            "max_abs_difference_tokens": max(
                (abs(a - b) for a, b in lengths), default=0
            ),
            "items_with_difference": sum(1 for a, b in lengths if a != b),
        }
        summary["output_failure_excess_over_base"] = _failure_excess(
            records, arms, "base"
        )
        summary["reading"] = (
            fraction_reading(summary)
            if getattr(args, "primary", "strict") == "fraction"
            else long_reading(summary)
        )
        summary["primary"] = getattr(args, "primary", "strict")
        if args.split == "setup_long" and summary["primary"] == "fraction":
            summary["qualification"] = qualification_reading(
                summary, records, sorted(items_by_id)
            )
    elif args.split == "setup":
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
    auto_summary = root / "auto" / "summary.json"
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
            e = json.loads((root / "auto" / f"item-{rec['id']}.json").read_text())[
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
    parser.add_argument(
        "phase", choices=["items", "long-items", "auto", "run", "summarize"]
    )
    parser.add_argument("--cohort", choices=["short", "long"], default="short")
    parser.add_argument(
        "--split",
        choices=["setup", "screen", "setup_long", "screen_long"],
        default="setup",
    )
    parser.add_argument("--model", choices=["1.7b", "4b"], default="1.7b")
    parser.add_argument("--arms", nargs="+", default=None)
    parser.add_argument(
        "--policy",
        choices=["register", "role_evicted"],
        default=None,
        help=(
            "focus-arm reminder policy; LONG default role_evicted (Exp 4 primary, "
            "amendment 1), short default register"
        ),
    )
    parser.add_argument(
        "--started-at",
        type=float,
        default=None,
        help="time.monotonic() value the budget counts from (default: phase entry)",
    )
    parser.add_argument("--n-setup", type=int, default=16)
    parser.add_argument("--n-screen", type=int, default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-new", type=int, default=MAX_NEW)
    parser.add_argument("--deadline", type=float, default=DEADLINE)
    parser.add_argument("--budget-minutes", type=float, default=0.0)
    parser.add_argument(
        "--ceiling-seconds",
        type=float,
        default=0.0,
        help="registered cumulative generation-seconds ceiling over the run's arms "
        "(all chunks); reaching it stops the run and marks it INCOMPLETE",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--primary",
        choices=["strict", "fraction"],
        default="strict",
        help="summarize: registered primary (Exp 4 = strict; Exp 4B = fraction)",
    )
    parser.add_argument(
        "--redo-arms",
        nargs="+",
        default=None,
        help="regenerate these arms even when the record already has them "
        "(instrument repairs under rule D2; disclosed in the ledger)",
    )
    parser.add_argument(
        "--ids", nargs="+", default=None, help="restrict run/auto to these item ids"
    )
    args = parser.parse_args(argv)
    if args.cohort == "long" and not args.split.endswith("_long"):
        args.split = args.split + "_long"
    if args.policy is None:
        args.policy = "role_evicted" if args.cohort == "long" else "register"
    if args.arms is None:
        # Amended execution matrix (Exp 4 amendment 2): SETUP-LONG base/focus/oracle,
        # SCREEN-LONG base/focus (no oracle), the register arm only on request.
        if args.cohort == "long":
            args.arms = ARMS_LONG if args.split == "setup_long" else ["base", "focus"]
        else:
            args.arms = ARMS
    {
        "items": phase_items,
        "long-items": phase_long_items,
        "auto": phase_auto,
        "run": phase_run,
        "summarize": phase_summarize,
    }[args.phase](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Exp 4C technical qualification and timing (REGISTRATION-4C.md, 44 generations).

Prescribed calls, in order:
1. eight TIMING calls through the package: SETUP items 359-99, 352-99, 351-99, 302-49,
   off then on for each; t_max = the maximum elapsed call time;
2. package-off outputs for the other 12 SETUP items (16 off prompts in total);
3. plain upstream ``AutoModelForCausalLM`` on the 16 off prompts under the package's
   EFFECTIVE EOS setting; 16/16 prompt-id and raw-token matches required;
4. reload the package and replay the eight timing calls; 8/8 prompt-byte, prompt-id and
   raw-token matches required.

Evidence discipline (review finding 2): every call is persisted atomically as its own
receipt under results/memorycode-long/qualification-4c/calls/ immediately after it
completes (identity, prompt bytes and ids, raw output incl. EOS, termination, timing,
manifest); an interrupted run resumes only the UNFINISHED prescribed calls under the
same qualification identity and never replaces a completed timing call; models are
released sequentially (references dropped, cache emptied) before the next load; the
report ``qualification-4c.json`` is derived from the receipts. Resident time of every
qualification process, interrupted ones included, is bounded by heartbeat receipts and
limited to the registered 3,600 s by the watchdog. Outputs are NOT scored.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location(
    "memorycode_package_run", ROOT / "scripts" / "memorycode_package_run.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
screen = runner.screen
items4c = runner.items4c

OUT = ROOT / "results" / "memorycode-long"
QDIR = OUT / "qualification-4c"
STAGES = ("timing", "off", "plain", "replay")


def prescribed_calls(setup_ids: list[str]) -> list[dict]:
    """The 44 prescribed calls with immutable identities (sequence, stage, id, arm)."""
    calls = []
    for iid, arm in items4c.TIMING_CALLS:
        calls.append({"stage": "timing", "id": iid, "arm": arm})
    for iid in setup_ids:
        if iid not in items4c.TIMING_IDS:
            calls.append({"stage": "off", "id": iid, "arm": "base"})
    off_ids = items4c.TIMING_IDS + [i for i in setup_ids if i not in items4c.TIMING_IDS]
    for iid in off_ids:
        calls.append({"stage": "plain", "id": iid, "arm": "base"})
    for iid, arm in items4c.TIMING_CALLS:
        calls.append({"stage": "replay", "id": iid, "arm": arm})
    for i, c in enumerate(calls):
        c["seq"] = i
        c["key"] = f"{i:02d}-{c['stage']}-{c['id']}-{c['arm']}"
    assert len(calls) == 44
    return calls


def call_path(call: dict) -> Path:
    return QDIR / "calls" / f"{call['key']}.json"


def load_call(call: dict) -> dict | None:
    p = call_path(call)
    return json.loads(p.read_text()) if p.exists() else None


def _sha(obj) -> str:
    data = obj.encode() if isinstance(obj, str) else json.dumps(obj).encode()
    return hashlib.sha256(data).hexdigest()


def package_call(model, tokenizer, mc, item, call, args, manifest, receipt) -> dict:
    dialogue = mc.load_dialogue(item["dialogue"])
    research_base = mc.build_long_prompt(
        dialogue, item["session"], item["queries"][0], screen._tokenizer(), ""
    )["prompt_tokens"]
    session, prompt, built, (head, sep, request) = runner.build_arm(
        model, tokenizer, mc, dialogue, item, call["arm"], research_base, args.max_new
    )
    messages = mc.focus_session_messages(dialogue, item["session"])
    receipt.begin_call()
    gen = runner.generate_package(
        session, request, head, sep, args.max_new, args.deadline
    )
    receipt.end_call(gen["seconds"])
    prompt_ids = session.encode(prompt)
    return {
        **call,
        "prompt": prompt,
        "prompt_sha256": _sha(prompt),
        "prompt_ids": prompt_ids,
        "prompt_ids_sha256": _sha(prompt_ids),
        "prompt_tokens": built["prompt_tokens"],
        "window": {
            k: v for k, v in built.items() if k not in ("prompt", "thread_text_kept")
        },
        "messages": messages,
        "head": head,
        "separator": sep,
        "request": request,
        "max_new": args.max_new,
        "deadline": args.deadline,
        "raw_ids": gen["generated_token_ids_raw"],
        "scored_ids": gen["generated_token_ids"],
        "text": gen["text"],
        "eos_token_ids": gen["eos_token_ids"],
        "ended_by_eos": gen["ended_by_eos"],
        "termination": gen["termination"],
        "timeout_reason": gen["timeout_reason"],
        "seconds": gen["seconds"],
        "manifest": manifest,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def plain_call(plain, plain_tokenizer, ref: dict, call: dict, args, receipt) -> dict:
    """Plain upstream model on the package-off prompt: explicit prompt-id comparison
    and raw output under the package's effective EOS list (finding 1)."""
    import torch

    ids_plain = plain_tokenizer(ref["prompt"], add_special_tokens=False)["input_ids"]
    ids = torch.tensor([ref["prompt_ids"]], device="cuda")
    receipt.begin_call()
    started = time.monotonic()
    with torch.no_grad():
        out = plain.generate(
            ids,
            attention_mask=torch.ones_like(ids),
            do_sample=False,
            num_beams=1,
            max_new_tokens=args.max_new,
            max_time=args.deadline,
            eos_token_id=ref["eos_token_ids"],
        )
    seconds = time.monotonic() - started
    receipt.end_call(seconds)
    raw = out[0, ids.shape[1] :].tolist()
    return {
        **call,
        "reference_key": ref["key"],
        "prompt_sha256": ref["prompt_sha256"],
        "prompt_ids_sha256": _sha(ref["prompt_ids"]),
        "plain_prompt_ids_sha256": _sha(ids_plain),
        "prompt_ids_match": ids_plain == ref["prompt_ids"],
        "raw_ids": raw,
        "raw_match": raw == ref["raw_ids"],
        "eos_token_ids": ref["eos_token_ids"],
        "seconds": seconds,
        "trunk": str(args.trunk),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def report(calls: list[dict], manifest: dict, identity: dict) -> dict:
    receipts = {c["key"]: load_call(c) for c in calls}
    missing = [k for k, v in receipts.items() if v is None]
    timing = [receipts[c["key"]] for c in calls if c["stage"] == "timing"]
    offs = {r["id"]: r for r in timing if r and r["arm"] == "base"}
    offs.update(
        {
            receipts[c["key"]]["id"]: receipts[c["key"]]
            for c in calls
            if c["stage"] == "off" and receipts[c["key"]]
        }
    )
    plain = [receipts[c["key"]] for c in calls if c["stage"] == "plain"]
    replay = [receipts[c["key"]] for c in calls if c["stage"] == "replay"]
    plain_rows = [
        {
            "id": r["id"],
            "prompt_ids_match": r["prompt_ids_match"],
            "raw_match": r["raw_match"],
        }
        for r in plain
        if r
    ]
    replay_rows = []
    for r in replay:
        if not r:
            continue
        orig = next(
            t for t in timing if t and t["id"] == r["id"] and t["arm"] == r["arm"]
        )
        replay_rows.append(
            {
                "id": r["id"],
                "arm": r["arm"],
                "prompt_bytes_match": r["prompt"] == orig["prompt"],
                "prompt_ids_match": r["prompt_ids"] == orig["prompt_ids"],
                "raw_match": r["raw_ids"] == orig["raw_ids"],
                "seconds": r["seconds"],
            }
        )
    n_plain = sum(r["prompt_ids_match"] and r["raw_match"] for r in plain_rows)
    n_replay = sum(
        r["prompt_bytes_match"] and r["prompt_ids_match"] and r["raw_match"]
        for r in replay_rows
    )
    complete = not missing
    t_max = max(t["seconds"] for t in timing if t) if any(timing) else None
    fingerprints_equal = all(
        runner.fingerprint_matches(r["manifest"], manifest)
        for r in timing
        + [receipts[c["key"]] for c in calls if c["stage"] in ("off", "replay")]
        if r
    )
    resident = runner.resident_seconds(QDIR)
    n_rule = items4c.sample_size(t_max) if t_max else None
    passed = (
        complete
        and n_plain == 16
        and n_replay == 8
        and fingerprints_equal
        and not resident["unbounded"]
        and resident["resident_seconds"] <= runner.QUALIFICATION_ALLOWANCE
    )
    return {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "identity": identity,
        "manifest": manifest,
        "complete": complete,
        "missing_calls": missing,
        "t_max_seconds": t_max,
        "timing_calls": [
            {
                k: t[k]
                for k in (
                    "seq",
                    "key",
                    "id",
                    "arm",
                    "seconds",
                    "termination",
                    "timeout_reason",
                    "prompt_tokens",
                    "prompt_sha256",
                    "prompt_ids_sha256",
                    "eos_token_ids",
                )
            }
            | {"raw_ids_sha256": _sha(t["raw_ids"]), "n_raw": len(t["raw_ids"])}
            for t in timing
            if t
        ],
        "off_outputs": {
            k: {
                "raw_ids_sha256": _sha(v["raw_ids"]),
                "n_raw": len(v["raw_ids"]),
                "seconds": v["seconds"],
                "termination": v["termination"],
            }
            for k, v in offs.items()
        },
        "plain_matches": plain_rows,
        "replay_matches": replay_rows,
        "n_plain_matches": n_plain,
        "n_replay_matches": n_replay,
        "fingerprints_equal": fingerprints_equal,
        "resident": resident,
        "resident_allowance_seconds": runner.QUALIFICATION_ALLOWANCE,
        "passed": passed,
        "n_by_timing_rule": n_rule,
        "eligible": bool(passed and n_rule is not None and n_rule >= items4c.N_MIN),
        "generations": len(calls),
        "receipts_dir": str(QDIR),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b")
    )
    parser.add_argument("--trunk", default=str(ROOT / "models/qwen3-4b-hf"))
    parser.add_argument("--out", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--max-new", type=int, default=screen.MAX_NEW)
    parser.add_argument("--deadline", type=float, default=screen.DEADLINE)
    parser.add_argument("--model", default="4b")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)
    if Path(args.out).exists():
        raise SystemExit(f"{args.out} exists; qualification runs once")

    from stencil import memorycode as mc

    hub = Path(args.hub)
    args.window, args.budget_tokens = mc.WINDOW, mc.BUDGET
    setup = [
        it
        for it in json.loads((OUT / "items.json").read_text())["items"]
        if it["split"] == "setup_long"
    ]
    by_id = {it["id"]: it for it in setup}
    calls = prescribed_calls([it["id"] for it in setup])
    QDIR.mkdir(parents=True, exist_ok=True)
    (QDIR / "calls").mkdir(exist_ok=True)
    provisional = runner.package_manifest(args, hub, OUT / "items-4c-candidates.json")
    identity_path = QDIR / "identity.json"
    identity = {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "package_sha256": provisional["package_sha256"],
        "checker_sha256": provisional["checker_sha256"],
        "calls": [
            {k: c[k] for k in ("seq", "key", "stage", "id", "arm")} for c in calls
        ],
        "max_new": args.max_new,
        "deadline": args.deadline,
    }
    if identity_path.exists():
        prior = json.loads(identity_path.read_text())
        if prior != identity:
            raise SystemExit("qualification identity changed; refusing to resume")
    else:
        screen._write_atomic(identity_path, identity)
    prior_resident = runner.resident_seconds(QDIR)
    remaining = runner.QUALIFICATION_ALLOWANCE - prior_resident["resident_seconds"]
    if args.report_only:
        manifest = next(
            (
                load_call(c)["manifest"]
                for c in calls
                if c["stage"] == "timing" and load_call(c)
            ),
            provisional,
        )
        rep = report(calls, manifest, identity)
        if rep["complete"]:
            screen._write_atomic(Path(args.out), rep)
        print(
            json.dumps(
                {
                    k: rep[k]
                    for k in (
                        "complete",
                        "missing_calls",
                        "t_max_seconds",
                        "n_plain_matches",
                        "n_replay_matches",
                        "passed",
                        "eligible",
                        "resident",
                    )
                },
                indent=1,
            )
        )
        return 0 if rep["eligible"] else 1
    if remaining <= runner.PERSIST_MARGIN or prior_resident["unbounded"]:
        raise SystemExit("qualification resident allowance exhausted; INELIGIBLE")
    receipt = runner.ProcessReceipt(
        QDIR,
        "qualification",
        resident_limit=min(remaining, 3000.0),
        call_limit=args.deadline + runner.CALL_GRACE,
    )
    manifest = None
    try:
        # stages 1-2 and 4 need the package; stage 3 the plain trunk
        def pending(stage):
            return [c for c in calls if c["stage"] == stage and load_call(c) is None]

        def can_start():
            return (
                receipt.elapsed()
                + args.deadline
                + runner.CALL_GRACE
                + runner.PERSIST_MARGIN
                <= receipt.resident_limit
            )

        for stage in ("timing", "off"):
            todo = pending(stage)
            if not todo:
                continue
            model, tokenizer = runner.load_package(hub)
            manifest = runner.package_manifest(
                args, hub, OUT / "items-4c-candidates.json", model
            )
            try:
                for c in todo:
                    if not can_start():
                        print("stopping: slice limit", flush=True)
                        return 2
                    rec = package_call(
                        model, tokenizer, mc, by_id[c["id"]], c, args, manifest, receipt
                    )
                    screen._write_atomic(call_path(c), rec)
                    print(
                        f"{c['key']}: {rec['seconds']:.1f}s {rec['termination']}",
                        flush=True,
                    )
            finally:
                runner.release_model(model, tokenizer)
                model = tokenizer = None
        todo = pending("plain")
        if todo:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            plain_tok = AutoTokenizer.from_pretrained(args.trunk)
            plain = AutoModelForCausalLM.from_pretrained(
                args.trunk, dtype=torch.bfloat16, device_map="cuda"
            )
            plain.eval()
            try:
                refs = {}
                for c in calls:
                    if c["stage"] in ("timing", "off") and c["arm"] == "base":
                        refs[c["id"]] = load_call(c)
                for c in todo:
                    if not can_start():
                        print("stopping: slice limit", flush=True)
                        return 2
                    rec = plain_call(plain, plain_tok, refs[c["id"]], c, args, receipt)
                    screen._write_atomic(call_path(c), rec)
                    print(
                        f"{c['key']}: ids={rec['prompt_ids_match']} "
                        f"raw={rec['raw_match']}",
                        flush=True,
                    )
            finally:
                runner.release_model(plain, plain_tok)
                plain = plain_tok = None
        todo = pending("replay")
        if todo:
            model, tokenizer = runner.load_package(hub)
            manifest = runner.package_manifest(
                args, hub, OUT / "items-4c-candidates.json", model
            )
            try:
                for c in todo:
                    if not can_start():
                        print("stopping: slice limit", flush=True)
                        return 2
                    rec = package_call(
                        model, tokenizer, mc, by_id[c["id"]], c, args, manifest, receipt
                    )
                    screen._write_atomic(call_path(c), rec)
                    print(
                        f"{c['key']}: {rec['seconds']:.1f}s {rec['termination']}",
                        flush=True,
                    )
            finally:
                runner.release_model(model, tokenizer)
                model = tokenizer = None
    finally:
        receipt.finish()
    manifest = load_call(calls[0])["manifest"]
    rep = report(calls, manifest, identity)
    screen._write_atomic(Path(args.out), rep)
    print(
        json.dumps(
            {
                k: rep[k]
                for k in (
                    "t_max_seconds",
                    "n_plain_matches",
                    "n_replay_matches",
                    "fingerprints_equal",
                    "passed",
                    "n_by_timing_rule",
                    "eligible",
                    "resident",
                )
            },
            indent=1,
        )
    )
    return 0 if rep["eligible"] else 1


if __name__ == "__main__":
    sys.exit(main())

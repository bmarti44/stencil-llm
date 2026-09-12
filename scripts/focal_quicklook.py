"""Bounded delivery-format pilot (NOT a registered result; Astra root-cause §12).

Arms per item, all with a frozen common retained history (base window
``--window``, default 1,792 tokens) and the same compact rule packets built from
the label-derived live rules (oracle; exposed SETUP-LONG pilot split):

* ``base``: plain greedy (identity-checked against the plain loop);
* ``before_compact``: the packets once, before the request, in the user turn;
* ``focal_header_compact``: comment cues at unit headers (body rules at the header);
* ``focal_phased_compact``: header rules at the header, body rules at the body;
* ``user_phased``: the same phased packets through a rebuilt user turn.

Records per arm: text, generated ids, inserted spans, events, token accounting,
parse/cap/loop status, scores on the item's checks with only the cue spans removed
(model echoes are counted, never removed).  Writes ``results/focal/quicklook.json``.
"""

from __future__ import annotations

import argparse
import ast
import functools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil import memorycode as mc  # noqa: E402
from stencil.focal import (  # noqa: E402
    count_echoes,
    rule_family,
    rule_phase,
    strip_spans,
)
from stencil.focal_runtime import (  # noqa: E402
    CUE_PREFIXES,
    FocalGenerator,
    HFBackend,
    cue_packet,
)

print = functools.partial(print, flush=True)  # noqa: A001


def score(text: str, checks: list, compute_score) -> dict:
    out: dict[str, list[float]] = {}
    for fam, regex in checks:
        kind = (
            "regex"
            if isinstance(regex, str)
            else ("bool" if isinstance(regex, bool) else "pair")
        )
        try:
            s = compute_score(text, fam, regex)
        except Exception:
            s = None
        out.setdefault(kind, []).append(0.0 if s is None else float(s))
    flat = [v for vs in out.values() for v in vs]
    return {
        "fraction": sum(flat) / max(1, len(flat)),
        **{k: sum(v) / len(v) for k, v in out.items()},
        "n_checks": len(flat),
    }


def parse_status(text: str) -> dict:
    code = mc.extract_code(text)
    try:
        ast.parse(code)
        ok = True
    except SyntaxError:
        ok = False
    lines = [ln.strip() for ln in code.split("\n") if ln.strip()]
    loop = 0
    for i in range(len(lines) - 5):
        if len({lines[i + j] for j in range(6)}) == 1:
            loop += 1
    return {"parses": ok, "fenced": "```" in text, "repeated_line_runs": loop}


def compact_reminder(rules) -> str:
    """Once-before rendering of the same packets (kind/phase groups) as prose."""
    groups: dict[tuple[str, str], list[str]] = {}
    for kind, phase, text in rules:
        groups.setdefault((kind, phase), []).append(text)
    labels = {
        ("function", "header"): "function",
        ("function", "body"): "function body",
        ("method", "header"): "method",
        ("method", "body"): "method body",
        ("init", "body"): "__init__ body",
        ("class", "header"): "class",
        ("import", "header"): "import",
        ("variable", "header"): "assignment",
        ("any", "header"): "code",
    }
    parts = [cue_packet(labels.get(k, k[0]), v) for k, v in groups.items()]
    return "Conventions still in force. " + " ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--items", type=int, default=3)
    ap.add_argument("--skip", type=int, default=1)
    ap.add_argument("--max-new", type=int, default=1536)
    ap.add_argument("--window", type=int, default=1792)
    ap.add_argument("--max-context", type=int, default=4096)
    ap.add_argument("--out", default=str(ROOT / "results/focal/quicklook.json"))
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(0)
    tokenizer = AutoTokenizer.from_pretrained(args.hub)
    model = AutoModelForCausalLM.from_pretrained(
        args.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    model.eval()
    eos_cfg = model.config.eos_token_id
    eos = tuple(eos_cfg if isinstance(eos_cfg, list) else [eos_cfg])
    topics = mc.load_topics()
    checker = mc.vendored_checker()
    compute_score = (
        checker.compute_score if hasattr(checker, "compute_score") else checker
    )

    all_items = json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
        "items"
    ]
    items = [i for i in all_items if i["split"] == "setup_long"][
        args.skip : args.skip + args.items
    ]
    records = []
    for item in items:
        did, s = (int(x) for x in item["id"].split("-"))
        dialogue = mc.load_dialogue(did)
        query = item["queries"][0]
        head, sep, request = mc.long_request(dialogue, query)
        checks = item["history_regex"]
        oracle = mc.oracle_sentences(dialogue, s, topics)
        rules = [(rule_family(t), rule_phase(t), t) for t in oracle]

        # frozen common history: the base prompt at the pilot window; the before
        # arm and user-channel rebuilds append text to the request in that prompt
        session = model.new_session(tokenizer, stencil_focus=False, window=args.window)
        for role, text, rendered in mc.focus_session_messages(dialogue, s):
            session.add_message(role, text, rendered=rendered)
        base_prompt = session.build_prompt(request, head=head, separator=sep)
        assert base_prompt.count(request) >= 1
        req_at = base_prompt.rfind(request)

        def with_request_suffix(
            suffix: str, base_prompt=base_prompt, req_at=req_at, request=request
        ):
            return (
                base_prompt[: req_at + len(request)]
                + suffix
                + base_prompt[req_at + len(request) :]
            )

        ids = session.encode(base_prompt)
        rec = {
            "id": item["id"],
            "n_rules": len(rules),
            "rules": rules,
            "prompt_tokens": len(ids),
            "window": args.window,
            "max_new": args.max_new,
            "arms": {},
        }

        def record(
            name, r, text_for_score, extra=None, rec=rec, checks=checks, item=item
        ):
            stripped = (
                strip_spans(r.text, r.inserted_spans) if r.inserted_spans else r.text
            )
            rec["arms"][name] = {
                "score": score(stripped, checks, compute_score),
                "parse": parse_status(stripped),
                "echoed_lines": count_echoes(stripped, CUE_PREFIXES),
                "n_generated": len(r.generated_ids),
                "steps": r.steps,
                "discarded_tokens": r.discarded_tokens,
                "inserted_tokens": r.inserted_tokens,
                "refed_tokens": r.refed_tokens,
                "prompt_tokens": r.prompt_tokens,
                "insertions": len(r.events),
                "events": r.events,
                "reminders": r.reminders,
                "seconds": r.seconds,
                "ended_by_eos": r.ended_by_eos,
                "truncated": r.truncated,
                "context_exceeded": r.context_exceeded,
                "text": r.text,
                "generated_ids": r.generated_ids,
                "inserted_spans": r.inserted_spans,
                **(extra or {}),
            }
            a = rec["arms"][name]
            sc = a["score"]
            print(
                f"[{item['id']}] {name:22s} fraction={sc['fraction']:.3f} "
                + " ".join(
                    f"{k}={sc[k]:.2f}" for k in ("regex", "pair", "bool") if k in sc
                )
                + f" gen={a['n_generated']} steps={a['steps']}"
                + f" ins={a['insertions']}/{a['inserted_tokens']}tok"
                + f" echo={a['echoed_lines']} eos={a['ended_by_eos']}"
                + f" parses={a['parse']['parses']}"
                + f" loops={a['parse']['repeated_line_runs']} s={a['seconds']:.0f}"
            )

        # base + identity check against model.generate
        t0 = time.time()
        with torch.no_grad():
            out = model.generate(
                torch.tensor([ids], device=model.device),
                attention_mask=torch.ones(
                    1, len(ids), device=model.device, dtype=torch.long
                ),
                max_new_tokens=args.max_new,
                do_sample=False,
                eos_token_id=list(eos),
            )
        pkg_ids = [t for t in out[0, len(ids) :].tolist() if t not in eos]
        t_pkg = time.time() - t0
        r0 = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=[],
            max_new_tokens=args.max_new,
            max_context=args.max_context,
            eos_ids=eos,
        ).generate(ids)
        record(
            "base",
            r0,
            r0.text,
            {"loop_identity": r0.generated_ids == pkg_ids, "pkg_seconds": t_pkg},
        )
        print(f"[{item['id']}] identity={r0.generated_ids == pkg_ids}")

        # before_compact: same packets once, in the user turn
        ids_b = session.encode(with_request_suffix("\n\n" + compact_reminder(rules)))
        rb = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=[],
            max_new_tokens=args.max_new,
            max_context=args.max_context,
            eos_ids=eos,
        ).generate(ids_b)
        record(
            "before_compact", rb, rb.text, {"reminder_tokens": len(ids_b) - len(ids)}
        )

        # focal comment channel, unphased and phased
        for name, kw in (
            ("focal_header_compact", dict(phased=False)),
            ("focal_phased_compact", dict(phased=True)),
        ):
            rf = FocalGenerator(
                HFBackend(model),
                tokenizer,
                rules=rules,
                max_new_tokens=args.max_new,
                max_context=args.max_context,
                eos_ids=eos,
                **kw,
            ).generate(ids)
            record(name, rf, rf.text)

        # user channel, phased
        def rebuild(packets, session=session, with_request_suffix=with_request_suffix):
            return session.encode(with_request_suffix("\n\n" + " ".join(packets)))

        ru = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=rules,
            max_new_tokens=args.max_new,
            max_context=args.max_context,
            eos_ids=eos,
            channel="user",
            rebuild_prompt=rebuild,
        ).generate(ids)
        record("user_phased", ru, ru.text)

        records.append(rec)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(records, indent=1))


if __name__ == "__main__":
    main()

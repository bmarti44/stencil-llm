"""Quick look (NOT a registered result): focal delivery on a few SETUP-LONG items.

Three generations per item through the shipping 4B package weights:

* ``base``: plain window prompt, greedy (identity-checked against the plain
  ``FocalGenerator`` loop with no rules, which must reproduce ``model.generate``);
* ``oracle_before``: the label-derived live rules rendered once before the request
  (same renderer as the long reminder), plain greedy;
* ``oracle_focal``: the same rules typed by :func:`stencil.focal.rule_family` and
  delivered at the governed units inside the generation.

Prints per-arm scores on the item's ``history_regex`` checks after stripping the
inserted spans.  Exposed SETUP items, oracle rules: a mechanism smoke test only.
Writes ``results/focal/quicklook.json``.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from stencil import memorycode as mc  # noqa: E402
from stencil.focal import rule_family, strip_spans  # noqa: E402
from stencil.focal_runtime import FocalGenerator, HFBackend  # noqa: E402

print = functools.partial(print, flush=True)  # noqa: A001


def score(text: str, checks: list, compute_score) -> dict:
    out = {}
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--items", type=int, default=2)
    ap.add_argument("--max-new", type=int, default=800)
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
    eos = tuple(
        model.config.eos_token_id
        if isinstance(model.config.eos_token_id, list)
        else [model.config.eos_token_id]
    )
    topics = mc.load_topics()
    checker = mc.vendored_checker()
    compute_score = (
        checker.compute_score if hasattr(checker, "compute_score") else checker
    )

    items = [
        i
        for i in json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
            "items"
        ]
        if i["split"] == "setup_long"
    ]
    items = items[: args.items]
    records = []
    for item in items:
        did, s = (int(x) for x in item["id"].split("-"))
        dialogue = mc.load_dialogue(did)
        query = item["queries"][0]
        head, sep, request = mc.long_request(dialogue, query)
        checks = item["history_regex"]
        oracle = mc.oracle_sentences(dialogue, s, topics)
        rules = [(rule_family(t), t) for t in oracle]

        def prompt_ids(request_text: str, dialogue=dialogue, s=s, head=head, sep=sep):
            session = model.new_session(tokenizer, stencil_focus=False)
            for role, text, rendered in mc.focus_session_messages(dialogue, s):
                session.add_message(role, text, rendered=rendered)
            prompt = session.build_prompt(request_text, head=head, separator=sep)
            return session.encode(prompt)

        rec = {"id": item["id"], "n_rules": len(rules), "rules": rules, "arms": {}}

        # base + identity check
        ids = prompt_ids(request)
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
        pkg_ids = out[0, len(ids) :].tolist()
        pkg_text = tokenizer.decode(pkg_ids, skip_special_tokens=True)
        t_pkg = time.time() - t0
        plain = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=[],
            max_new_tokens=args.max_new,
            eos_ids=eos,
        )
        r0 = plain.generate(ids)
        pkg_stripped = [t for t in pkg_ids if t not in eos]
        identity = r0.generated_ids == pkg_stripped
        rec["arms"]["base"] = {
            "score": score(pkg_text, checks, compute_score),
            "n_tokens": len(pkg_ids),
            "seconds": t_pkg,
            "loop_identity": identity,
            "loop_seconds": r0.seconds,
            "text": pkg_text,
        }
        print(
            f"[{item['id']}] base identity={identity} tokens={len(pkg_ids)} "
            f"pkg {t_pkg:.1f}s loop {r0.seconds:.1f}s"
        )

        # oracle before the request
        reminder = mc.render_long_reminder(oracle)
        ids_b = prompt_ids(reminder + "\n\n" + request)
        rb = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=[],
            max_new_tokens=args.max_new,
            eos_ids=eos,
        ).generate(ids_b)
        rec["arms"]["oracle_before"] = {
            "score": score(rb.text, checks, compute_score),
            "n_tokens": len(rb.generated_ids),
            "seconds": rb.seconds,
            "prompt_tokens": len(ids_b),
            "text": rb.text,
        }

        # oracle focal
        rf = FocalGenerator(
            HFBackend(model),
            tokenizer,
            rules=rules,
            max_new_tokens=args.max_new,
            eos_ids=eos,
        ).generate(ids)
        stripped = strip_spans(rf.text, rf.inserted_spans)
        rec["arms"]["oracle_focal"] = {
            "score": score(stripped, checks, compute_score),
            "score_unstripped": score(rf.text, checks, compute_score),
            "n_tokens": len(rf.generated_ids),
            "inserted_tokens": rf.inserted_tokens,
            "insertions": len(rf.events),
            "events": rf.events,
            "seconds": rf.seconds,
            "text": rf.text,
            "stripped": stripped,
        }
        for arm, a in rec["arms"].items():
            sc = a["score"]
            print(
                f"[{item['id']}] {arm:14s} fraction={sc['fraction']:.3f} "
                + " ".join(
                    f"{k}={sc[k]:.2f}" for k in ("regex", "pair", "bool") if k in sc
                )
                + f" tokens={a['n_tokens']} s={a['seconds']:.0f}"
                + (
                    f" ins={a['insertions']}/{a['inserted_tokens']}tok"
                    if "insertions" in a
                    else ""
                )
            )
        records.append(rec)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(records, indent=1))


if __name__ == "__main__":
    main()

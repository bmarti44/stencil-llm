"""Reproduce the 2026-09-05 development-only relation audit reconciliation."""

import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/classifier"
FIELDS = ("target_span", "new_rule_spans", "message_new_rule")


def key(row):
    return row["source"], row["old_rule"], row["message"]


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def decide(index, row, astra, opus):
    """Apply visible status/key/scope tests; review rationales supply evidence."""
    al = astra.get("new_label", row["label"])
    ol = opus.get("new_label", row["label"])
    chosen = al if al != row["label"] else ol
    reason = (astra if al != row["label"] else opus).get("why", "")
    if row["status"] in {"cancelled", "completed", "superseded"}:
        if "supersedes" in (al, ol) or chosen == "reinstates":
            return (
                "none",
                True,
                (
                    "Inactive target plus changed value/scope or modified restoration: "
                    "do not supersede or copy the original; admit the explicit new "
                    "persistent span. Ambiguous restoration readings fail safe."
                ),
            )
    if chosen == "cancels" and row["scope"] == "global" and index != 5349:
        # These reviewed withdrawals are narrower than the global obligation.
        if index not in {2806, 4097, 4596}:
            return (
                "none",
                False,
                (
                    "Scoped suspension does not withdraw the entire global target; "
                    "no replacement requirement, and v1 has no suspension operation."
                ),
            )
    if index == 1591:
        return (
            "none",
            False,
            "Leave this output unchanged is one-off, not a persistent replacement.",
        )
    if index == 3837:
        return (
            "none",
            False,
            "An annex named C does not unambiguously replace standing numbering.",
        )
    if index == 3961:
        return (
            "none",
            True,
            "Asset-class grouping permits within-group sorting; compatible addition.",
        )
    if index == 4008:
        return (
            "none",
            False,
            "The next requested table is single-reply; no persistent update.",
        )
    if index == 4737:
        return (
            "none",
            False,
            "Reported instruction and permission leave replacement ambiguous.",
        )
    return chosen, None, reason


def main():
    names = [
        "relations/kimi-relations.jsonl",
        "review/relations-astra-patch.jsonl",
        "review/relations-opus-patch.jsonl",
    ]
    paths = [DATA / name for name in names]
    rows, ar, op = map(read, paths)
    astra = {r["row_index"]: r for r in ar if "summary" not in r}
    indices = defaultdict(list)
    for i, row in enumerate(rows, 1):
        indices[key(row)].append(i)
    opus = defaultdict(list)
    mappings = []
    for pi, patch in enumerate(op[1:], 1):
        matches = [
            i for i in indices[key(patch)] if rows[i - 1]["label"] == patch["old_label"]
        ]
        assert matches, patch
        if patch["drop"] and "duplicate" in patch["why"]:
            # Unindexed duplicate-removal rows refer to later copies. Distinct
            # statuses/labels are preserved through exact row identity below.
            available = [i for i in matches if not any(p["drop"] for p in opus[i])]
            matches = [max(available)]
        for i in matches:
            opus[i].append(patch)
        mappings.append(
            {"opus_patch_row": pi, "source_rows": matches, "reason": patch["why"]}
        )
    patches, kept, disagreements, drops = [], [], [], []
    for i, original in enumerate(rows, 1):
        row = copy.deepcopy(original)
        ap = astra.get(i, {})
        ops = opus.get(i, [])
        oq = next((p for p in ops if not p["drop"]), ops[0] if ops else {})
        if ap:
            assert key(ap) == key(row) and ap["old_label"] == row["label"]
        for field in FIELDS:
            if "new_" + field in ap:
                assert row[field] == ap["old_" + field]
                row[field] = copy.deepcopy(ap["new_" + field])
        al, ol = ap.get("new_label", row["label"]), oq.get("new_label", row["label"])
        drop = ap.get("drop", False) or any(p["drop"] for p in ops)
        why = [p["why"] for p in [ap, *ops] if p]
        if drop:
            drops.append(i)
            decision = "drop"
        elif al == ol:
            row["label"] = al
            decision = "agreement"
        else:
            label, admission, reason = decide(i, row, ap, oq)
            row["label"] = label
            if admission is not None:
                row["message_new_rule"] = admission
                if admission:
                    row["new_rule_spans"] = [row["target_span"]["text"]]
            decision = "disagreement"
            why.append(reason)
            disagreements.append(
                {
                    "row_index": i,
                    "source": row["source"],
                    "astra": al,
                    "opus": ol,
                    "astra_explicit": bool(ap),
                    "opus_explicit": bool(oq),
                    "decision": label,
                    "message_new_rule": row["message_new_rule"],
                    "reason": reason,
                    "old_rule": row["old_rule"],
                    "message": row["message"],
                    "status": row["status"],
                    "scope": row["scope"],
                }
            )
        # Always preserve Astra's selected text; normalize offsets and admission
        # representation. Original inputs remain immutable.
        span = row["target_span"]
        quote = span["text"]
        start = span["start"]
        if row["message"][start : start + len(quote)] != quote:
            assert row["message"].count(quote) == 1
            start = row["message"].index(quote)
        row["target_span"] = {"start": start, "end": start + len(quote), "text": quote}
        row["new_rule_spans"] = [
            s if isinstance(s, str) else s.get("text", s.get("quote"))
            for s in row["new_rule_spans"]
        ]
        assert all(
            isinstance(s, str) and s in row["message"] for s in row["new_rule_spans"]
        )
        patch = {k: original[k] for k in ("source", "message", "old_rule")}
        patch.update(
            row_index=i,
            old_label=original["label"],
            new_label=row["label"],
            drop=drop,
            why="; ".join(dict.fromkeys(why)) or "Mechanical field normalization",
            reconciliation=decision,
        )
        for field in FIELDS:
            if field in ap or "new_" + field in ap or original[field] != row[field]:
                patch["old_" + field] = original[field]
                patch["new_" + field] = row[field]
        if ap or ops or any("new_" + f in patch for f in FIELDS):
            patches.append(patch)
        if not drop:
            kept.append(row)
    enrichment_repairs = []
    for name in ("astra", "opus"):
        path = DATA / f"relations/{name}-enrich.jsonl"
        paths.append(path)
        for i, row in enumerate(read(path), 1):
            if row["label"] == "supersedes" and row["status"] != "live":
                patch = {k: row[k] for k in ("source", "message", "old_rule")}
                patch.update(
                    old_label="supersedes",
                    new_label="none",
                    drop=False,
                    old_message_new_rule=row["message_new_rule"],
                    new_message_new_rule=True,
                    old_new_rule_spans=row["new_rule_spans"],
                    new_new_rule_spans=[row["target_span"]["text"]],
                    why="Inactive target, changed value: none + new persistent span",
                    reconciliation="enrichment_status_consistency",
                )
                patches.append(patch)
                enrichment_repairs.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "row_index": i,
                        "source": row["source"],
                    }
                )
    summary = {
        "date": "2026-09-05",
        "reviewer": "astra-reconciliation",
        "data_lineage": (
            "fit-on=kimi+enrich after merged patch; calibrated-on=dev split; "
            "evaluated-on=fable held-out, author-disjoint; held-out unopened"
        ),
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        },
        "source_rows": len(rows),
        "kept_rows": len(kept),
        "drops": len(drops),
        "drop_row_indices": drops,
        "label_counts": dict(Counter(r["label"] for r in kept)),
        "relabels": dict(
            Counter(
                rows[i - 1]["label"] + "->" + r["new_label"]
                for r in patches
                if not r["drop"]
                and (i := r.get("row_index"))
                and rows[i - 1]["label"] != r["new_label"]
            )
        ),
        "patch_rows": len(patches),
        "disagreements": disagreements,
        "disagreement_definition": (
            "Audited labels differ, including unchanged original where a reviewer "
            "supplied no patch; drops take precedence."
        ),
        "enrichment_status_repairs": enrichment_repairs,
        "opus_identity_resolution": mappings,
        "patch_application": (
            "Use one-based original kimi row_index AND exact "
            "source/old_rule/message/old_label; assert old_FIELD before "
            "installing new_FIELD. Enrichment patches use unique exact identities. "
            "Drop union. Normalize new_rule_spans to strings."
        ),
    }
    out = DATA / "review/relations-merged-patch.jsonl"
    out.write_text(
        "".join(
            json.dumps(r, ensure_ascii=False) + "\n"
            for r in [{"summary": summary}, *patches]
        )
    )
    table = [
        "# Relation audit disagreements — 2026-09-05",
        "",
        "Data lineage: development corpus only; held-out unopened. "
        "Row numbers are one-based original kimi rows.",
        "An omitted patch retains the original label; "
        "drop-union decisions are in the merged summary.",
        "",
        "| Row | Astra | Opus | Decision | New rule | Reason |",
        "|---:|---|---|---|---|---|",
    ]
    for d in disagreements:
        table.append(
            f"| {d['row_index']} | {d['astra']} | {d['opus']} | {d['decision']} "
            f"| {d['message_new_rule']} | {d['reason'].replace('|', '/')} |"
        )
    (DATA / "review/relations-disagreements.md").write_text("\n".join(table) + "\n")
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "source_rows",
                    "kept_rows",
                    "drops",
                    "label_counts",
                    "patch_rows",
                )
            }
        )
    )
    print("disagreements", len(disagreements))


if __name__ == "__main__":
    main()

"""Independent saved-record accounting; no inference, fitting or bank reads."""

from __future__ import annotations

import json
from collections import Counter

import numpy as np

from scripts import focus3_gate_v8 as v8
from scripts import train_relations as train
from stencil import focus3 as f


def main():
    out = v8.OUT
    paths = sorted((out / "records").glob("*.json"))
    assert len(paths) == 96
    actions = added = changes = pairs = spans = 0
    unauthorized, cross_key, reinstatement_checks, completions = [], [], [], []
    keys = {}
    previous = {}
    for path in paths:
        rec = json.loads(path.read_text())
        ep, ti = rec["episode"], rec["turn_index"]
        trace = rec["trace"]
        keymap = keys.setdefault(ep, {})
        before = {r["id"]: r for r in trace["before"]}
        after = {r["id"]: r for r in trace["after"]}
        assert len(before) == len(trace["before"])
        assert len(after) == len(trace["after"])
        assert before.keys() <= after.keys()
        if ti:
            assert before == previous[ep]
        previous[ep] = after
        new_ids = after.keys() - before.keys()
        changed_ids = {rid for rid in before if before[rid] != after[rid]}
        accounted_new, accounted_changed = set(), set()
        gold = Counter(
            (a["label"], a.get("target"), a.get("span")) for a in rec["turn"]["events"]
        )
        for action in trace["applied"]:
            actions += 1
            label, target, span = action["label"], action.get("target"), action["span"]
            identity = (label, target, span)
            if gold[identity]:
                gold[identity] -= 1
            else:
                admission = next(a for a in trace["admissions"] if a["span"] == span)
                unauthorized.append(
                    dict(
                        episode=ep,
                        turn_index=ti,
                        **action,
                        prule=admission["probabilities"][1],
                    )
                )
            if label in ("admit", "supersedes", "reinstates"):
                admission = next(a for a in trace["admissions"] if a["span"] == span)
                rid = f"{ti}:{admission['start']}"
                assert rid in new_ids and rid not in accounted_new
                accounted_new.add(rid)
                row = after[rid]
                assert row["status"] == "live"
                assert row["text"] == (
                    before[target]["text"] if label == "reinstates" else span
                )
                if label == "admit":
                    assert admission["accepted"]
                    assert admission["probabilities"][1] >= 0.95
                    keymap[rid] = f.relation_key(f.prose_message(span))
                else:
                    keymap[rid] = keymap.get(
                        target, f.relation_key(before[target]["text"])
                    )
            if target in changed_ids:
                old, new = before[target], after[target]
                assert dict(old, status=new["status"]) == new
                assert old["status"] == "live"
                assert (
                    new["status"]
                    == {
                        "supersedes": "superseded",
                        "cancels": "cancelled",
                        "completes": "completed",
                    }[label]
                )
                accounted_changed.add(target)
            if label == "completes":
                old = before[target]
                assert old["scope"] != "*"
                # Explicit task names are present in this setup's completions.
                assert f.scope_of(span, None) == old["scope"]
                completions.append(
                    dict(episode=ep, turn_index=ti, **action, target_scope=old["scope"])
                )
            if label == "reinstates":
                old = before[target]
                assert old["status"] in ("cancelled", "completed")
                assert not admission["overflow"]
                assert admission["probabilities"][1] >= 0.95
                assert f.relation_key(f.prose_message(span)) == keymap[target]
                assert not f.cancellation_message(rec["turn"]["text"], trace["pairs"])
        assert accounted_new == new_ids
        assert accounted_changed == changed_ids
        added += len(new_ids)
        changes += len(changed_ids)
        for pred in trace["pairs"] + trace["admissions"]:
            if not pred["overflow"]:
                z = np.asarray(pred["logits"], dtype=np.float64)
                assert np.isfinite(z).all()
                p = np.exp(z - z.max())
                p /= p.sum()
                np.testing.assert_allclose(
                    p, pred["probabilities"], rtol=1e-12, atol=1e-12
                )
        for pair in trace["pairs"]:
            row = train.normalize_row(
                dict(pair["input"], label="none", source="astra-v8-saved-record-audit")
            )
            assert list(train.render_pair(row)) == pair["model_input"]
            if pair.get("cross_key"):
                assert pair["applied"] == "none"
                cross_key.append(
                    dict(
                        episode=ep,
                        turn_index=ti,
                        target=pair["input"]["target_id"],
                        span=pair["input"]["target_span"]["text"],
                        label=pair["proposed"],
                    )
                )
            if pair["proposed"] == "reinstates":
                target = pair["input"]["target_id"]
                old = before[target]
                admission = next(
                    a
                    for a in trace["admissions"]
                    if a["start"] == pair["input"]["target_span"]["start"]
                )
                span = admission["span"]
                own_key = f.relation_key(f.prose_message(span))
                target_key = keymap.get(target, f.relation_key(old["text"]))
                reinstatement_checks.append(
                    dict(
                        episode=ep,
                        turn_index=ti,
                        span=span,
                        target=target,
                        own_key=own_key,
                        target_key=target_key,
                        status=old["status"],
                        prule=admission["probabilities"][1],
                        applied=pair["applied"],
                    )
                )
                if own_key != target_key:
                    assert pair["applied"] != "reinstates"
        pairs += len(trace["pairs"])
        spans += len(trace["admissions"])
    summary = json.loads((out / "summary.json").read_text())
    assert len(unauthorized) == summary["unauthorized"]["applications"]
    assert len(cross_key) == summary["cross_key_proposals"]
    result = dict(
        audit="PASS",
        records=len(paths),
        actions=actions,
        added_rows=added,
        status_changes=changes,
        unexplained_mutations=0,
        pairs=pairs,
        admission_spans=spans,
        raw_softmax=True,
        trainer_input_parity=True,
        unauthorized=unauthorized,
        cross_key_proposals=cross_key,
        reinstatement_proposals=reinstatement_checks,
        completions=completions,
        inputs={str(p.relative_to(v8.g.ROOT)): v8.g.digest(p) for p in paths},
    )
    v8.g.write(out / "independent-audit.json", result)
    print(
        json.dumps({k: v for k, v in result.items() if not isinstance(v, (list, dict))})
    )


if __name__ == "__main__":
    main()

"""Frozen classifier-driven rule register; renderer only, no attention masking.

Gold events are accepted only by Oracle. Runtime receives ordinary role/text.
Inference branches are loaded lazily; importing this module performs no work.
"""

from __future__ import annotations

import copy
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from stencil import focus2

LABELS = ("none", "supersedes", "cancels", "completes", "reinstates")
THRESHOLDS = dict(supersedes=0.94, cancels=0.50, completes=0.50, reinstates=0.50)
ROOT = Path(__file__).resolve().parents[2]
NONE_PAIR_THRESHOLD = 0.50  # v5 fixed positive-side bound; no gold-none quantile.
ORDER_DEFAULT = "Ordering: return the list in the given order."


def ordering_row(row):
    """Supported sort-schema field recognition, never a relation/admission veto."""
    return bool(
        re.search(r"\b(?:ascending|descending|ordering)\b|sorting rule", row.text, re.I)
    )


def semantic_key(row, gold_keys):
    if row.id.startswith("default:ordering:"):
        return "order:" + row.scope
    return gold_keys.get(row.id, "unmapped:" + row.id)


def decision(p, overflow=False, thresholds=None):
    if overflow or len(p) != 5 or not all(math.isfinite(v) for v in p):
        return "none"
    k = max(range(5), key=lambda i: p[i])
    label = LABELS[k]
    cutoffs = THRESHOLDS if thresholds is None else thresholds
    return label if k and p[k] >= cutoffs[label] else "none"


def sentences(text):
    """Verbatim sentence spans, retaining punctuation and source offsets."""
    return [
        (m.start(), m.group()) for m in re.finditer(r"\S.*?(?:[.!?](?=\s|$)|$)", text)
    ]


def prose_message(text):
    """Relation message: prose before the harness's sort request/payload block."""
    return re.split(r"\bSort request for task [A-Z]", text, maxsplit=1)[0].rstrip()


def relation_key(text):
    """Semantic metadata only; register provenance/identity stays separate."""
    if re.search(r"\btag\b", text, re.I):
        return "tag"
    if re.search(r"sort|order|payload", text, re.I):
        return "sort-order"
    return "instruction"


def admission_inputs(spans, previous):
    """Training segment A: up to three preceding, speaker-prefixed sentences.

    Include earlier spans in this user message; the previous user message is
    the historical context available to this user-only register API.
    """
    preceding = [s for _, s in sentences(previous)]
    inputs = []
    for span in spans:
        context = " ".join("user: " + s for s in preceding[-3:])
        inputs.append((context or "(no context)", f"[user] {span}"))
        preceding.append(span)
    return inputs


def scope_of(text, current):
    if re.search(
        r"\b(?:this reply only|this time only|this one answer|for this message)\b",
        text,
        re.I,
    ):
        return None
    if re.search(r"\b(?:conversation|all tasks|every sorting request)\b", text, re.I):
        return "*"
    m = re.search(r"\b[Tt]ask ([A-Z][A-Za-z0-9_-]*)\b", text)
    return m[1] if m else current


def kind_of(text):
    return "sort" if re.search(r"sort|payload|\btag\b|\bJSON\b", text, re.I) else "all"


def request_kind(text):
    return "sort" if re.search(r"\bSort request for task [A-Z]", text) else "prose"


def selected_task(text, current):
    # Anchored direct user request; quoted/incidental task names never switch.
    for _, span in sentences(text):
        m = re.match(
            r"(?:Work on|Return to|Continue|Switch to) task "
            r"([A-Z][A-Za-z0-9_-]*)\b",
            span,
        )
        if m:
            current = m[1]
    return current


def task_switch_only(span):
    # Admission spans retain the harness request after a semicolon; task
    # switching uses the same prose prefix as relation pairing.
    return bool(
        re.fullmatch(
            r"(?:Work on|Return to|Continue|Switch to) task [A-Z][A-Za-z0-9_-]*[.;!?]?",
            prose_message(span),
        )
    )


def can_reinstate(span, admission, old):
    return (
        old.status != "live"
        and not task_switch_only(span)
        and (
            (not admission["overflow"] and admission["probabilities"][1] >= 0.95)
            or bool(old.text and old.text in span)
        )
    )


@dataclass
class Rule:
    id: str
    text: str
    key: str
    scope: str
    kind: str
    version: int
    status: str
    provenance_turn: int
    span_start: int


def overlaps(a, b):
    return a == b or "*" in (a, b)


class Register:
    def __init__(self):
        self.rows = []

    def snapshot(self):
        return [asdict(r) for r in self.rows]

    def get(self, rid):
        return next(r for r in self.rows if r.id == rid)

    def add(self, text, key, scope, kind, turn, start):
        rid = f"{turn}:{start}"
        if any(r.id == rid for r in self.rows):
            return self.get(rid)
        version = 1 + max((r.version for r in self.rows if r.key == key), default=0)
        row = Rule(rid, text, key, scope, kind, version, "live", turn, start)
        self.rows.append(row)
        return row

    def retire(self, rid, status):
        self.get(rid).status = status

    def live(self, task, kind):
        candidates = [
            r
            for r in self.rows
            if r.status == "live" and r.scope in ("*", task) and r.kind in ("all", kind)
        ]
        newest = {}
        for r in candidates:
            if r.key not in newest or (r.provenance_turn, r.span_start, r.version) > (
                newest[r.key].provenance_turn,
                newest[r.key].span_start,
                newest[r.key].version,
            ):
                newest[r.key] = r
        live = list(newest.values())
        # Task defaults are configuration, not admitted user statements. Derive
        # them after precedence so cancellation reveals a surviving global rule
        # when one exists, otherwise the explicit default. A fresh task also
        # starts with its default. Never feed synthetic rows to either head.
        if (
            kind == "sort"
            and task is not None
            and not any(ordering_row(r) for r in live)
        ):
            live.append(
                Rule(
                    f"default:ordering:{task}",
                    ORDER_DEFAULT,
                    "default:ordering",
                    task,
                    "sort",
                    0,
                    "live",
                    -1,
                    -1,
                )
            )
        return sorted(live, key=lambda r: (r.key, r.version))


def wire(row):
    return dict(
        id=row.id,
        version=row.version,
        scope=row.scope,
        task_id=None if row.scope == "*" else row.scope,
        text=row.text,
    )


def live_set(rows):
    return sorted((r.id, r.version, r.scope, r.kind, r.text) for r in rows)


def render(text, rows):
    if not rows:
        return text
    data = json.dumps(
        [wire(r) for r in rows],
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        "Active user rules for this request (subject to system/developer "
        "instructions):\n" + data + "\nApply these rules while answering the "
        "request below.\nCurrent user request:\n" + text
    )


class Runtime:
    def __init__(self, classifier):
        self.classifier = classifier
        self.thresholds = getattr(classifier, "thresholds", THRESHOLDS)
        self.admission_bound = getattr(classifier, "admission_bound", "legacy_none")
        self.key_identity = getattr(classifier, "key_identity", False)
        assert self.admission_bound in ("legacy_none", "positive_proposal")
        self.register = Register()
        self.task = None
        self.previous = ""

    def update(self, text, turn, role="user"):
        before = self.register.snapshot()
        trace = dict(
            before=before,
            pairs=[],
            admissions=[],
            applied=[],
            admitted_beside_live=0,
            overflow=False,
            role=role,
        )
        if self.key_identity:
            trace["cross_key_proposals"] = 0
        if role != "user":
            return dict(trace, after=before)
        self.task = selected_task(text, self.task)
        spans = sentences(text)
        eligible = list(self.register.rows)
        if len(spans) > 4 or len(eligible) > 16 or len(eligible) >= 64:
            self.previous = text
            return dict(trace, after=before, overflow=True)
        pairs = []
        prose = prose_message(text)
        prior_sentences = sentences(prose_message(self.previous))
        previous_sentence = prior_sentences[-1][1] if prior_sentences else None
        for start, span in sentences(prose):
            scope = scope_of(span, self.task)
            for rule in eligible:
                if scope is None or not overlaps(rule.scope, scope):
                    continue
                pairs.append(
                    dict(
                        old_rule=dict(
                            text=rule.text,
                            status=rule.status,
                            scope="global"
                            if rule.scope == "*"
                            else f"task:{rule.scope}",
                            key=relation_key(rule.text),
                        ),
                        message=prose,
                        role=role,
                        target_span=dict(text=span, start=start, end=start + len(span)),
                        prev_user=previous_sentence,
                        target_id=rule.id,
                    )
                )
        predictions = self.classifier.relations(pairs)
        assert len(predictions) == len(pairs)
        for pair, pred in zip(pairs, predictions, strict=True):
            trace["pairs"].append(
                dict(
                    input=pair,
                    **pred,
                    proposed=decision(
                        pred["probabilities"], pred["overflow"], self.thresholds
                    ),
                    applied="none",
                )
            )
        trace["overflow"] = any(p["overflow"] for p in predictions)
        admissions = self.classifier.admission([s for _, s in spans], self.previous)
        assert len(admissions) == len(spans)
        trace["overflow"] |= any(a["overflow"] for a in admissions)
        # Retain scores even when a relation branch consumes/skips the span.
        trace["admissions"] = [
            dict(span=span, start=start, **admission, accepted=False)
            for (start, span), admission in zip(spans, admissions, strict=True)
        ]
        for (start, span), admission in zip(spans, admissions, strict=True):
            scope = scope_of(span, self.task)
            rows = [
                p
                for p in trace["pairs"]
                if p["input"]["target_span"]["start"] == start
                and scope is not None
                and overlaps(self.register.get(p["input"]["target_id"]).scope, scope)
            ]
            if self.key_identity:
                # Explicit semantic fields constrain a relation; anaphoric or
                # whole-task prose inherits the relation's nominated target key.
                span_key = relation_key(prose_message(span))
                for p in rows:
                    target = self.register.get(p["input"]["target_id"])
                    target_key = target.key
                    proposal_key = target_key if span_key == "instruction" else span_key
                    p["proposal_key"] = proposal_key
                    p["cross_key"] = (
                        p["proposed"] != "none" and proposal_key != target_key
                    )
                    trace["cross_key_proposals"] += int(p["cross_key"])
                # Preserve raw proposals for diagnostics, drop from both
                # precedence and the positive-proposal admission bound.
                rows = [p for p in rows if not p["cross_key"]]
            positive = [
                p
                for p in rows
                if p["proposed"] != "none"
                and self.register.get(p["input"]["target_id"]).kind
                in ("all", kind_of(span))
            ]
            # Task-completion prose has no request-kind word. It can address
            # all obligations; retain the pre-existing atomic completion check.
            if kind_of(span) == "all":
                positive = [p for p in rows if p["proposed"] != "none"]
            positive = [
                p
                for p in positive
                if p["proposed"] != "reinstates"
                or can_reinstate(
                    span, admission, self.register.get(p["input"]["target_id"])
                )
            ]
            blocked = any(p["overflow"] for p in rows)
            # Multiple completes form one whole-task transaction only when all
            # active obligations of that explicitly named task agree.
            if len(positive) > 1:
                targets = [self.register.get(p["input"]["target_id"]) for p in positive]
                valid_complete = (
                    all(p["proposed"] == "completes" for p in positive)
                    and scope is not None
                    and scope != "*"
                    and all(r.scope == scope for r in targets)
                    and {r.id for r in targets}
                    == {
                        r.id
                        for r in eligible
                        if r.scope == scope and r.status == "live"
                    }
                )
                if valid_complete and not blocked:
                    for p in positive:
                        rid = p["input"]["target_id"]
                        self.register.retire(rid, "completed")
                        p["applied"] = "completes"
                        trace["applied"].append(
                            dict(label="completes", target=rid, span=span)
                        )
                    continue
            if positive and not blocked:
                p = max(
                    positive,
                    key=lambda p: p["probabilities"][LABELS.index(p["proposed"])],
                )
                old = self.register.get(p["input"]["target_id"])
                label = p["proposed"]
                if label == "completes" and (
                    old.scope == "*"
                    or any(
                        r.scope == old.scope and r.status == "live" and r.id != old.id
                        for r in eligible
                    )
                ):
                    continue
                if label == "reinstates":
                    if old.status == "live":
                        continue
                    self.register.add(
                        old.text, old.key, old.scope, old.kind, turn, start
                    )
                elif old.status != "live":
                    continue
                elif label == "supersedes":
                    # Verbatim replacement; partial-scope overrides shadow only
                    # their intersection. Preserve global outside that scope.
                    self.register.add(span, old.key, scope, old.kind, turn, start)
                    if scope == old.scope or scope == "*":
                        old.status = "superseded"
                else:
                    self.register.retire(
                        old.id, "cancelled" if label == "cancels" else "completed"
                    )
                p["applied"] = label
                trace["applied"].append(dict(label=label, target=old.id, span=span))
                continue
            confident_none = (
                all(p["proposed"] == "none" for p in rows)
                if self.admission_bound == "positive_proposal"
                else all(p["probabilities"][0] >= NONE_PAIR_THRESHOLD for p in rows)
            )
            accept = (
                not positive
                and not blocked
                and confident_none
                and not admission["overflow"]
                and admission["probabilities"][1] >= 0.95
                and scope is not None
                and not task_switch_only(span)
            )
            next(a for a in trace["admissions"] if a["start"] == start)["accepted"] = (
                accept
            )
            if accept and not any(
                r.text == span and r.scope == scope and r.status == "live"
                for r in self.register.rows
            ):
                beside = any(
                    r.status == "live" and overlaps(r.scope, scope)
                    for r in self.register.rows
                )
                trace["admitted_beside_live"] += int(beside)
                self.register.add(
                    span,
                    relation_key(prose_message(span))
                    if self.key_identity
                    else f"new:{turn}:{start}",
                    scope,
                    kind_of(span),
                    turn,
                    start,
                )
                trace["applied"].append(dict(label="admit", span=span))
        self.previous = text
        return dict(trace, after=self.register.snapshot())


class Oracle:
    def __init__(self):
        self.register = Register()
        self.task = None

    def update(self, text, turn, events):
        before = self.register.snapshot()
        self.task = selected_task(text, self.task)
        for event in events:
            label = event["label"]
            if label in ("cancels", "completes"):
                self.register.retire(
                    event["target"], "cancelled" if label == "cancels" else "completed"
                )
                continue
            span = event["span"]
            start = text.index(span)
            if label == "admit":
                self.register.add(
                    span, event["key"], event["scope"], event["kind"], turn, start
                )
            else:
                old = self.register.get(event["target"])
                scope = event.get("scope", old.scope)
                self.register.add(
                    old.text if label == "reinstates" else span,
                    old.key,
                    scope,
                    old.kind,
                    turn,
                    start,
                )
                if label == "supersedes" and (old.scope == scope or scope == "*"):
                    old.status = "superseded"
        return dict(
            before=before, after=self.register.snapshot(), applied=copy.deepcopy(events)
        )


class FrozenClassifier:
    """Exact CPU architecture/input encoding used by the two frozen heads."""

    def __init__(
        self,
        relations_path=None,
        thresholds=None,
        admission_bound="legacy_none",
        admission_path=None,
        key_identity=False,
    ):
        import torch
        from safetensors.torch import load_file
        from transformers import AutoModel, AutoTokenizer

        torch.set_num_threads(4)
        self.torch = torch
        self.thresholds = THRESHOLDS if thresholds is None else thresholds
        self.admission_bound = admission_bound
        self.key_identity = key_identity
        relations_path = relations_path or ROOT / "data/classifier/model/relations"
        self.branches = {}
        for branch, classes in [("relations", 5), ("ft", 3)]:
            path = (
                relations_path
                if branch == "relations"
                else admission_path or ROOT / "data/classifier/model" / branch
            )
            tok = AutoTokenizer.from_pretrained(path / "encoder", local_files_only=True)
            enc = AutoModel.from_pretrained(
                path / "encoder", local_files_only=True
            ).eval()
            enc.requires_grad_(False)
            head = torch.nn.Sequential(
                torch.nn.Dropout(0.1),
                torch.nn.Linear(enc.config.hidden_size + 4, classes),
            ).eval()
            state = (
                load_file(str(path / "head.safetensors"))
                if branch == "relations"
                else torch.load(path / "head.pt", map_location="cpu", weights_only=True)
            )
            if branch == "ft":
                assert state["labels"] == ["none", "rule", "fact"]
                assert state["roles"] == ["user", "assistant", "tool", "system"]
                assert state["hidden"] == enc.config.hidden_size
                state = state["head"]
            head.load_state_dict(state)
            head.requires_grad_(False)
            self.branches[branch] = (tok, enc, head, classes)
        frozen = json.loads((relations_path / "thresholds.json").read_text())
        assert self.thresholds in [
            frozen["thresholds"],
            frozen.get("secondary_thresholds"),
        ]

    def infer(self, branch, inputs, limit):
        tok, enc, head, classes = self.branches[branch]
        outputs = []
        for start in range(0, len(inputs), 32):
            chunk = inputs[start : start + 32]
            encoded = [tok(a, b, truncation=False) for a, b in chunk]
            valid = [i for i, v in enumerate(encoded) if len(v["input_ids"]) <= limit]
            results = [
                dict(
                    probabilities=[1.0] + [0.0] * (classes - 1),
                    overflow=True,
                    model_input=[a, b],
                )
                for a, b in chunk
            ]
            if valid:
                batch = tok.pad([encoded[i] for i in valid], return_tensors="pt")
                with self.torch.inference_mode():
                    hidden = enc(**batch).last_hidden_state[:, 0]
                    roles = self.torch.tensor([[1.0, 0.0, 0.0, 0.0]] * len(valid))
                    logits = head(self.torch.cat([hidden, roles], dim=1))
                    probabilities = logits.double().softmax(-1).tolist()
                for i, p, logits_row in zip(
                    valid, probabilities, logits.tolist(), strict=True
                ):
                    results[i] = dict(
                        probabilities=p,
                        logits=logits_row,
                        overflow=False,
                        model_input=chunk[i],
                        token_count=len(encoded[i]["input_ids"]),
                    )
            outputs.extend(results)
        return outputs

    def relations(self, pairs):
        return self.infer("relations", [pair_input(p) for p in pairs], 512)

    def admission(self, spans, previous):
        return self.infer("ft", admission_inputs(spans, previous), 192)


def agreement(candidate, gold, gold_keys):
    c, o = set(live_set(candidate)), set(live_set(gold))
    keys = [semantic_key(r, gold_keys) for r in candidate]
    return dict(
        exact=c == o,
        false_retirement=not o <= c,
        contradictory=any(n > 1 for n in Counter(keys).values()),
    )


def score(turn, text, ids, eos):
    broken = (
        not text.strip()
        or eos not in (focus2.EOS, focus2.END)
        or focus2.repetitive(ids)
    )
    if turn["kind"] != "sort":
        return dict(success=not broken, stale=False, broken=broken)
    try:
        value = focus2.parse_json(text)
    except (ValueError, TypeError, RecursionError):
        value = None
    valid = (
        isinstance(value, dict)
        and set(value) == {"answer", "tag"}
        and type(value["tag"]) is int
        and isinstance(value["answer"], list)
        and all(type(x) is int for x in value["answer"])
    )
    expected = focus2.target("sort", turn["payload"], turn["direction"])
    task = bool(valid and focus2.json_equal(value["answer"], expected))
    tag = bool(valid and value["tag"] == turn["tag"])
    stale = bool(
        valid
        and turn["post_change"]
        and any(
            focus2.json_equal(
                value["answer"], focus2.target("sort", turn["payload"], d)
            )
            for d in turn["stale"]
        )
    )
    return dict(
        success=task and tag and not broken,
        stale=stale,
        broken=broken or not valid,
        task=task,
        constraint=tag,
    )


def episode_metrics(records):
    tasks = [r for r in records if r["turn"]["kind"] == "sort"]
    return dict(
        stale=any(r["score"]["stale"] for r in tasks),
        final_success=tasks[-1]["score"]["success"],
        broken=any(r["score"]["broken"] for r in records if r["turn"]["post_change"]),
        false_retirement=any(r["agreement"]["false_retirement"] for r in tasks),
        exact=all(r["agreement"]["exact"] for r in tasks),
        contradictory=any(r["agreement"]["contradictory"] for r in tasks),
    )


def summarize(episodes, records, n):
    metrics = {}
    for ep in episodes:
        metrics[ep["id"]] = {
            arm: episode_metrics(
                [r for r in records if r["episode"] == ep["id"] and r["arm"] == arm]
            )
            for arm in ("C", "O", "N", "T")
        }
    groups = {"pooled": episodes}
    groups.update(
        {
            family: [e for e in episodes if e["family"] == family]
            for family in sorted({e["family"] for e in episodes})
        }
    )
    counts = {
        family: {
            arm: {
                key: sum(metrics[e["id"]][arm][key] for e in es)
                for key in next(iter(metrics.values()))[arm]
            }
            for arm in ("C", "O", "N", "T")
        }
        for family, es in groups.items()
    }
    c, o, t = (counts["pooled"][a] for a in ("C", "O", "T"))
    terms = dict(
        stale_distance=abs(c["stale"] - o["stale"]) <= n // 16,
        success_distance=abs(c["final_success"] - o["final_success"]) <= n // 16,
        false_retirements=c["false_retirement"] <= n // 32,
        breakage=c["broken"] <= n // 32,
        beats_naive=c["stale"] < t["stale"],
        agreement=c["exact"] >= 3 * n // 4,
        per_family=all(
            counts[k]["C"]["exact"] >= 3 * n // 16 for k in groups if k != "pooled"
        ),
        no_contradiction=c["contradictory"] == 0,
    )
    paired = {}
    for reference in ("O", "N", "T"):
        paired[reference] = {}
        for endpoint in ("stale", "final_success", "broken"):
            paired[reference][endpoint] = dict(
                c_only=sum(
                    m["C"][endpoint] and not m[reference][endpoint]
                    for m in metrics.values()
                ),
                reference_only=sum(
                    m[reference][endpoint] and not m["C"][endpoint]
                    for m in metrics.values()
                ),
            )
    for values in counts.values():
        for arm in ("N", "T"):
            for key in ("false_retirement", "exact", "contradictory"):
                values[arm][key] = None
    for values in metrics.values():
        for arm in ("N", "T"):
            for key in ("false_retirement", "exact", "contradictory"):
                values[arm][key] = None
    return dict(
        paired_discordances=paired,
        verdict="PASS" if all(terms.values()) else "FAIL",
        terms=terms,
        counts=counts,
        episodes=metrics,
        un_release=counts.get("switch-and-return"),
        masking=False,
    )


def pair_input(row):
    """Frozen train_relations.render_pair encoding, without importing a script."""
    rule = row["old_rule"]
    a = f"[target] {rule['status']} {rule['scope']} {rule['text']}"
    metadata = {
        k: rule[k] for k in ("key", "version", "task_id") if rule.get(k) is not None
    }
    if metadata:
        a += " [metadata] " + json.dumps(metadata, sort_keys=True, ensure_ascii=False)
    b = f"[message] {row['role']}: {row['message']} [span] {row['target_span']['text']}"
    if row.get("prev_user"):
        b += f" [prev_user] {row['prev_user']}"
    return a, b

"""FOCUS-2 draft v2: answer-blind text edits and auditable paired CPU consumers.

No script imports, bank reads, device access or output writes at import time.
History/fork/map logic is a narrow adaptation of focus_check35.Engine; repair
follows focus_check37.Engine.repair's placeholder branch as bound by check 39.
Unlike those runners, every request starts with empty KV and contiguous positions.
Strict JSON primitives are locally adapted from sc1_episodes.parse_json,
json_equal and at_path to avoid importing its compiler/governance dependencies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import re
import subprocess
import time
from functools import cache, lru_cache, partial
from pathlib import Path

from stencil.stats import mcnemar_exact_one_sided, tango_upper_bound

ROOT = Path(__file__).resolve().parents[2]
EOS = 151645
END = 151643
CAP = 64
GPU_CAP = 6 * 3600
ARMS = ("neither", "placement-only", "eviction-only", "both", "text-restate")
EVICTION_ARMS = ("eviction-only", "both")
CHECKPOINTS = ("SWITCH", "HOLD", "BACK", "CLEAR", "NEUTRAL2")
REQUESTS = ("SET", "PREHOLD", *CHECKPOINTS)
FAMILIES = {
    "sort": ("ascending", "descending"),
    "case": ("lower", "upper"),
    "fields": ("left", "right"),
    "representation": ("array", "string"),
}
RECAP = (
    "Cancel the superseded task rule: {superseded_rule}.\n"
    "Your earlier answers under that rule followed a rule that no longer "
    "applies; do not imitate your earlier answers; the rules that apply now are:\n"
    "{live_rules_or_default}\n"
    "Use earlier facts when requested, while following the current rules "
    "for this answer."
)
RECAP_HASH = "2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7"
TEMPLATES = {
    "recap": RECAP,
    "system": "Follow the live task rule. Keep earlier facts for later requests.",
    "ascending": "Sort the integers from smallest to largest.",
    "descending": "Sort the integers from largest to smallest.",
    "lower": "Convert every word to lowercase, retaining word order.",
    "upper": "Convert every word to uppercase, retaining word order.",
    "left": "Select the left integer from each record, retaining record order.",
    "right": "Select the right integer from each record, retaining record order.",
    "array": "Represent the items as a JSON integer array, retaining item order.",
    "string": (
        "Represent the items as a comma-separated decimal string without "
        "spaces, retaining item order."
    ),
    "default": (
        "Copy the current payload exactly as a JSON value without the "
        "canceled transformation."
    ),
    "schema": (
        'Output compact JSON with "answer" and integer "tag", without '
        "prose or unrequested keys."
    ),
    "tag": "Keep tag equal to {tag}.",
    "request": "Process this payload: {payload}\n{obligations}",
    "obligations": "Additional requested keys: {keys}.",
    "memo": 'Invent a six-letter ASCII memo and include it as "memo".',
    "recall": "Retrieve the earlier user and tool facts as user_fact and tool_fact.",
    "assistant_recall": "Retrieve your SET memo as assistant_fact.",
    "placement": "{live_rules_or_default}\n",
    "user_fact": "Remember user_fact = {value} for a later request.",
    "tool_request": (
        "Read and remember tool_fact from the fact tool for a later request."
    ),
    "tool_call": '<tool_call>\n{"name":"fact","arguments":{}}\n</tool_call>',
    "tool_return": '{"tool_fact":{value}}',
    "ack": ".",
    "delay": "The room is quiet. " * 102 + "Quiet.",
    "header": "<|im_start|>{role}\n",
    "closure": "<|im_end|>\n",
    "thinking": "<think>\n\n</think>\n\n",
}
CLAIM_CEILING = (
    '"context-management mechanism on a frozen trunk; not compact '
    'state, not waves"; oracle-managed synthetic episodes only, no '
    "autonomous change detection, benchmark transfer, literature "
    "priority, Miller weight-circuit selection, or general safety "
    "claim. Retained HOLD asymmetry and default priors stay visible. "
    "Neither/eviction-only alone cannot carry a headline."
)
EXPECTATION = (
    "Pre-registered expectation for the future FOCUS-2 run: both minus"
    " placement-only is bounded by the demonstration-attributable "
    "share, roughly 10/32 of the historical 29/32 deficit; eviction "
    "does not address the roughly 19/32 pre-demo decay. On the "
    "historical sort SWITCH comparison, inside-request placement "
    "already achieves 27/32, so remaining headroom is at most 5/32 and"
    " the expected eviction gain is smaller. These are scoped "
    "development-based expectations, not a proved numerical ceiling "
    "for the four-family all-five endpoint or an added pass/fail gate."
    " Retain the both-correct mechanism stratum; no new no-answer "
    "control arm is added."
)
READINGS = (
    "Prewritten readings (v1 anchor retained; v2 committed before any "
    "FOCUS-2 outcome, with development outcomes disclosed): PASS "
    "requires competence, all primary comparisons/magnitude and "
    "safety, within scope below; significant but <5-point component "
    "gains -> PASS with MARGINAL ADDED CONTROL, no headline "
    "joint-control claim. Failure to beat placement/text -> no "
    "demonstrated extra mechanism (compatible with prompting), not "
    "equivalence. Repair STOP/loss of CLEAR gains -> release fragile, "
    "do not proceed/promote. Primary benefit plus collateral/breakage "
    "failure -> unsafe context management, do not promote. Benefit "
    "confined to wrong prior answers -> error-demonstration cleanup; "
    "no stale-correct mechanism claim. If both fails, still publish "
    "the fixed placement-only >= text-restate and eviction-only vs "
    "neither secondary readings with their limits above. Other failed "
    "contrasts -> FAIL, not a compact-state conclusion; "
    "INELIGIBLE/INCOMPLETE/INVALID earn no efficacy claim. A null on "
    "the stringent all-five endpoint is not evidence of absence or "
    "established power."
)
HISTORICAL_COST_MIN = {"check37": 14.715, "check38": 8.02, "check39": 16.591}


class Invalid(ValueError):
    status = "INVALID"


class StopRepair(Invalid):
    status = "STOP-REPAIR"


class Ineligible(Invalid):
    status = "INELIGIBLE"


class Incomplete(RuntimeError):
    status = "INCOMPLETE"


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(canonical(value))


def parse_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite")
        return result

    def constant(value):
        raise ValueError("nonfinite")

    return json.loads(
        text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number
    )


def json_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            json_equal(x, y) for x, y in zip(a, b, strict=True)
        )
    return a == b


def at_path(value, path):
    require(path.startswith("/") and not re.search(r"~(?![01])", path), "JSON pointer")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def stream(seed, bank, family, direction, delay, episode, request, purpose):
    key = (
        f"focus2-v1:{seed}:{bank}:{family}:{direction}:{delay}:"
        f"{episode}:{request}:{purpose}"
    )
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def payload(rng, family):
    if family in ("sort", "representation"):
        while True:
            values = rng.sample(range(-99, 100), rng.randint(4, 6))
            if family == "representation":
                return {"items": values}
            if values != sorted(values) and values != sorted(values, reverse=True):
                return values
    if family == "case":
        words = []
        while len(words) < 3:
            word = "".join(
                rng.choice("abcdefghijklmnopqrstuvwxyz")
                for _ in range(rng.randint(3, 6))
            )
            if word in [w.lower() for w in words]:
                continue
            # Each word is mixed, so either canceled skill differs from copy.
            words.append(word[0].upper() + word[1:])
        return words
    require(family == "fields", "family")
    values = rng.sample(range(-99, 100), 6)
    return [{"left": values[i], "right": values[i + 1]} for i in (0, 2, 4)]


def generate_banks():
    banks = {"competence": [], "pilot": [], "final": []}
    for bank, seed, count in (
        ("competence", 9053702, 64),
        ("pilot", 9053702, 1),
        ("final", 9053703, 16),
    ):
        for family, skills in FAMILIES.items():
            for direction in (*skills, "default") if bank == "competence" else skills:
                for delay in (0,) if bank == "competence" else (0, 512):
                    for i in range(count):
                        rng = partial(stream, seed, bank, family, direction, delay, i)
                        facts = rng("SET", "facts").sample(range(10, 100), 2)
                        ep = dict(
                            id=f"{bank}:{family}:{direction}:{delay}:{i}",
                            family=family,
                            direction=direction,
                            delay=delay,
                            index=i,
                            bank=bank,
                            seed=seed,
                            tag=rng("SET", "tag").randint(10, 99),
                            user_fact=facts[0],
                            tool_fact=facts[1],
                            memo=bank != "competence"
                            and i < (4 if bank == "final" else 1),
                        )
                        ep["requests"] = {
                            step: payload(rng(step, "payload"), family)
                            for step in (("SET",) if bank == "competence" else REQUESTS)
                        }
                        banks[bank].append(ep)
    return banks


def fingerprint(family, value):
    if family in ("sort", "representation"):
        value = sorted(value["items"] if family == "representation" else value)
        family = "integer-set"
    elif family == "case":
        value = sorted(w.casefold() for w in value)
    elif family == "fields":
        value = [[r["left"], r["right"]] for r in value]
    else:
        raise Invalid("family")
    return digest([family, value])


def validate_banks(banks, development):
    require(development is not None, "missing outcome-free development manifest")
    require(set(development) == {"coverage", "fingerprints"}, "development fields")
    require(
        set(development["coverage"]) == {*range(31, 40), "repair"},
        "development coverage",
    )
    require(
        all(re.fullmatch(r"[0-9a-f]{64}", x) for x in development["fingerprints"]),
        "development fingerprints",
    )
    seen = set(development["fingerprints"])
    for rows in banks.values():
        for ep in rows:
            for value in ep["requests"].values():
                fp = fingerprint(ep["family"], value)
                require(fp not in seen, "semantic collision (no redraw)")
                seen.add(fp)
    require(banks == generate_banks(), "banks differ from fixed seeded laws/counts")
    return sorted(seen)


def active(ep, step):
    if ep["direction"] == "default" or step in ("CLEAR", "NEUTRAL2"):
        return "default"
    skills = FAMILIES[ep["family"]]
    return (
        skills[1 - skills.index(ep["direction"])]
        if step in ("SWITCH", "HOLD")
        else ep["direction"]
    )


def scope(step):
    return {
        "SET": "SET",
        "PREHOLD": "SET",
        "SWITCH": "SWITCH",
        "HOLD": "SWITCH",
        "BACK": "BACK",
        "CLEAR": "CLEAR",
        "NEUTRAL2": "CLEAR",
    }[step]


def target(family, value, direction):
    if direction == "default":
        return copy.deepcopy(value)
    if family == "sort":
        return sorted(value, reverse=direction == "descending")
    if family == "case":
        return [getattr(w, direction)() for w in value]
    if family == "fields":
        return [r[direction] for r in value]
    return (
        value["items"][:]
        if direction == "array"
        else ",".join(map(str, value["items"]))
    )


def optional_keys(ep, step):
    if step == "SET" and ep["memo"]:
        return ["memo"]
    if step == "NEUTRAL2":
        return ["user_fact", "tool_fact"] + (["assistant_fact"] if ep["memo"] else [])
    return []


def obligations(ep, step):
    keys = optional_keys(ep, step)
    text = TEMPLATES["obligations"].format(keys=", ".join(keys) or "none")
    if "memo" in keys:
        text += " " + TEMPLATES["memo"]
    if "user_fact" in keys:
        text += " " + TEMPLATES["recall"]
    if "assistant_fact" in keys:
        text += " " + TEMPLATES["assistant_recall"]
    return text


def rule(ep, step):
    return TEMPLATES[active(ep, step)]


def live_rules(ep, step):
    return "\n".join(
        (
            rule(ep, step),
            TEMPLATES["schema"],
            TEMPLATES["tag"].format(tag=ep["tag"]),
            obligations(ep, step),
        )
    )


def current_cue(ep, arm, step):
    if arm == "text-restate":
        retired = {
            "SWITCH": "SET",
            "HOLD": "SET",
            "BACK": "SWITCH",
            "CLEAR": "BACK",
            "NEUTRAL2": "BACK",
        }
        return (
            RECAP.format(
                superseded_rule=rule(ep, retired[step]).rstrip("."),
                live_rules_or_default=live_rules(ep, step),
            )
            + "\n"
        )
    if arm in ("placement-only", "both") and step in ("SWITCH", "BACK", "CLEAR"):
        return TEMPLATES["placement"].format(live_rules_or_default=live_rules(ep, step))
    return None


def request_text(ep, step):
    return TEMPLATES["request"].format(
        payload=canonical(ep["requests"][step]), obligations=obligations(ep, step)
    )


def gold(ep, step, memo="abcdef"):
    value = dict(
        answer=target(ep["family"], ep["requests"][step], active(ep, step)),
        tag=ep["tag"],
    )
    for key in optional_keys(ep, step):
        value[key] = memo if key in ("memo", "assistant_fact") else ep[key]
    return canonical(value)


def encode(tok, text):
    value = tok.encode(text, add_special_tokens=False)
    return list(value.ids if hasattr(value, "ids") else value)


def delay_text(tok):
    text = TEMPLATES["delay"]
    require(
        len(encode(tok, text)) == 512, "delay user content must be exactly 512 tokens"
    )
    return text


def repetitive(ids):
    return any(
        ids[i : i + p] * 8 == ids[i : i + p * 8]
        for p in range(1, 5)
        for i in range(len(ids) - p * 8 + 1)
    )


def neutral_flags(text, ids, eos):
    flags = dict(
        empty=not text.strip(),
        placeholder=text.strip() == ".",
        truncated=eos not in (EOS, END),
        repetitive=repetitive(ids),
    )
    return dict(**flags, broken=any(flags.values()))


def answer_shape(value, family, direction):
    def integers(xs):
        return isinstance(xs, list) and all(type(x) is int for x in xs)

    if family == "case":
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    if family == "fields":
        return (
            integers(value)
            or isinstance(value, list)
            and all(
                isinstance(r, dict)
                and set(r) == {"left", "right"}
                and all(type(x) is int for x in r.values())
                for r in value
            )
        )
    if family == "representation":
        # Both active representations are structurally valid task values.
        return (
            integers(value)
            or isinstance(value, str)
            or isinstance(value, dict)
            and set(value) == {"items"}
            and integers(value["items"])
        )
    return integers(value)


def memo_source(text):
    try:
        memo = at_path(parse_json(text), "/memo")
    except (ValueError, TypeError, RecursionError):
        return None
    return (
        memo if isinstance(memo, str) and re.fullmatch(r"[A-Za-z]{6}", memo) else None
    )


def score(ep, step, text, ids, eos, *, source_memo=None):
    try:
        value = parse_json(text)
    except (ValueError, TypeError, RecursionError):
        value = None
    schema = (
        isinstance(value, dict)
        and {"answer", "tag"} <= value.keys()
        and value.keys() <= {"answer", "tag", *optional_keys(ep, step)}
        and type(value["tag"]) is int
        and answer_shape(value["answer"], ep["family"], active(ep, step))
    )
    task = bool(
        schema
        and json_equal(
            value["answer"],
            target(ep["family"], ep["requests"][step], active(ep, step)),
        )
    )
    constraint = bool(schema and value["tag"] == ep["tag"])
    flags = dict(
        empty=not text.strip(),
        placeholder=text.strip() == ".",
        schema_invalid=not schema,
        truncated=eos not in (EOS, END),
        repetitive=repetitive(ids),
    )
    broken = any(flags.values())
    collateral = {}
    for key in optional_keys(ep, step):
        if key == "memo":
            collateral[key] = memo_source(text) is not None
        else:
            expected = source_memo if key == "assistant_fact" else ep[key]
            collateral[key] = bool(
                schema and expected is not None and json_equal(value.get(key), expected)
            )
    return dict(
        **flags,
        broken=broken,
        task=task,
        constraint=constraint,
        success=task and constraint and not broken,
        collateral=collateral,
        imposition={
            d: bool(
                schema
                and json_equal(
                    value["answer"], target(ep["family"], ep["requests"][step], d)
                )
            )
            for d in (*FAMILIES[ep["family"]], "default")
        },
    )


class History:
    """Message ownership is public; body edits never consult answers or scores."""

    def __init__(self, tok):
        self.tok, self.messages, self.serial = tok, [], 0

    def fork(self):
        result = History(self.tok)
        result.messages, result.serial = copy.deepcopy(self.messages), self.serial
        return result

    def part(self, kind, ids, event):
        self.serial += 1
        return dict(id=self.serial, kind=kind, scope=event, ids=list(ids))

    def message(self, role, kind, event, pieces, *, closed=True):
        parts = [
            self.part(
                "header", encode(self.tok, TEMPLATES["header"].format(role=role)), event
            )
        ]
        parts += [self.part(k, ids, ev) for k, ids, ev in pieces]
        if closed:
            parts.append(
                self.part("closure", encode(self.tok, TEMPLATES["closure"]), event)
            )
        self.messages.append(
            dict(
                role=role, kind=kind, scope=event, turn=len(self.messages), parts=parts
            )
        )

    def pair(self, kind, event, user, ids, eos):
        self.validate()
        self.message("user", kind, event, [("input", encode(self.tok, user), event)])
        self.message(
            "assistant",
            kind,
            event,
            [("body", encode(self.tok, TEMPLATES["thinking"]), event)],
            closed=False,
        )
        self.answer(ids, eos)

    def request(self, ep, step, cue=None):
        self.validate()
        event = scope(step)
        pieces = []
        if cue:
            pieces.append(("cue", encode(self.tok, cue), event))
        pieces.append(("input", encode(self.tok, request_text(ep, step)), event))
        self.message("user", "task", event, pieces)
        self.message(
            "assistant",
            "task",
            event,
            [("body", encode(self.tok, TEMPLATES["thinking"]), event)],
            closed=False,
        )
        self.validate(current=True)

    def answer(self, ids, eos):
        self.validate(current=True)
        msg = self.messages[-1]
        msg["parts"][-1]["ids"].extend(ids)
        event = msg["scope"]
        # Preserve the generated EOS even when endoftext needs an im_end closure.
        if eos is not None:
            msg["parts"].append(self.part("generated_eos", [eos], event))
        closure = encode(self.tok, "\n" if eos == EOS else TEMPLATES["closure"])
        msg["parts"].append(self.part("closure", closure, event))
        self.validate()

    def validate(self, current=False):
        expected = "user"
        for i, msg in enumerate(self.messages):
            role = msg["role"]
            require(msg["turn"] == i, "turn ownership")
            require(msg["parts"] and msg["parts"][0]["kind"] == "header", "header")
            require(
                msg["parts"][0]["ids"]
                == encode(self.tok, TEMPLATES["header"].format(role=role)),
                "role header",
            )
            pending = current and i == len(self.messages) - 1
            if role == "system":
                require(i == 0, "system slot")
            else:
                require(
                    role == expected,
                    "unanswered historical user or malformed tool group",
                )
                if role == "user":
                    expected = "assistant"
                elif role == "tool":
                    expected = "assistant"
                else:
                    expected = "tool" if msg["kind"] == "tool_call" else "user"
            if pending:
                require(
                    role == "assistant" and msg["parts"][-1]["kind"] == "body",
                    "current generation prefill",
                )
            else:
                require(
                    msg["parts"][-1]["kind"] == "closure", "unanswered history/closure"
                )
                tail = [t for p in msg["parts"][-2:] for t in p["ids"]]
                require(
                    tail[-len(encode(self.tok, TEMPLATES["closure"])) :]
                    == encode(self.tok, TEMPLATES["closure"]),
                    "valid assistant closure",
                )
            if role == "user" and any(p["kind"] == "cue" for p in msg["parts"]):
                require(
                    msg["kind"] == "task"
                    and any(p["kind"] == "input" and p["ids"] for p in msg["parts"]),
                    "separate moved-cue turn",
                )
            if msg["kind"] == "tool_call":
                body = [
                    t for p in msg["parts"] if p["kind"] == "body" for t in p["ids"]
                ]
                require(
                    body == encode(self.tok, TEMPLATES["tool_call"]),
                    "malformed tool call",
                )
            if role == "tool":
                body = [
                    t for p in msg["parts"] if p["kind"] == "return" for t in p["ids"]
                ]
                try:
                    value = parse_json(self.tok.decode(body))
                except ValueError as exc:
                    raise Invalid("malformed tool return") from exc
                require(
                    isinstance(value, dict)
                    and set(value) == {"tool_fact"}
                    and type(value["tool_fact"]) is int
                    and 10 <= value["tool_fact"] <= 99,
                    "malformed tool fact",
                )
        require(expected == "user", "unanswered historical user/tool group")

    def render(self, current=False):
        self.validate(current=current)
        ids, tokens, segments = [], [], []
        for msg in self.messages:
            for p in msg["parts"]:
                segments.append(
                    dict(
                        id=p["id"],
                        kind=p["kind"],
                        scope=p["scope"],
                        turn=msg["turn"],
                        role=msg["role"],
                        start=len(ids),
                        end=len(ids) + len(p["ids"]),
                    )
                )
                ids.extend(p["ids"])
                tokens.extend([len(segments) - 1] * len(p["ids"]))
        return dict(
            ids=ids, tokens=tokens, segments=segments, positions=list(range(len(ids)))
        )


def initial_history(tok, ep):
    h = History(tok)
    h.message(
        "system",
        "rules",
        "base",
        [
            ("base", encode(tok, TEMPLATES["system"] + "\n"), "base"),
            ("cue", encode(tok, live_rules(ep, "SET") + "\n"), "SET"),
        ],
    )
    h.pair(
        "fact",
        "user-fact",
        TEMPLATES["user_fact"].format(value=ep["user_fact"]),
        [13],
        EOS,
    )
    h.message(
        "user",
        "fact",
        "tool-fact",
        [("input", encode(tok, TEMPLATES["tool_request"]), "tool-fact")],
    )
    h.message(
        "assistant",
        "tool_call",
        "tool-fact",
        [("body", encode(tok, TEMPLATES["tool_call"]), "tool-fact")],
    )
    h.message(
        "tool",
        "tool_return",
        "tool-fact",
        [
            (
                "return",
                encode(
                    tok,
                    TEMPLATES["tool_return"].replace("{value}", str(ep["tool_fact"])),
                ),
                "tool-fact",
            )
        ],
    )
    h.message("assistant", "fact", "tool-fact", [("body", [13], "tool-fact")])
    h.validate()
    return h


def competence_history(tok, ep):
    """Immediate visible-cue trials have no intervening facts or delays."""
    h = History(tok)
    h.message(
        "system", "rules", "base", [("base", encode(tok, TEMPLATES["system"]), "base")]
    )
    return h


def intervene(history, ep, arm, step):
    require(arm in ARMS and step in ("SWITCH", "BACK", "CLEAR"), "intervention")
    original = history.render()
    retired = {"SWITCH": "SET", "BACK": "SWITCH", "CLEAR": "BACK"}[step]
    removed, retired_cues = [], []
    for msg in history.messages:
        survivors = []
        for p in msg["parts"]:
            if p["kind"] == "cue" and p["scope"] == retired:
                retired_cues.append(copy.deepcopy(p))
                continue
            if (
                arm in EVICTION_ARMS
                and msg["kind"] == "task"
                and msg["role"] == "assistant"
                and p["kind"] == "body"
                and p["scope"] == retired
            ):
                require(p["ids"], "vacuous body removal")
                removed.append(
                    dict(
                        id=p["id"],
                        turn=msg["turn"],
                        ids=p["ids"][:],
                        sha256=digest(p["ids"]),
                        replacement_tokens=[13],
                    )
                )
                p = history.part("repaired_body", [13], retired)
            survivors.append(p)
        msg["parts"] = survivors
    require(retired_cues, "vacuous cue retirement")
    if arm in EVICTION_ARMS:
        require(removed, "vacuous answer removal")
    if arm in ("neither", "eviction-only"):
        history.messages[0]["parts"].insert(
            -1,
            history.part(
                "cue", encode(history.tok, live_rules(ep, step) + "\n"), scope(step)
            ),
        )
    edited = history.render()
    lookup = {
        (s["id"], offset): s["start"] + offset
        for s in edited["segments"]
        for offset in range(s["end"] - s["start"])
    }
    mapping = [
        lookup.get((s["id"], offset))
        for s in original["segments"]
        for offset in range(s["end"] - s["start"])
    ]
    kept = [(i, j) for i, j in enumerate(mapping) if j is not None]
    require(
        kept and all(original["ids"][i] == edited["ids"][j] for i, j in kept),
        "nonvacuous survivor token identity",
    )
    return dict(
        retired_event=retired,
        original=original,
        edited=edited,
        original_to_edited=mapping,
        removed_bodies=removed,
        retired_cues=retired_cues,
        survivor_count=len(kept),
    )


@cache
def paired_interval(b, c, n):
    require(
        type(b) is int
        and type(c) is int
        and 0 <= b
        and 0 <= c
        and b + c <= n
        and n > 0,
        "paired table",
    )

    # At the parameter boundary +1 the upper endpoint is exactly +1; the
    # generic inversion's open feasible interval cannot evaluate that point.
    def upper(x, y):
        return 1.0 if x == n else tango_upper_bound(x, y, n, alpha=0.025)

    try:
        interval = [-upper(c, b), upper(b, c)]
        require(
            all(math.isfinite(x) for x in interval)
            and -1 <= interval[0] <= (b - c) / n <= interval[1] <= 1,
            "paired numerical inversion failure",
        )
        return interval
    except (ValueError, RuntimeError) as exc:
        raise Invalid(f"paired numerical inversion failure: {exc}") from exc


def paired(candidate, comparator):
    require(len(candidate) == len(comparator), "unpaired observations")
    require(all(type(x) is bool for x in candidate + comparator), "binary outcomes")
    n = len(candidate)
    a = sum(x and y for x, y in zip(candidate, comparator, strict=True))
    b = sum(x and not y for x, y in zip(candidate, comparator, strict=True))
    c = sum(not x and y for x, y in zip(candidate, comparator, strict=True))
    return dict(
        n=n,
        a=a,
        b=b,
        c=c,
        d=n - a - b - c,
        table=[[a, b], [c, n - a - b - c]],
        candidate=sum(candidate),
        comparator=sum(comparator),
        delta=(b - c) / n if n else None,
        interval=paired_interval(b, c, n) if n else None,
        p=mcnemar_exact_one_sided(b, c) if n else None,
        interval_method="nominal inverted paired-score 95% (asymptotic)",
    )


def holm(pvalues):
    require(
        len(pvalues) == 3 and all(math.isfinite(p) and 0 <= p <= 1 for p in pvalues),
        "exactly three primary Holm tests",
    )
    out, previous = [None] * 3, 0.0
    for rank, index in enumerate(sorted(range(3), key=lambda i: pvalues[i])):
        previous = max(previous, min(1.0, (3 - rank) * pvalues[index]))
        out[index] = previous
    return out


@cache
def exact_upper(k, n):
    require(
        type(k) is int and type(n) is int and 0 <= k <= n and n > 0, "binomial count"
    )
    if k == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        p = (lo + hi) / 2
        cdf = sum(math.comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k + 1))
        if cdf > 0.05:
            lo = p
        else:
            hi = p
    return (lo + hi) / 2


def contrasts(rows):
    return {
        a: paired(
            [r["arms"]["both"]["Y"] for r in rows], [r["arms"][a]["Y"] for r in rows]
        )
        for a in ("placement-only", "eviction-only", "text-restate")
    }


def decisions(rows, terminal="COMPLETE"):
    require(len({r["id"] for r in rows}) == len(rows), "duplicate episode")
    primary = contrasts(rows)
    complete = len(rows) == 256 and terminal == "COMPLETE"
    if rows:
        for a, p in zip(primary, holm([x["p"] for x in primary.values()]), strict=True):
            primary[a]["adjusted_p"] = p
    primary_pass = complete and all(
        x["b"] > x["c"] and x["adjusted_p"] <= 0.05 for x in primary.values()
    )
    primary_pass = (
        primary_pass
        and primary["text-restate"]["b"] - primary["text-restate"]["c"] >= 13
    )
    safety = paired(
        [r["arms"]["both"]["broken"] for r in rows],
        [r["arms"]["text-restate"]["broken"] for r in rows],
    )
    safety.update(
        h=safety["b"],
        r=safety["c"],
        fixed_n=256,
        upper_h=exact_upper(safety["b"], 256) if complete else None,
        passes=bool(complete and safety["b"] <= 2 and safety["p"] > 0.05),
    )
    collateral = {}
    for key, fixed_n in (
        ("user_fact", 256),
        ("tool_fact", 256),
        ("assistant_fact", 64),
        ("constraint", 256),
    ):
        selected = [r for r in rows if key != "assistant_fact" or r["memo"]]
        table = paired(
            [r["arms"]["both"][key] for r in selected],
            [r["arms"]["text-restate"][key] for r in selected],
        )
        table.update(
            fixed_n=fixed_n,
            passes=complete
            and len(selected) == fixed_n
            and table["candidate"] <= table["comparator"],
        )
        collateral[key] = table
    safety["passes"] = safety["passes"] and all(
        x["passes"] for x in collateral.values()
    )
    if not complete:
        status = terminal if terminal != "COMPLETE" else "INCOMPLETE"
    elif not safety["passes"]:
        status = "FAIL-SAFETY"
    elif not primary_pass:
        status = "FAIL"
    elif any(x["delta"] < 0.05 for x in primary.values()):
        status = "PASS with MARGINAL ADDED CONTROL"
    else:
        status = "PASS"
    secondary = {}
    for a, b, label in (
        ("placement-only", "text-restate", "placement-only >= text-restate"),
        ("eviction-only", "neither", "eviction-only vs neither"),
    ):
        secondary[label] = paired(
            [r["arms"][a]["Y"] for r in rows], [r["arms"][b]["Y"] for r in rows]
        )
        secondary[label]["observed_candidate_ge"] = (
            secondary[label]["candidate"] >= secondary[label]["comparator"]
        )
    strata = {}
    for field in ("family", "direction", "delay", "both_correct"):
        values = (
            (True, False)
            if field == "both_correct"
            else sorted({r[field] for r in rows})
        )
        strata[field] = {
            str(v): contrasts([r for r in rows if r[field] == v]) for v in values
        }
    source_strata = {}
    for valid in (True, False):
        selected = [r for r in rows if r["memo"] and r["source_valid"] == valid]
        source_strata[str(valid)] = paired(
            [r["arms"]["both"]["assistant_fact"] for r in selected],
            [r["arms"]["text-restate"]["assistant_fact"] for r in selected],
        )
    correct = strata["both_correct"]["True"]["placement-only"]
    errors = strata["both_correct"]["False"]["placement-only"]
    if not correct["n"]:
        mechanism = "Empty both-correct stratum: uninformative, no mechanism claim."
    elif correct["delta"] <= 0 and errors["n"] and errors["delta"] > 0:
        mechanism = (
            "Observed benefit is error-demonstration cleanup; "
            "no stale-correct mechanism claim."
        )
    else:
        mechanism = (
            "The both-correct stratum supplies the stale-demonstration "
            "estimate; stratified tests are descriptive."
        )
    return dict(
        status=status,
        complete=complete,
        n=len(rows),
        fixed_n=256,
        primary=primary,
        primary_pass=primary_pass,
        safety=safety,
        collateral=collateral,
        secondary=secondary,
        strata=strata,
        source_validity=source_strata,
        mechanism_reading=mechanism,
        source_missing=sum(r["memo"] and not r["source_valid"] for r in rows),
        secondary_limit=(
            "Observed parity is not demonstrated noninferiority/equivalence; "
            "descriptive comparisons cannot rescue primary/safety failure or "
            "carry the headline claim."
        ),
        safety_limit=(
            "Absence of detected harm plus a count cap; not proof of noninferiority."
        ),
        expectation=EXPECTATION,
        prewritten_readings=READINGS,
        claim_ceiling=CLAIM_CEILING,
        historical_gpu_minutes=HISTORICAL_COST_MIN,
    )


REQUIRED_RECORD = set(
    (
        "stage episode family direction delay arm checkpoint input_text input_ids "
        "output_text output_ids eos shared_prior_hash prior_correctness both_correct "
        "source_facts source_status live_rules event_scope input_layout edit flags "
        "cost binding complete history_closure_ids delay_user_tokens "
        "complete_delay_tokens"
    ).split()
)


def atomic_json(path, value):
    """Exclusive immutable publication; a crash leaves a diagnostic partial file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    require(not path.exists() and not temp.exists(), "refusing output overwrite/retry")
    with temp.open("x", encoding="utf-8") as handle:
        handle.write(canonical(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    # link, unlike replace, fails if another writer already published this name.
    os.link(temp, path)
    temp.unlink()
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class RecordStore:
    def __init__(self, path):
        self.path = Path(path)

    def write(self, record):
        require(REQUIRED_RECORD <= record.keys(), "missing durable request fields")
        key = digest([record["episode"], record["arm"], record["checkpoint"]])
        atomic_json(
            self.path / (key + ".json"), {"record": record, "sha256": digest(record)}
        )

    def rows(self):
        require(not list(self.path.glob("*.partial")), "interrupted record publication")
        result = []
        for path in sorted(self.path.glob("*.json")):
            value = parse_json(path.read_text())
            require(
                set(value) == {"record", "sha256"}
                and digest(value["record"]) == value["sha256"],
                "corrupt record hash",
            )
            row = value["record"]
            require(
                path.stem == digest([row["episode"], row["arm"], row["checkpoint"]]),
                "record identity",
            )
            result.append(row)
        return result


class Budget:
    def __init__(self, clock=time.monotonic, spent=0.0, cap=GPU_CAP):
        require(0 <= spent <= GPU_CAP and 0 < cap <= GPU_CAP, "cost over cap")
        self.clock, self.spent, self.cap = clock, spent, cap
        self.started = clock()

    def elapsed(self):
        return self.spent + max(0.0, self.clock() - self.started)

    def check(self, projection=0.0):
        if self.elapsed() + projection >= self.cap:
            raise Incomplete("GPU allocation budget exhausted/projected over cap")


class Engine:
    def __init__(self, tok, backend, store, budget, binding):
        self.tok, self.backend, self.store = tok, backend, store
        self.budget, self.binding = budget, binding

    def answer(self, history, ep, arm, step, *, edit=None, prior=None, source=None):
        layout = history.render(current=True)
        require(layout["ids"], "empty prefill")
        record = dict(
            stage=ep["bank"],
            episode=ep["id"],
            family=ep["family"],
            direction=ep["direction"],
            delay=ep["delay"],
            arm=arm,
            checkpoint=step,
            input_ids=layout["ids"],
            input_text=self.tok.decode(layout["ids"], skip_special_tokens=False),
            input_layout=layout,
            edit=edit,
            binding=self.binding,
            live_rules=live_rules(ep, step) if not step.startswith("DELAY") else None,
            event_scope=scope(step) if not step.startswith("DELAY") else step,
            output_ids=[],
            output_text="",
            eos=None,
            flags=None,
            source_facts={
                "user_fact": ep["user_fact"],
                "tool_fact": ep["tool_fact"],
                "assistant_fact": source,
            },
            source_status="valid"
            if source
            else "missing"
            if ep["memo"]
            else "not-requested",
            shared_prior_hash=digest(prior) if prior is not None else None,
            prior_correctness=[p["flags"] for p in prior] if prior else [],
            both_correct=bool(prior and all(p["flags"]["success"] for p in prior)),
            complete=False,
            cost={},
        )
        start, prefill_seconds, decode_seconds, steps = self.budget.clock(), 0.0, 0.0, 0
        decode_calls = 0
        error = None
        try:
            self.budget.check()
            cache = self.backend.empty()
            before = self.budget.clock()
            try:
                token = self.backend.prefill(
                    layout["ids"],
                    cache,
                    layout,
                    dict(episode=ep, arm=arm, checkpoint=step),
                )
            finally:
                prefill_seconds = self.budget.clock() - before
            self.budget.check()
            for i in range(CAP):
                self.budget.check()
                require(type(token) is int and token >= 0, "invalid greedy token")
                steps += 1
                if token in (EOS, END):
                    record["eos"] = token
                    break
                record["output_ids"].append(token)
                if i < CAP - 1:
                    self.budget.check()
                    before = self.budget.clock()
                    decode_calls += 1
                    try:
                        token = self.backend.decode(token, cache)
                    finally:
                        decode_seconds += self.budget.clock() - before
                    self.budget.check()
            record["complete"] = True
        except (Exception, KeyboardInterrupt) as exc:
            error = exc
        finally:
            record["output_text"] = self.tok.decode(
                record["output_ids"], skip_special_tokens=False
            )
            if not step.startswith("DELAY"):
                record["flags"] = score(
                    ep,
                    step,
                    record["output_text"],
                    record["output_ids"],
                    record["eos"],
                    source_memo=source,
                )
            else:
                record["flags"] = neutral_flags(
                    record["output_text"], record["output_ids"], record["eos"]
                )
            record["history_closure_ids"] = encode(
                self.tok, "\n" if record["eos"] == EOS else TEMPLATES["closure"]
            )
            record["delay_user_tokens"] = 512 if step.startswith("DELAY") else 0
            record["complete_delay_tokens"] = (
                (
                    len(layout["ids"])
                    + len(record["output_ids"])
                    + (record["eos"] is not None)
                    + len(record["history_closure_ids"])
                )
                if step.startswith("DELAY")
                else 0
            )
            record["cost"] = dict(
                allocation_seconds=self.budget.clock() - start,
                prefill_seconds=prefill_seconds,
                decode_seconds=decode_seconds,
                emitted_tokens=steps,
                decode_calls=decode_calls,
                prefill_tokens=len(layout["ids"]),
                cumulative_seconds=self.budget.elapsed(),
                peak_memory_bytes=self.backend.peak_memory,
            )
            self.store.write(record)
        if error:
            raise error
        history.answer(record["output_ids"], record["eos"])
        return record


def neutral_history(tok, text, event):
    history = History(tok)
    history.message("user", "neutral", event, [("input", encode(tok, text), event)])
    history.message(
        "assistant",
        "neutral",
        event,
        [("body", encode(tok, TEMPLATES["thinking"]), event)],
        closed=False,
    )
    return history


def prior_packet(records):
    return [
        {k: r[k] for k in ("checkpoint", "output_ids", "output_text", "eos", "flags")}
        for r in records
    ]


def episode(engine, ep):
    delays = {}
    if ep["delay"]:
        text = delay_text(engine.tok)
        for step in ("DELAY0", "DELAY1", "DELAY2"):
            h = neutral_history(engine.tok, text, step)
            delays[step] = engine.answer(h, ep, "shared", step)

    def replay(h, step):
        if step in delays:
            r = delays[step]
            h.pair("neutral", step, delay_text(engine.tok), r["output_ids"], r["eos"])

    h = initial_history(engine.tok, ep)
    priors = []
    for step in ("SET", "PREHOLD"):
        if step == "PREHOLD":
            replay(h, "DELAY0")
        h.request(ep, step)
        priors.append(engine.answer(h, ep, "shared", step))
    prior = prior_packet(priors)
    memo = memo_source(priors[0]["output_text"]) if ep["memo"] else None
    branches = {a: h.fork() for a in ARMS}
    rows = []
    for step in CHECKPOINTS:
        for arm in ARMS:
            h = branches[arm]
            edit = (
                intervene(h, ep, arm, step)
                if step in ("SWITCH", "BACK", "CLEAR")
                else None
            )
            if step in ("HOLD", "NEUTRAL2"):
                replay(h, "DELAY1" if step == "HOLD" else "DELAY2")
            h.request(ep, step, cue=current_cue(ep, arm, step))
            rows.append(
                engine.answer(h, ep, arm, step, edit=edit, prior=prior, source=memo)
            )
    return rows


def validate_records(records, episodes, tok, binding, *, complete):
    """Replay the exact renderer/removal consumer from immutable raw responses."""
    indexed = {}
    by_id = {ep["id"]: ep for ep in episodes}
    for r in records:
        require(
            REQUIRED_RECORD <= r.keys() and r["binding"] == binding,
            "record binding/fields",
        )
        key = r["episode"], r["arm"], r["checkpoint"]
        require(
            key not in indexed and r["episode"] in by_id, "duplicate/unpaired record"
        )
        indexed[key] = r
        ep = by_id[r["episode"]]
        require(
            all(r[k] == ep[k] for k in ("family", "direction", "delay")),
            "pair metadata",
        )
        require(
            r["output_text"] == tok.decode(r["output_ids"], skip_special_tokens=False),
            "output text/token mismatch",
        )
        require(
            len(r["output_ids"]) + (r["eos"] is not None) <= CAP
            and r["eos"] in (None, EOS, END),
            "output cap/EOS",
        )
        require(
            all(type(t) is int and t >= 0 for t in r["output_ids"]), "output tokens"
        )
        require(
            all(
                isinstance(v, (float, int))
                and not isinstance(v, bool)
                and math.isfinite(v)
                and v >= 0
                for v in r["cost"].values()
            ),
            "cost counters",
        )
        cost = r["cost"]
        require(
            type(r["complete"]) is bool
            and cost["emitted_tokens"] == len(r["output_ids"]) + (r["eos"] is not None)
            and cost["prefill_tokens"] == len(r["input_ids"])
            and cost["decode_calls"] <= CAP - 1,
            "inconsistent token counter",
        )
        if r["complete"]:
            require(
                cost["decode_calls"] == max(0, cost["emitted_tokens"] - 1),
                "decode counter",
            )
        require(
            cost["allocation_seconds"]
            >= cost["prefill_seconds"] + cost["decode_seconds"],
            "allocation counter",
        )
        expected_closure = encode(
            tok, "\n" if r["eos"] == EOS else TEMPLATES["closure"]
        )
        require(
            r["history_closure_ids"] == expected_closure, "history closure metadata"
        )
    consumed, summaries = set(), []

    def consume(ep, arm, step, h, *, edit=None, prior=None, memo=None):
        key = ep["id"], arm, step
        if key not in indexed:
            require(not complete, "incomplete pairing")
            return None
        r = indexed[key]
        consumed.add(key)
        layout = h.render(current=True)
        require(
            r["input_layout"] == layout
            and r["input_ids"] == layout["ids"]
            and r["input_text"] == tok.decode(layout["ids"], skip_special_tokens=False),
            "renderer/history/map mismatch",
        )
        require(r["edit"] == edit, "removal consumer mismatch")
        require(
            r["shared_prior_hash"] == (digest(prior) if prior is not None else None)
            and r["prior_correctness"] == ([p["flags"] for p in prior] if prior else [])
            and r["both_correct"]
            == bool(prior and all(p["flags"]["success"] for p in prior)),
            "shared priors mismatch",
        )
        require(
            r["source_facts"]
            == {
                "user_fact": ep["user_fact"],
                "tool_fact": ep["tool_fact"],
                "assistant_fact": memo,
            },
            "source facts mismatch",
        )
        require(
            r["source_status"]
            == ("valid" if memo else "missing" if ep["memo"] else "not-requested"),
            "source status mismatch",
        )
        require(r["stage"] == ep["bank"], "stage pairing")
        if not step.startswith("DELAY"):
            require(
                r["flags"]
                == score(
                    ep,
                    step,
                    r["output_text"],
                    r["output_ids"],
                    r["eos"],
                    source_memo=memo,
                ),
                "checker mismatch",
            )
            require(
                r["live_rules"] == live_rules(ep, step)
                and r["event_scope"] == scope(step),
                "live scope mismatch",
            )
        else:
            require(
                r["flags"] == neutral_flags(r["output_text"], r["output_ids"], r["eos"])
                and r["delay_user_tokens"] == 512
                and r["complete_delay_tokens"]
                == len(layout["ids"])
                + len(r["output_ids"])
                + (r["eos"] is not None)
                + len(r["history_closure_ids"]),
                "delay counters/flags",
            )
        if not r["complete"]:
            require(not complete, "partial request")
            return None
        h.answer(r["output_ids"], r["eos"])
        return r

    for ep in episodes:
        delays = {}
        for step in ("DELAY0", "DELAY1", "DELAY2") if ep["delay"] else ():
            h = neutral_history(tok, delay_text(tok), step)
            delays[step] = consume(ep, "shared", step, h)

        def replay(h, step, ep=ep, delays=delays):
            if not ep["delay"]:
                return True
            r = delays[step]
            if r is None:
                return False
            h.pair("neutral", step, delay_text(tok), r["output_ids"], r["eos"])
            return True

        h = (
            competence_history(tok, ep)
            if ep["bank"] == "competence"
            else initial_history(tok, ep)
        )
        priors = []
        for step in ("SET",) if ep["bank"] == "competence" else ("SET", "PREHOLD"):
            if step == "PREHOLD" and not replay(h, "DELAY0"):
                break
            h.request(
                ep,
                step,
                cue=live_rules(ep, step) + "\n" if ep["bank"] == "competence" else None,
            )
            r = consume(ep, "shared", step, h)
            if r is None:
                break
            priors.append(r)
        if ep["bank"] == "competence":
            if priors:
                summaries.append(
                    dict(
                        id=ep["id"],
                        family=ep["family"],
                        direction=ep["direction"],
                        success=priors[0]["flags"]["success"],
                    )
                )
            continue
        if len(priors) < 2:
            continue
        prior = prior_packet(priors)
        memo = memo_source(priors[0]["output_text"]) if ep["memo"] else None
        arm_summaries = {}
        for arm in ARMS:
            branch, rs = h.fork(), []
            for step in CHECKPOINTS:
                edit = (
                    intervene(branch, ep, arm, step)
                    if step in ("SWITCH", "BACK", "CLEAR")
                    else None
                )
                if step in ("HOLD", "NEUTRAL2") and not replay(
                    branch, "DELAY1" if step == "HOLD" else "DELAY2"
                ):
                    break
                branch.request(ep, step, cue=current_cue(ep, arm, step))
                r = consume(ep, arm, step, branch, edit=edit, prior=prior, memo=memo)
                if r is None:
                    break
                rs.append(r)
            if len(rs) == 5:
                arm_summaries[arm] = dict(
                    Y=all(r["flags"]["success"] for r in rs),
                    broken=any(r["flags"]["broken"] for r in rs),
                    constraint=any(not r["flags"]["constraint"] for r in rs),
                    **{
                        key: not rs[-1]["flags"]["collateral"].get(key, False)
                        for key in ("user_fact", "tool_fact", "assistant_fact")
                    },
                )
        if len(arm_summaries) == 5:
            summaries.append(
                dict(
                    id=ep["id"],
                    family=ep["family"],
                    direction=ep["direction"],
                    delay=ep["delay"],
                    memo=ep["memo"],
                    source_valid=memo is not None,
                    both_correct=all(p["flags"]["success"] for p in prior),
                    arms=arm_summaries,
                )
            )
    require(consumed == set(indexed), "orphan or out-of-order partial records")
    require(not complete or len(summaries) == len(episodes), "incomplete episodes")
    return summaries


def load_backend(tok, config):
    """Only the fully validated, future registered foreground path calls this."""
    import torch

    from stencil.qwen3 import KVCache, Qwen3, Qwen3Config

    class Backend:
        def __init__(self):
            cfg = Qwen3Config.from_hf(config["config_path"])
            with torch.device("meta"):
                self.model = Qwen3(cfg)
            self.model.load_state_dict(
                torch.load(
                    ROOT / config["weights_path"],
                    map_location="cpu",
                    weights_only=True,
                    mmap=True,
                ),
                strict=True,
                assign=True,
            )
            for module in self.model.modules():
                if hasattr(module, "hf_compatible"):
                    module.hf_compatible = True
            self.model.requires_grad_(False)
            self.model = self.model.to(device="cuda", dtype=torch.bfloat16).eval()
            require(self.model.hf_compatible, "hf_compatible trunk required")
            self.cfg = cfg

        @property
        def peak_memory(self):
            return torch.cuda.max_memory_allocated()

        def empty(self):
            return KVCache(self.cfg)

        def forward(self, ids, cache):
            with torch.inference_mode():
                return int(
                    self.model(torch.tensor([ids], device="cuda"), cache=cache)[
                        0, -1
                    ].argmax()
                )

        def prefill(self, ids, cache, layout, context):
            require(
                cache.length == 0 and all(v is None for v in cache.k + cache.v),
                "nonempty prefill cache",
            )
            return self.forward(ids, cache)

        def decode(self, token, cache):
            return self.forward([token], cache)

        def close(self):
            self.model = None
            torch.cuda.empty_cache()

    return Backend()


PINS = dict(
    v1_commit="2ea04e97b5b3e3965837329b1df9b412054da3c5",
    v2_commit="7d0c24413b5d9093f814071c37e5c332b3ec62dd",
    ledger="LEDGER-PLAN.md",
    v2_section_sha256=(
        "5ddfd57854045bf17219ba4f1626bfc04cac9e2322c9784bb753cdec2ecbb40c"
    ),
    check36_source="c2946880fc4aea73f6bfb6f6e34994dfd9b2e525",
    check36_paths=[
        "scripts/focus_check36.py",
        "scripts/focus_check35.py",
        "scripts/focus_check34.py",
        "scripts/focus_check32_kv.py",
    ],
    check36_review="results/check36-review-fable.md",
    check36_review_sha256=(
        "4819d670238adc1ae732e19b11958ffd5b1949e59131feacf8c23ac33e45809a"
    ),
    check38_review="results/check38-review-fable.md",
    check38_review_sha256=(
        "44bc884cde860c883718db1125175bcaf334ffde00093a74c66d5e70540ead31"
    ),
    check37_readme="results/quick-checks/check37/README.md",
    prereg_commit="e24afd4b07870b4985d184f4183fea505b72b372",
    receipt_commit="e30343d24cc6e2ad171ae5e44ff2b6d3ea1c18f0",
    summary="results/quick-checks/check39/4b/summary.json",
    summary_sha256="e5b906f54be46d7171d6a90eb670b37bdd6621297f2adc069214926a4c76c951",
    repair_reading="results/quick-checks/check39/4b/prewritten-reading.md",
    prereg_reading="results/quick-checks/check39/README.md",
    repair_readme="results/quick-checks/check39/README.md",
    check39_code="scripts/focus_check39.py",
    repair_code="scripts/focus_check37.py",
    launch="2026-09-05T08:43:10Z",
)
CONFIG = dict(
    model="Qwen3-4B",
    dtype="bf16",
    hf_compatible=True,
    greedy=True,
    thinking=False,
    cap=64,
    gpu_cap_seconds=GPU_CAP,
    arm_order=list(ARMS),
    seeds={"competence": 9053702, "pilot": 9053702, "final": 9053703},
    namespace="focus2-v1",
    repair="placeholder",
    placeholder_ids=[13],
    positions="contiguous",
    cache="empty per request",
)
RUNTIME_SOURCES = {
    "generator": ROOT / "src/stencil/focus2.py",
    "cli": ROOT / "scripts/focus2.py",
    "checker_tests": ROOT / "tests/test_focus2.py",
    "qwen": ROOT / "src/stencil/qwen3.py",
    "stats": ROOT / "src/stencil/stats.py",
    "qwen_default_config": ROOT / "models/qwen3-1.7b-hf/config.json",
}
REQUIRED_FILES = set(
    (
        "banks templates section readings development review config model model_config "
        "tokenizer tokenizer_config qwen qwen_default_config stats generator cli "
        "checker_tests check36_review check38_review check39_summary check39_reading "
        "check39_readme check39_code repair_code check37_readme"
    ).split()
)


def git_bytes(root, *args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise Invalid(
            "missing/invalid Git commit or membership: " + " ".join(args)
        ) from exc


def safe_path(root, relative):
    require(
        isinstance(relative, str)
        and not Path(relative).is_absolute()
        and ".." not in Path(relative).parts,
        "dependency path",
    )
    path = root / relative
    require(
        path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
        "dependency escapes repository",
    )
    return path


def member(root, commit, relative, expected=None):
    path = safe_path(root, relative)
    require(path.is_file(), "missing dependency " + relative)
    require(
        git_bytes(root, "ls-files", "--error-unmatch", "--", relative).strip(),
        "untracked dependency",
    )
    require(
        not git_bytes(root, "status", "--porcelain", "--", relative).strip(),
        "dirty dependency " + relative,
    )
    content = path.read_bytes()
    require(
        git_bytes(root, "show", f"{commit}:{relative}") == content,
        "freeze commit membership/content " + relative,
    )
    if expected is not None:
        require(sha(content) == expected, "dependency hash " + relative)
    return content


def v2_section(text):
    marker = "## FOCUS-2 — PLACEMENT + EVICTION AT INSTRUCTION CHANGE (DRAFT v2,"
    if marker in text:
        text = text[text.index(marker) :]
    return text.split("\n### CPU implementation handoff", 1)[0].rstrip("\n")


def repair_gate(receipt):
    if (
        receipt.get("verdict") != "PROCEED_PLACEHOLDER"
        or receipt.get("preselected_larger_test_variant") != "placeholder"
    ):
        raise StopRepair("absent, STOP or unselected check-39 placeholder policy")
    require(
        receipt.get("placeholder_token_ids") == [13]
        and receipt.get("placeholder_cpu_verified") is True,
        "check39 period binding",
    )
    require(
        receipt.get("n") == 64
        and receipt.get("complete") is True
        and receipt.get("status") == "complete",
        "incomplete repair receipt",
    )
    passes = True
    for mode in ("surviving", "rebuilt"):
        p, c = (receipt["arms"][f"{a}/{mode}"] for a in ("placeholder", "intact"))
        for arm in (p, c):
            broken = arm["broken_episodes"]
            require(
                len(broken) == len(set(broken))
                and all(type(x) is int and 0 <= x < 64 for x in broken),
                "repair episode indices",
            )
            require(
                set(arm["steps"]) == {"RELEASE1", "RELEASE2", "NEUTRAL1", "NEUTRAL2"},
                "repair checkpoint inventory",
            )
            for cell in arm["steps"].values():
                require(
                    cell["n"] == 64
                    and 0 <= cell["success"] <= cell["valid"] <= 64
                    and 0 <= cell["broken"] <= 64,
                    "repair counts",
                )
        pb, cb = set(p["broken_episodes"]), set(c["broken_episodes"])
        b, c_only = len(pb - cb), len(cb - pb)
        passes &= b - c_only <= 2 and mcnemar_exact_one_sided(b, c_only) >= 0.05
        if mode == "surviving":
            passes &= all(
                p["steps"][s]["success"] >= c["steps"][s]["success"] - 2
                for s in ("RELEASE1", "RELEASE2")
            )
        passes &= all(
            a["steps"][s]["success"] >= 56
            for a in (p, c)
            for s in ("NEUTRAL1", "NEUTRAL2")
        )
    return bool(passes)


def verify_evidence(root, manifest, contents):
    for key in (
        "v1_commit",
        "v2_commit",
        "check36_source",
        "prereg_commit",
        "receipt_commit",
    ):
        require(
            manifest["anchors"].get(key) == PINS[key],
            "missing/mismatched outcome anchor " + key,
        )
        require(
            git_bytes(root, "rev-parse", f"{PINS[key]}^{{commit}}").decode().strip()
            == PINS[key],
            "anchor commit",
        )
    v1 = git_bytes(root, "show", f"{PINS['v1_commit']}:{PINS['ledger']}").decode()
    require(
        RECAP in v1 and "Prewritten readings" in v1, "original template/readings anchor"
    )
    original = v2_section(
        git_bytes(root, "show", f"{PINS['v2_commit']}:{PINS['ledger']}").decode()
    )
    require(
        sha(original) == PINS["v2_section_sha256"]
        and contents["section"].decode() == original,
        "immutable v2 section snapshot",
    )
    require(
        all(x in original for x in (RECAP, READINGS, EXPECTATION, CLAIM_CEILING)),
        "v2 prewritten readings",
    )
    require(
        contents["readings"].decode()
        == READINGS + "\n" + EXPECTATION + "\nClaim ceiling: " + CLAIM_CEILING,
        "readings bytes",
    )
    for role, key in (
        ("check36_review", "check36_review"),
        ("check38_review", "check38_review"),
    ):
        require(
            manifest["files"][role]["path"] == PINS[key]
            and sha(contents[role]) == PINS[key + "_sha256"],
            "accuracy review binding",
        )
    require(
        b"ACCURATE-WITH-CORRECTIONS" in contents["check36_review"],
        "check36 incomplete review",
    )
    for i, path in enumerate(PINS["check36_paths"]):
        key = f"check36_source_{i}"
        require(
            key in manifest["files"] and manifest["files"][key]["path"] == path,
            "reviewed source dependency",
        )
        require(
            contents[key]
            == git_bytes(root, "show", f"{PINS['check36_source']}:{path}"),
            "check36 reviewed source mismatch",
        )
    for role, key in (
        ("check39_summary", "summary"),
        ("check39_reading", "repair_reading"),
        ("check39_readme", "repair_readme"),
        ("check39_code", "check39_code"),
        ("repair_code", "repair_code"),
        ("check37_readme", "check37_readme"),
    ):
        require(manifest["files"][role]["path"] == PINS[key], "repair dependency path")
    require(
        sha(contents["check39_summary"]) == PINS["summary_sha256"]
        and contents["check39_summary"]
        == git_bytes(root, "show", f"{PINS['receipt_commit']}:{PINS['summary']}"),
        "check39 receipt provenance",
    )
    receipt = parse_json(contents["check39_summary"])
    require(
        receipt["source_commit"] == PINS["prereg_commit"]
        and receipt["started_utc"] == PINS["launch"],
        "repair launch chronology",
    )
    from datetime import datetime

    prereg_time = (
        git_bytes(root, "show", "-s", "--format=%cI", PINS["prereg_commit"])
        .decode()
        .strip()
    )
    require(
        datetime.fromisoformat(prereg_time) < datetime.fromisoformat(PINS["launch"]),
        "preregistration must precede launch",
    )
    git_bytes(
        root,
        "merge-base",
        "--is-ancestor",
        PINS["prereg_commit"],
        PINS["receipt_commit"],
    )
    require(
        contents["check39_reading"]
        == git_bytes(root, "show", f"{PINS['prereg_commit']}:{PINS['prereg_reading']}"),
        "prewritten check39 reading",
    )
    require(
        contents["check39_readme"]
        == git_bytes(root, "show", f"{PINS['receipt_commit']}:{PINS['repair_readme']}"),
        "check39 readme receipt",
    )
    require(
        contents["check39_readme"].startswith(contents["check39_reading"]),
        "repair reading copy",
    )
    # Only source/reading dependencies are inspected. In particular the historical
    # check37 episode-bank hash in the receipt is retained as receipt metadata;
    # its contents are never opened or used for generation/deduplication.
    for role in ("check39_code", "repair_code", "check39_reading"):
        path = manifest["files"][role]["path"]
        require(
            receipt["source_hashes"].get(path) == sha(contents[role]),
            "repair source hash",
        )
        if role != "check39_reading":
            require(
                contents[role]
                == git_bytes(root, "show", f"{PINS['prereg_commit']}:{path}"),
                "precommitted repair code",
            )
    for path, expected in receipt["source_hashes"].items():
        if path.endswith(".py"):
            source = git_bytes(root, "show", f"{PINS['prereg_commit']}:{path}")
            require(sha(source) == expected, "repair imported-source provenance")
    require(b"STOP" in contents["check37_readme"], "historical check37 STOP record")
    if not repair_gate(receipt):
        raise StopRepair("check39 selected repair fails its prewritten gate")


@lru_cache(maxsize=2)
def template_manifest(tok):
    require(
        sha(RECAP) == RECAP_HASH
        and encode(tok, ".") == [13]
        and tok.token_to_id("<|im_end|>") == EOS,
        "template/period/tokenizer binding",
    )
    delay_text(tok)
    strings = set(TEMPLATES.values())
    banks = generate_banks()
    for bank in banks.values():
        for ep in bank:
            history = initial_history(tok, ep)
            history.validate()
            strings.add(TEMPLATES["user_fact"].format(value=ep["user_fact"]))
            strings.add(
                TEMPLATES["tool_return"].replace("{value}", str(ep["tool_fact"]))
            )
            for step in ep["requests"]:
                strings.update(
                    (
                        request_text(ep, step),
                        live_rules(ep, step),
                        live_rules(ep, step) + "\n",
                    )
                )
                if step in CHECKPOINTS:
                    for arm in ARMS:
                        cue = current_cue(ep, arm, step)
                        if cue:
                            strings.add(cue)
                text = gold(ep, step, memo="qzjxkv")
                require(len(encode(tok, text)) < CAP, "gold output exceeds cap")
                if set(optional_keys(ep, step)) & {"memo", "assistant_fact"}:
                    require(
                        len(encode(tok, text)) + 6 - len(encode(tok, "qzjxkv")) < CAP,
                        "worst-case six-letter memo gold cap",
                    )
                require(
                    score(ep, step, text, encode(tok, text), EOS, source_memo="qzjxkv")[
                        "success"
                    ],
                    "gold checker fixture",
                )
    return dict(
        templates={k: sha(v) for k, v in TEMPLATES.items()},
        rendered={
            sha(s): dict(
                text=s, tokens=encode(tok, s), tokens_sha256=digest(encode(tok, s))
            )
            for s in sorted(strings)
        },
        renderer_fixture_sha256=validate_renderers(tok),
        recap_sha256=RECAP_HASH,
        eos=EOS,
        placeholder_ids=[13],
    )


def validate_renderers(tok):
    """Outcome-free closure/layout assertions before backend construction."""
    hashes = []
    for ep in generate_banks()["pilot"]:
        h = initial_history(tok, ep)
        for step in ("SET", "PREHOLD"):
            if ep["delay"] and step == "PREHOLD":
                h.pair("neutral", "DELAY0", delay_text(tok), [13], EOS)
            h.request(ep, step)
            h.answer(encode(tok, gold(ep, step)), EOS)
        for arm in ARMS:
            branch = h.fork()
            for step in CHECKPOINTS:
                if step in ("SWITCH", "BACK", "CLEAR"):
                    hashes.append(digest(intervene(branch, ep, arm, step)))
                if ep["delay"] and step in ("HOLD", "NEUTRAL2"):
                    branch.pair("neutral", "DELAY", delay_text(tok), [13], EOS)
                branch.request(ep, step, cue=current_cue(ep, arm, step))
                hashes.append(digest(branch.render(current=True)))
                branch.answer(encode(tok, gold(ep, step)), EOS)
    return digest(hashes)


def load_tokenizer(path):
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(path))


def prepare_freeze(directory, *, tok=None, section_text=None, development=None):
    directory = Path(directory)
    require(not directory.exists(), "candidate directory already exists")
    tok = tok or load_tokenizer(ROOT / "models/qwen3-4b-hf/tokenizer.json")
    section_text = section_text or v2_section(
        git_bytes(ROOT, "show", f"{PINS['v2_commit']}:{PINS['ledger']}").decode()
    )
    banks = generate_banks()
    if development is not None:
        validate_banks(banks, development)
    templates = template_manifest(tok)
    directory.mkdir(parents=True)
    for name, value in (("banks", banks), ("templates", templates), ("config", CONFIG)):
        atomic_json(directory / (name + ".json"), value)
    (directory / "section.md").write_text(section_text, encoding="utf-8")
    (directory / "readings.txt").write_text(
        READINGS + "\n" + EXPECTATION + "\nClaim ceiling: " + CLAIM_CEILING,
        encoding="utf-8",
    )
    if development is not None:
        atomic_json(directory / "development.json", development)
    manifest = dict(
        status="DRAFT",
        version=2,
        fit_on="none",
        repair="placeholder",
        anchors={
            k: PINS[k]
            for k in (
                "v1_commit",
                "v2_commit",
                "check36_source",
                "prereg_commit",
                "receipt_commit",
            )
        },
        files={
            p.stem: {"path": p.name, "sha256": sha(p.read_bytes())}
            for p in sorted(directory.iterdir())
        },
        remaining=[
            "outcome-free development/repair dedup manifest"
            if development is None
            else "development manifest commit",
            "all dependency/model/tokenizer/config hashes and commit membership",
            "registration review",
            "committed freeze and external launch receipt",
        ],
        candidate_only=True,
    )
    atomic_json(directory / "manifest.json", manifest)
    return manifest


def preflight(
    folder,
    launch,
    stage,
    output,
    *,
    tok=None,
    tokenizer_factory=None,
    certificates=True,
):
    folder, output = Path(folder).resolve(), Path(output).resolve()
    require(folder.is_dir(), "missing freeze directory")
    manifest_path = folder / "manifest.json"
    require(manifest_path.is_file(), "missing manifest")
    manifest = parse_json(manifest_path.read_text())
    require(manifest.get("status") == "REGISTERED", "DRAFT / NOT REGISTERED")
    if manifest.get("repair") != "placeholder":
        raise StopRepair("absent/unselected repair policy")
    require(
        manifest.get("version") == 2 and manifest.get("fit_on") == "none",
        "registration version/lineage",
    )
    require(manifest.get("candidate_only") is False, "unregistered candidate manifest")
    require(
        launch is not None and Path(launch).is_file(), "missing external launch receipt"
    )
    root = Path(git_bytes(folder, "rev-parse", "--show-toplevel").decode().strip())
    launch = Path(launch).resolve()
    require(
        launch.is_relative_to(root)
        and output != folder
        and not output.is_relative_to(folder),
        "launch/output placement",
    )
    receipt = parse_json(member(root, "HEAD", str(launch.relative_to(root))))
    require(
        output == safe_path(root, receipt.get("output_path", "")).resolve(),
        "launch receipt must bind exactly one output directory",
    )
    require(
        receipt.get("output_path") == manifest.get("output_path"),
        "immutable manifest output binding",
    )
    commit = receipt["freeze_commit"]
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "invalid freeze commit")
    require(
        receipt["manifest_path"] == str(manifest_path.relative_to(root)),
        "manifest path binding",
    )
    member(root, commit, receipt["manifest_path"], receipt["manifest_sha256"])
    git_bytes(root, "merge-base", "--is-ancestor", commit, "HEAD")
    if "check39_summary" not in manifest["files"]:
        raise StopRepair("absent check39 repair receipt")
    if not safe_path(root, manifest["files"]["check39_summary"]["path"]).is_file():
        raise StopRepair("absent check39 repair receipt")
    require(
        REQUIRED_FILES <= manifest["files"].keys(),
        "missing dependencies/readings/templates/banks",
    )
    require(
        all(
            manifest_path != safe_path(root, x["path"])
            for x in manifest["files"].values()
        ),
        "self-referential manifest",
    )
    contents = {
        k: member(root, commit, d["path"], d["sha256"])
        for k, d in manifest["files"].items()
    }
    for role, actual in RUNTIME_SOURCES.items():
        require(
            role in contents and actual.read_bytes() == contents[role],
            "executed dependency is not the frozen source: " + role,
        )
    verify_evidence(root, manifest, contents)
    for anchor in (PINS["v1_commit"], PINS["v2_commit"], PINS["receipt_commit"]):
        git_bytes(root, "merge-base", "--is-ancestor", anchor, commit)
    require(parse_json(contents["config"]) == CONFIG, "frozen config differs")
    review = parse_json(contents["review"])
    require(
        review.get("status") == "APPROVED"
        and review.get("open_high_critical") == 0
        and review.get("section_sha256") == sha(contents["section"]),
        "registration review outstanding",
    )
    require(
        review.get("dependencies")
        == {k: v["sha256"] for k, v in manifest["files"].items() if k != "review"},
        "registration review dependency binding",
    )
    banks = parse_json(contents["banks"])
    validate_banks(banks, parse_json(contents["development"]))
    tok = tok or (tokenizer_factory or load_tokenizer)(
        root / manifest["files"]["tokenizer"]["path"]
    )
    require(
        parse_json(contents["templates"]) == template_manifest(tok),
        "complete template/rendered tokens mismatch",
    )
    binding = dict(
        manifest_sha256=receipt["manifest_sha256"],
        freeze_commit=commit,
        registration_sha256=sha(contents["section"]),
        hashes={k: v["sha256"] for k, v in manifest["files"].items()},
        template_sha256=RECAP_HASH,
    )
    result = dict(
        root=root,
        manifest=manifest,
        tok=tok,
        banks=banks,
        binding=binding,
        historical_check37="STOP (not pooled; not a v2 veto)",
        spent=0.0,
        projection=0.0,
    )
    if certificates:
        for previous in (
            ("competence", "pilot")
            if stage == "run"
            else ("competence",)
            if stage == "pilot"
            else ()
        ):
            cert, end = validate_certificate(output, previous, result)
            require(
                end["spent_before"] == result["spent"], "nonadditive allocation costs"
            )
            result["spent"] = end["spent_after"]
            if previous == "pilot":
                result["projection"] = cert["projection_seconds"]
                result["worst_cell_seconds"] = cert["worst_cell_seconds"]
        if result["spent"] + result["projection"] >= GPU_CAP:
            raise Incomplete("cost/projection over six GPU-hour cap")
    return result


def competence_gate(rows):
    cells = {}
    for family, directions in FAMILIES.items():
        for direction in (*directions, "default"):
            chosen = [
                r for r in rows if r["family"] == family and r["direction"] == direction
            ]
            require(
                len(chosen) == 64 and all(type(r["success"]) is bool for r in chosen),
                "competence cell count",
            )
            cells[f"{family}/{direction}"] = dict(
                n=64, success=sum(r["success"] for r in chosen)
            )
    require(len(rows) == 768, "competence total")
    return dict(
        status="PASS"
        if all(c["success"] >= 56 for c in cells.values())
        else "INELIGIBLE",
        cells=cells,
    )


def run_episodes(engine, episodes, *, worst_cell_seconds=0.0, load_seconds=0.0):
    new_broken = 0
    for index, ep in enumerate(episodes):
        engine.budget.check(1.25 * worst_cell_seconds * (len(episodes) - index))
        started = engine.budget.elapsed()
        rows = episode(engine, ep)
        both = any(r["flags"]["broken"] for r in rows if r["arm"] == "both")
        restate = any(r["flags"]["broken"] for r in rows if r["arm"] == "text-restate")
        new_broken += both and not restate
        if new_broken >= 3:
            return "FAIL-SAFETY"
        if ep["bank"] == "pilot":
            worst_cell_seconds = max(
                worst_cell_seconds, engine.budget.elapsed() - started
            )
            engine.budget.check(
                1.25
                * (
                    worst_cell_seconds * (len(episodes) - index - 1 + 256)
                    + load_seconds
                )
            )
    return "COMPLETE"


def certificate(stage, rows, summaries, end, binding):
    if stage == "competence":
        value = competence_gate(summaries)
    else:
        require(stage == "pilot" and len(summaries) == 16, "pilot complete cells")
        cells = {}
        endpoints = []
        for summary in summaries:
            last = max(
                r["cost"]["cumulative_seconds"]
                for r in rows
                if r["episode"] == summary["id"]
            )
            endpoints.append((last, summary["id"]))
        previous = end["spent_before"] + end["load_seconds"]
        for last, identity in sorted(endpoints):
            require(last >= previous, "pilot allocation chronology")
            cells[identity] = last - previous
            previous = last
        # Include the final durable write/unload, as well as rendering and
        # publication gaps between requests, in the measured allocation cost.
        require(end["spent_after"] >= previous, "pilot terminal allocation")
        cells[max(endpoints)[1]] += end["spent_after"] - previous
        worst = max(cells.values())
        # Include the next load and all 256 final episodes, with 25% reserve.
        value = dict(
            status="PASS",
            cells=cells,
            worst_cell_seconds=worst,
            projection_seconds=1.25 * (256 * worst + end["load_seconds"]),
            timing_only=True,
        )
    return dict(
        **value,
        binding=binding,
        records_hash=digest(
            sorted(rows, key=lambda r: (r["episode"], r["arm"], r["checkpoint"]))
        ),
        records_count=len(rows),
        spent_after=end["spent_after"],
    )


def validate_certificate(output, stage, pre):
    folder = Path(output) / stage
    require(
        (folder / "certificate.json").is_file() and (folder / "end.json").is_file(),
        "missing competence/pilot certificate",
    )
    end = parse_json((folder / "end.json").read_text())
    cert = parse_json((folder / "certificate.json").read_text())
    require(
        end["status"] in ("COMPLETE", "INELIGIBLE")
        and end["binding"] == pre["binding"]
        and end["spent_after"] >= end["spent_before"] >= 0,
        "incomplete/bad stage certificate",
    )
    rows = RecordStore(folder / "records").rows()
    start = parse_json((folder / "start.json").read_text())
    require(
        start
        == dict(stage=stage, binding=pre["binding"], spent_before=end["spent_before"]),
        "stage start receipt",
    )
    summaries = validate_records(
        rows, pre["banks"][stage], pre["tok"], pre["binding"], complete=True
    )
    require(
        end["record_count"] == len(rows)
        and end["records_hash"]
        == digest(
            sorted(rows, key=lambda r: (r["episode"], r["arm"], r["checkpoint"]))
        ),
        "stage receipt raw records",
    )
    require(
        end["spent_after"] - end["spent_before"] + 1e-6
        >= end["load_seconds"] + sum(r["cost"]["allocation_seconds"] for r in rows),
        "forged allocation cost",
    )
    computed = certificate(stage, rows, summaries, end, pre["binding"])
    require(
        cert == computed,
        "forged or failing competence/pilot certificate",
    )
    if computed["status"] == "INELIGIBLE":
        raise Ineligible("competence miss; no family dropping or retest")
    require(
        end["status"] == "COMPLETE" and computed["status"] == "PASS",
        "stage eligibility",
    )
    return computed, end


def execute_stage(
    folder,
    launch,
    output,
    stage,
    *,
    backend_factory=None,
    tokenizer_factory=None,
    clock=time.monotonic,
):
    require(stage in ("competence", "pilot", "run"), "stage")
    pre = preflight(folder, launch, stage, output, tokenizer_factory=tokenizer_factory)
    destination = Path(output) / stage
    require(not destination.exists(), "refusing output overwrite/retry")
    budget = Budget(clock, spent=pre["spent"])
    budget.check(pre["projection"])
    destination.mkdir(parents=True)
    atomic_json(
        destination / "start.json",
        dict(stage=stage, binding=pre["binding"], spent_before=pre["spent"]),
    )
    store = RecordStore(destination / "records")
    status, reason, load_seconds = "INCOMPLETE", "interrupted", 0.0
    backend = None
    engine = None
    loading_start = clock()
    try:
        budget.check(pre["projection"])
        config = {
            "config_path": pre["root"]
            / pre["manifest"]["files"]["model_config"]["path"],
            "weights_path": pre["root"] / pre["manifest"]["files"]["model"]["path"],
        }
        backend = (backend_factory or load_backend)(pre["tok"], config)
        load_seconds = clock() - loading_start
        budget.check()
        engine = Engine(pre["tok"], backend, store, budget, pre["binding"])
        if stage == "competence":
            for ep in pre["banks"][stage]:
                budget.check()
                h = competence_history(pre["tok"], ep)
                h.request(ep, "SET", cue=live_rules(ep, "SET") + "\n")
                engine.answer(h, ep, "shared", "SET")
            status = "COMPLETE"
        else:
            status = run_episodes(
                engine,
                pre["banks"]["final" if stage == "run" else "pilot"],
                worst_cell_seconds=pre.get("worst_cell_seconds", 0.0),
                load_seconds=load_seconds,
            )
        reason = (
            "finished scheduling"
            if status == "COMPLETE"
            else "third irrecoverable both-only broken episode"
        )
        budget.check()
    except (KeyboardInterrupt, Incomplete, MemoryError) as exc:
        status, reason = "INCOMPLETE", str(exc) or "interrupted"
    except Invalid as exc:
        status, reason = exc.status, str(exc)
    except Exception as exc:
        status, reason = (
            "INCOMPLETE",
            f"resource/backend interruption: {type(exc).__name__}: {exc}",
        )
    finally:
        if not load_seconds:
            load_seconds = clock() - loading_start
        engine = None
        if backend is not None and hasattr(backend, "close"):
            backend.close()
        backend = None
        spent_after = budget.elapsed()
        try:
            rows = store.rows()
        except (Invalid, ValueError, OSError) as exc:
            rows = []
            status, reason = "INVALID", f"partial/corrupt records retained: {exc}"
        end = dict(
            status=status,
            reason=reason,
            binding=pre["binding"],
            spent_before=pre["spent"],
            spent_after=spent_after,
            load_seconds=load_seconds,
            record_count=len(rows),
            records_hash=digest(
                sorted(rows, key=lambda r: (r["episode"], r["arm"], r["checkpoint"]))
            ),
        )
        # Validation/aggregation is CPU and runs after allocation accounting ends.
        if status == "COMPLETE":
            try:
                summaries = validate_records(
                    rows,
                    pre["banks"]["final" if stage == "run" else stage],
                    pre["tok"],
                    pre["binding"],
                    complete=True,
                )
                if stage != "run":
                    cert = certificate(stage, rows, summaries, end, pre["binding"])
                    atomic_json(destination / "certificate.json", cert)
                    if cert["status"] != "PASS":
                        end["status"] = "INELIGIBLE"
            except Invalid as exc:
                end.update(status="INVALID", reason=str(exc))
        atomic_json(destination / "end.json", end)
    return end


def analyze(folder, launch, output, *, tok=None, tokenizer_factory=None):
    pre = preflight(
        folder, launch, "run", output, tok=tok, tokenizer_factory=tokenizer_factory
    )
    directory = Path(output) / "run"
    rows = RecordStore(directory / "records").rows()
    path = directory / "end.json"
    end = parse_json(path.read_text()) if path.is_file() else {"status": "INCOMPLETE"}
    terminal = end["status"]
    require(
        terminal in ("COMPLETE", "INCOMPLETE", "INVALID", "FAIL-SAFETY"),
        "unknown run status",
    )
    summaries = validate_records(
        rows,
        pre["banks"]["final"],
        pre["tok"],
        pre["binding"],
        complete=terminal == "COMPLETE",
    )
    if path.is_file():
        require(
            end["binding"] == pre["binding"]
            and end["records_hash"]
            == digest(
                sorted(rows, key=lambda r: (r["episode"], r["arm"], r["checkpoint"]))
            )
            and end["record_count"] == len(rows),
            "run receipt/records mismatch",
        )
        require(
            end["spent_before"] == pre["spent"] and end["spent_after"] >= pre["spent"],
            "nonadditive final cost",
        )
        if end["spent_after"] >= GPU_CAP:
            terminal = "INCOMPLETE" if terminal != "INVALID" else terminal
    report = decisions(summaries, terminal)
    report["binding"] = pre["binding"]
    report["allocation_seconds"] = end.get("spent_after")
    report["historical_check37"] = pre["historical_check37"]
    report["checkpoint_counts"] = {}
    for arm in ARMS:
        report["checkpoint_counts"][arm] = {}
        for step in CHECKPOINTS:
            rs = [
                r
                for r in rows
                if r["arm"] == arm and r["checkpoint"] == step and r["complete"]
            ]
            report["checkpoint_counts"][arm][step] = dict(
                n=len(rs),
                fixed_n=256,
                success=sum(r["flags"]["success"] for r in rs),
                flags={
                    k: sum(r["flags"][k] for r in rs)
                    for k in (
                        "empty",
                        "placeholder",
                        "schema_invalid",
                        "truncated",
                        "repetitive",
                        "broken",
                    )
                },
            )
    report["directional_impositions"] = {}
    report["checkpoint_strata"] = {}
    for field in ("family", "direction", "delay", "both_correct"):
        cells = {}
        for r in rows:
            if r["arm"] not in ARMS or not r["complete"]:
                continue
            key = f"{r[field]}/{r['arm']}/{r['checkpoint']}"
            cell = cells.setdefault(
                key, dict(n=0, success=0, broken=0, constraint_failure=0)
            )
            cell["n"] += 1
            cell["success"] += r["flags"]["success"]
            cell["broken"] += r["flags"]["broken"]
            cell["constraint_failure"] += not r["flags"]["constraint"]
        report["checkpoint_strata"][field] = cells
    for family, directions in FAMILIES.items():
        for direction in directions:
            for arm in ARMS:
                for step in ("CLEAR", "NEUTRAL2"):
                    rs = [
                        r
                        for r in rows
                        if r["family"] == family
                        and r["direction"] == direction
                        and r["arm"] == arm
                        and r["checkpoint"] == step
                        and r["complete"]
                    ]
                    report["directional_impositions"][
                        f"{family}/{direction}/{arm}/{step}"
                    ] = dict(
                        n=len(rs),
                        fixed_n=32,
                        impositions={
                            d: sum(r["flags"]["imposition"][d] for r in rs)
                            for d in (*directions, "default")
                        },
                        placeholder=sum(r["flags"]["placeholder"] for r in rs),
                    )
    return report

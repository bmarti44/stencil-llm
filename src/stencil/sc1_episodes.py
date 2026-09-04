"""SC1 structured-source compiler, finite executor and production checker.

The grammar contains generic primitives and irrelevant filler, never a scenario
bank. Production stories and independent review evidence must be supplied by
isolated commissioning sessions; this module cannot attest to their semantics.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from stencil.sc1 import (
    MAX_PREFIX,
    MAX_QUERY,
    canonical,
    digest,
    file_hash,
    render_episode,
    token_ids,
)

COMPILER_VERSION = "SC1-source-v2.1"
AUTHORS = ("kimi-k3", "fable", "gpt-6-astra", "Opus")
STYLES = ("editing", "tool-work")
ORIGINS = ("user", "tool")
SCOPES = ("continuing", "overridden", "cancelled-or-completed", "switched")
STREAMS = (
    "author",
    "style",
    "origin",
    "age",
    "scope",
    "authoring",
    "literals",
    "filler",
    "order",
)
FACTORS = STREAMS[:5]
ATTACKS = (
    "old-ID substitution",
    "cancelled action executed",
    "wrong entity",
    "wrong scope",
    "empty output",
    "collateral edit",
)
SUBSTITUTES = (
    "missing required field/object",
    "wrong exact value",
    "forbidden extra output",
    "incomplete artifact/call",
)
# Disclosed incidental prose; none can introduce an instruction or decisive fact.
FILLER = (
    "A pale reflection crossed the empty courtyard before the clouds returned.",
    "The afternoon notes describe quiet footsteps beside an open window.",
    "Loose leaves settled near a wooden bench while distant bells sounded.",
    "A small breeze moved the curtain, then the room became still again.",
    "The observer sketched a shaded doorway and an uneven line of stones.",
    "Rain left faint circles on the walkway outside the unused meeting room.",
    "The notebook also mentions soft light falling across an ordinary wall.",
    "A bird rested briefly on the fence before disappearing behind the roof.",
)
FILLER_VERSION = "SC1-incidental-v1"
REQUIRED_FIELDS = set(
    """schema_version id source_id pool index assignments seeds attempt provenance
    domain task scenario_gist entities source_graph instruction_trajectory
    decisive_facts
    distractors filler_manifest task_spec initial_state state_trace obligations
    protected_set expected_artifact expected_state reference checker mutation_plan
    mutations system tools turns final_request layout_audit source_fingerprint
    distinctness_review validation""".split()
)
PREDICATES = {
    "state_equals",
    "protected_unchanged",
    "json_equals",
    "required_lines",
    "forbidden_substrings",
    "max_lines",
}
SCHEMA = {
    "version": COMPILER_VERSION,
    "episode_fields": sorted(REQUIRED_FIELDS),
    "source_fields": [
        "pool",
        "index",
        "id",
        "source_id",
        "provenance",
        "domain",
        "task",
        "scenario_gist",
        "entities",
        "source_graph",
        "instruction_trajectory",
        "decisive_facts",
        "distractors",
        "task_spec",
        "initial_state",
        "state_trace",
        "obligations",
        "protected_set",
        "work",
        "system",
        "tools",
        "turns",
        "final_request",
        "filler_turn",
        "distinctness_review",
        "review",
    ],
    "task_kinds": ["json_patch", "text", "tool"],
    "predicates": sorted(PREDICATES),
    "limits": {"prefix": MAX_PREFIX, "query": MAX_QUERY, "reference": 256, "lines": 40},
    "patch": (
        "array of add/replace/remove objects with JSON-pointer path "
        "and value except remove"
    ),
    "call": "one bare object with name and arguments; create/update/delete/get/list",
    "source_literals": "${NAME} expands from a typed seed-derived literal spec",
    "provider_seed_mapping": (
        "unsigned first 32 SHA-256 bits; recorded even without provider seed support"
    ),
}
SCHEMA["structures"] = {
    "entities": "array of {id, name, type, structural_role}; structural roles unique",
    "source_graph": (
        "authored setting, task, ordered events/dependencies, unordered relations; "
        "refer to entities by ID; type exact literals as value/literal"
    ),
    "evidence": (
        "decisive_facts and instruction_trajectory are arrays with id, turn, "
        "evidence_text (unique verbatim substring), necessary boolean; "
        "trajectory also has authority=user, kind and assigned scope"
    ),
    "task_spec": (
        "kind=json_patch/text/tool; fields maps generic field names to "
        "string/number/integer/boolean/null; permitted_paths lists authorized JSON "
        "pointers; operations is a subset of create/update/delete/get/list"
    ),
    "work": (
        "json_patch: {patch: operation array}; text: {text: full artifact}; "
        "tool: {name: operation, arguments: typed argument object}"
    ),
    "state_trace": (
        "{start: full state before scripted events, events: ordered array of "
        "{turn, call, return, public_text}}; replay must yield initial_state"
    ),
    "predicates": (
        "obligations/protected_set: arrays of {id, kind, evidence_ids}; json_equals/"
        "state_equals use value and optional path; protected_unchanged uses path "
        "and optional value/absent; required_lines/forbidden_substrings use values; "
        "max_lines uses integer value"
    ),
    "literal_specs": (
        "map of placeholder name to {type: identifier/name/string/integer, optional "
        "length/range}; ${NAME} expands in keys/values/text; exact placeholders "
        "preserve numeric type; answer_literals lists all indispensable literals"
    ),
    "expansion": (
        "author 12–24 turns {role,text}, all causal events already in assigned age "
        "region; filler_turn selects a non-evidence turn for irrelevant expansion; "
        "compiler never moves or invents decisive events"
    ),
    "attacks": (
        "map applicable named slots to {output: structured value or text, "
        "obligation_ids}; inapplicable maps other slots to narrative reasons; "
        "compiler generates prioritized substitutes and rejects inadequate coverage"
    ),
    "review": (
        "reviewer, narrative_obligations, semantic_leakage, generic_safe, "
        "recency_only, "
        "coverage_probes [{output or result, obligation_ids}]; production sign-offs "
        "are independent, never generated by the compiler"
    ),
}


def tool_schemas(spec):
    """Original finite API families, containing generic types and no oracle values."""
    fields = {key: {"type": value} for key, value in spec["fields"].items()}
    record = {"type": "object", "properties": fields, "additionalProperties": False}
    parameters = {
        "create": {
            "id": {"type": "string"},
            "record": {**record, "required": list(fields)},
        },
        "update": {"id": {"type": "string"}, "changes": {**record, "minProperties": 1}},
        "delete": {"id": {"type": "string"}},
        "get": {"id": {"type": "string"}},
        "list": {},
    }
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": "One isolated in-memory record-store operation.",
                "parameters": {
                    "type": "object",
                    "properties": parameters[name],
                    "required": list(parameters[name]),
                    "additionalProperties": False,
                },
            },
        }
        for name in spec["operations"]
    ]


def stream_digest(pool, index, stream, attempt=0):
    if (
        pool not in {"smoke", "setup", "final"}
        or type(index) is not int
        or type(attempt) is not int
        or index < 0
        or stream not in STREAMS
        or not 0 <= attempt < 3
    ):
        raise ValueError("invalid commissioning stream")
    if stream in FACTORS or stream == "order":
        attempt = 0
    return hashlib.sha256(
        f"SC1-v2|20260904|{pool}|{index}|{stream}|{attempt}".encode()
    ).hexdigest()


def commission_slot(pool, index, attempt=0):
    seeds = {s: stream_digest(pool, index, s, attempt) for s in STREAMS}
    first = {s: int(h[:2], 16) for s, h in seeds.items()}
    assignments = {
        "author": AUTHORS[first["author"] >> 6],
        "style": STYLES[first["style"] >> 7],
        "origin": ORIGINS[first["origin"] >> 7],
        "age": "recent" if first["age"] >> 6 == 3 else "old",
        "scope": SCOPES[first["scope"] >> 6],
    }
    return {
        "pool": pool,
        "index": index,
        "assignments": assignments,
        "seeds": seeds,
        "attempt": attempt,
        "master_seed": 20260904,
        "provider_seed": int(seeds["authoring"][:8], 16),
        "order": ["clf", "rule"] if first["order"] >> 7 == 0 else ["rule", "clf"],
        "setup_order": ["full", "evicted"]
        if first["order"] >> 7 == 0
        else ["evicted", "full"],
    }


def realized_counts(episodes):
    report = {}
    for pool in sorted({e["pool"] for e in episodes}):
        rows = [e for e in episodes if e["pool"] == pool]
        report[pool] = {
            factor: dict(Counter(e["assignments"][factor] for e in rows))
            for factor in FACTORS
        }
        report[pool]["domain"] = dict(Counter(e["domain"] for e in rows))
        report[pool]["crossed"] = dict(
            Counter("|".join(e["assignments"][f] for f in FACTORS) for e in rows)
        )
        report[pool]["n"] = len(rows)
    return report


def normalize_text(text):
    lines = [
        line.rstrip(" \t")
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    result = []
    for line in lines:
        if line or not result or result[-1]:
            result.append(line)
    return "\n".join(result)


def json_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            json_equal(x, y) for x, y in zip(a, b, strict=True)
        )
    return a == b


def parse_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate key")
            out[key] = value
        return out

    def constant(value):
        raise ValueError("non-finite number: " + value)

    value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    # Reject overflowing finite JSON spellings such as 1e999 too.
    canonical(value)
    return value


def path_parts(path):
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or re.search(r"~(?![01])", path)
    ):
        raise ValueError("invalid JSON pointer")
    return [p.replace("~1", "/").replace("~0", "~") for p in path[1:].split("/")]


ABSENT = object()


def at_path(value, path):
    current = value
    for part in path_parts(path):
        if not isinstance(current, dict) or part not in current:
            return ABSENT
        current = current[part]
    return current


def apply_patch(base, patch, *, strict=True):
    if not isinstance(patch, list) or not patch or len(patch) > 40:
        raise ValueError("expected nonempty bounded JSON patch")
    state = copy.deepcopy(base)
    for operation in patch:
        if not isinstance(operation, dict):
            raise ValueError("patch operation must be an object")
        op = operation.get("op")
        expected = {"op", "path"} if op == "remove" else {"op", "path", "value"}
        if (
            op not in {"add", "replace", "remove"}
            or (strict and set(operation) != expected)
            or not expected <= set(operation)
        ):
            raise ValueError("unknown patch fields/operation")
        parts = path_parts(operation["path"])
        parent = state
        for part in parts[:-1]:
            if not isinstance(parent, dict) or part not in parent:
                raise ValueError("missing patch parent")
            parent = parent[part]
        key = parts[-1]
        if not isinstance(parent, dict) or (
            op in {"replace", "remove"} and key not in parent
        ):
            raise ValueError("missing patch target")
        if op == "remove":
            del parent[key]
        else:
            parent[key] = copy.deepcopy(operation["value"])
    return state


def valid_type(value, name):
    return {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(name, False)


def execute_call(initial, call, spec):
    """Validate completely before mutating an isolated copy of the finite store."""
    if not isinstance(call, dict) or set(call) != {"name", "arguments"}:
        raise ValueError("exactly one bare function call required")
    name, args = call["name"], call["arguments"]
    if (
        not isinstance(name, str)
        or name not in spec["operations"]
        or not isinstance(args, dict)
    ):
        raise ValueError("unpermitted function/type")
    keys = {
        "create": {"id", "record"},
        "update": {"id", "changes"},
        "delete": {"id"},
        "get": {"id"},
        "list": set(),
    }
    if name not in keys or set(args) != keys[name]:
        raise ValueError("unknown/missing call arguments")
    if name != "list" and (not isinstance(args["id"], str) or not args["id"]):
        raise ValueError("id must be a nonempty string")
    if name in {"create", "update"}:
        payload = args["record" if name == "create" else "changes"]
        if (
            not isinstance(payload, dict)
            or not payload
            or set(payload) - spec["fields"].keys()
        ):
            raise ValueError("unknown/empty record fields")
        if name == "create" and set(payload) != set(spec["fields"]):
            raise ValueError("incomplete created record")
        if any(not valid_type(v, spec["fields"][k]) for k, v in payload.items()):
            raise ValueError("record field type mismatch")
    state = copy.deepcopy(initial)
    if name == "create":
        if args["id"] in state:
            raise ValueError("record already exists")
        state[args["id"]] = copy.deepcopy(args["record"])
    elif name in {"update", "delete", "get"}:
        if args["id"] not in state:
            raise ValueError("missing record")
        if name == "update":
            state[args["id"]].update(copy.deepcopy(args["changes"]))
        elif name == "delete":
            del state[args["id"]]
    result = (
        copy.deepcopy(state[args["id"]])
        if name == "get"
        else sorted(state)
        if name == "list"
        else {"ok": True}
    )
    return state, result


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        rows = []
        for key in sorted(a.keys() | b.keys()):
            p = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in a or key not in b:
                rows.append(
                    {
                        "path": p,
                        "before": a.get(key),
                        "after": b.get(key),
                        "before_exists": key in a,
                        "after_exists": key in b,
                    }
                )
            else:
                rows.extend(differences(a[key], b[key], p))
        return rows
    return [] if json_equal(a, b) else [{"path": path, "before": a, "after": b}]


def predicate_pass(predicate, result, initial):
    kind = predicate["kind"]
    if kind in {"json_equals", "state_equals"}:
        value = at_path(result, predicate["path"]) if "path" in predicate else result
        return value is not ABSENT and json_equal(value, predicate["value"])
    if kind == "protected_unchanged":
        actual = at_path(result, predicate["path"])
        expected = at_path(initial, predicate["path"])
        if predicate.get("absent"):
            return actual is ABSENT
        if "value" in predicate:
            expected = predicate["value"]
        return (
            actual is ABSENT
            and expected is ABSENT
            or actual is not ABSENT
            and expected is not ABSENT
            and json_equal(actual, expected)
        )
    if kind == "required_lines":
        return isinstance(result, str) and all(
            normalize_text(line) in normalize_text(result).split("\n")
            for line in predicate["values"]
        )
    if kind == "forbidden_substrings":
        text = result if isinstance(result, str) else canonical(result)
        return all(s not in text for s in predicate["values"])
    if kind == "max_lines":
        return (
            isinstance(result, str)
            and len(normalize_text(result).split("\n")) <= predicate["value"]
        )
    raise ValueError("unknown predicate: " + kind)


def check_result(episode, result):
    """One final-state/artifact consumer, also used by unreachable-state probes."""
    initial = episode["initial_state"]
    expected = (
        episode["expected_state"]
        if episode["task_spec"]["kind"] == "tool"
        else episode["expected_artifact"]
    )
    if isinstance(result, str) and isinstance(expected, str):
        result, expected = normalize_text(result), normalize_text(expected)
    failures = [
        p["id"] for p in episode["checker"] if not predicate_pass(p, result, initial)
    ]
    protected = [
        p["id"]
        for p in episode["protected_set"]
        if not predicate_pass(p, result, initial)
    ]
    delta = differences(initial, result)
    permitted = episode["task_spec"]["permitted_paths"]
    outside = [
        d
        for d in delta
        if not any(d["path"] == p or d["path"].startswith(p + "/") for p in permitted)
    ]
    # Whole-text replacements remain bounded by protected content predicates.
    if isinstance(result, str):
        outside = []
    if not json_equal(result, expected):
        failures.append("complete_result")
    if json_equal(result, initial):
        failures.append("affirmative_work")
    return {
        "success": not failures and not protected and not outside,
        "causes": sorted(
            set(failures + protected + (["unauthorized_change"] if outside else []))
        ),
        "failed_obligations": failures,
        "failed_invariants": protected,
        "corruption": bool(protected or outside),
        "state_diff": delta,
        "expected_diff": differences(expected, result),
        "unauthorized_changes": outside,
    }


def run_checker(episode, output):
    """Production parser/executor/checker; refs and mutations use this same call."""
    spec = episode["task_spec"]
    parsed = result = action_result = None
    schema_valid = True
    causes = []
    try:
        if spec["kind"] == "text":
            if not isinstance(output, str) or not output.strip():
                raise ValueError("empty text")
            parsed = result = normalize_text(output)
            if len(result.split("\n")) > 40:
                raise ValueError("text exceeds 40 lines")
        else:
            parsed = parse_json(output)
            if spec["kind"] == "tool":
                result, action_result = execute_call(
                    episode["initial_state"], parsed, spec
                )
            elif spec["kind"] == "json_patch":
                result = apply_patch(episode["initial_state"], parsed)
                if len(output.splitlines()) > 40:
                    raise ValueError("patch exceeds 40 lines")
                if set(result) != set(spec["fields"]) or any(
                    not valid_type(result[k], v) for k, v in spec["fields"].items()
                ):
                    raise ValueError("artifact schema mismatch")
            else:
                raise ValueError("unknown output kind")
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        schema_valid = False
        causes.append("parser/schema: " + str(exc))
        # Parsed editing content must still be checked for collateral edits.
        if spec["kind"] == "json_patch" and result is None and parsed is not None:
            try:
                result = apply_patch(episode["initial_state"], parsed, strict=False)
            except (ValueError, TypeError, KeyError):
                pass
        if spec["kind"] == "tool":
            result = None  # No state is invented for a rejected operation.
    verdict = (
        check_result(episode, result)
        if result is not None
        else {
            "success": False,
            "causes": [],
            "failed_obligations": [],
            "failed_invariants": [],
            "corruption": False,
            "state_diff": [],
            "expected_diff": [],
            "unauthorized_changes": [],
        }
    )
    verdict.update(
        schema_valid=schema_valid,
        success=schema_valid and verdict["success"],
        causes=causes + verdict["causes"],
        result=result,
        action_result=action_result,
    )
    return verdict


def _literal_expand(source, slot):
    literals = {}
    for name, spec in sorted(source.get("literal_specs", {}).items()):
        h = hashlib.sha256(
            (slot["seeds"]["literals"] + "|" + name).encode()
        ).hexdigest()
        kind = spec["type"]
        if kind == "identifier":
            value = h[: spec.get("length", 8)]
            if not 6 <= len(value) <= 12:
                raise ValueError("identifier length outside contract")
        elif kind == "name":
            value = "N" + h[:7]
        elif kind == "integer":
            value = int(h[:8], 16) % spec.get("range", 10000)
        elif kind == "string":
            value = h[: spec.get("length", 10)]
        else:
            raise ValueError("unknown literal type")
        literals[name] = value

    def expand(value):
        if isinstance(value, str):
            if (
                value.startswith("${")
                and value.endswith("}")
                and value.count("${") == 1
            ):
                return literals[value[2:-1]]
            return re.sub(r"\$\{([^}]+)\}", lambda m: str(literals[m[1]]), value)
        if isinstance(value, list):
            return [expand(x) for x in value]
        if isinstance(value, dict):
            return {expand(k): expand(v) for k, v in value.items()}
        return value

    return expand(copy.deepcopy(source)), literals


def sibling_fingerprint(source):
    """Canonical causal graph; alpha rename by declared structural role.

    Events/dependencies retain order. Explicit unordered relation/entity sets sort.
    Equal literal values share a typed placeholder, preserving equality relations.
    Independent semantic review is mandatory even when hashes differ.
    """
    entities = sorted(
        source["entities"], key=lambda e: (e["structural_role"], e["type"])
    )
    keys = [(e["structural_role"], e["type"]) for e in entities]
    if len(set(keys)) != len(keys):
        raise ValueError("entities need unique structural roles")
    replacements = {}
    for i, e in enumerate(entities):
        for key in ("id", "name"):
            if key in e:
                replacements[e[key]] = f"@entity:{e['type']}:{i}"
    values = {}

    def walk(value, key=""):
        if isinstance(value, str):
            if value in replacements:
                return replacements[value]
            if key in {
                "literal",
                "value",
                "active_value",
                "superseded_value",
                "cancelled_value",
                "name",
                "identifier",
            } or value.startswith("${"):
                typed = (type(value).__name__, value)
                values.setdefault(typed, f"@literal:string:{len(values)}")
                return values[typed]
            return re.sub(r"\$\{[^}]+\}", "@literal", value)
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and key in {"literal", "value"}
        ):
            typed = ("number", value)
            values.setdefault(typed, f"@literal:number:{len(values)}")
            return values[typed]
        if isinstance(value, list):
            rows = [walk(v, key) for v in value]
            return (
                sorted(rows, key=canonical)
                if key in {"entities", "relations", "unordered"}
                else rows
            )
        if isinstance(value, dict):
            return {
                k: walk(v, k)
                for k, v in sorted(value.items())
                if k not in {"text", "char_span", "token_span", "turn", "evidence_text"}
            }
        return value

    return digest(
        walk(
            {
                "graph": source["source_graph"],
                "trajectory": source["instruction_trajectory"],
                "entities": [
                    {"type": e["type"], "structural_role": e["structural_role"]}
                    for e in entities
                ],
            }
        )
    )


def source_spec_hash(source):
    """Bind source content without circular hashes between review records."""
    return digest(
        {
            k: v
            for k, v in source.items()
            if k not in {"review", "distinctness_review", "provenance"}
        }
    )


def _wrong(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value + "x"
    if isinstance(value, (int, float)):
        return value + 1
    if value is None:
        return "wrong"
    return {}


def generate_mutations(ep, authored):
    """Generate obligation-linked negatives; no scope event is invented.

    Named semantics require a source-declared attack witness. Inapplicable slots
    consume the first unused applicable substitute, in the registered order.
    """
    spec, reference = ep["task_spec"], ep["reference"]
    obligations = [p["id"] for p in ep["obligations"]]
    protected = [p["id"] for p in ep["protected_set"]]
    if not obligations or not protected:
        raise ValueError("nonempty obligations/protected set required")
    substitutes = []
    if spec["kind"] == "json_patch":
        base = parse_json(reference)
        missing = copy.deepcopy(base[:-1])
        wrong = copy.deepcopy(base)
        if "value" in wrong[0]:
            wrong[0]["value"] = _wrong(wrong[0]["value"])
        else:
            wrong[0]["path"] += "x"
        extra = [
            *copy.deepcopy(base),
            {"op": "add", "path": "/extra", "value": "unexpected"},
        ]
        incomplete = copy.deepcopy(base)
        del incomplete[0]["path"]
        substitutes = [canonical(x) for x in (missing, wrong, extra, incomplete)]
    elif spec["kind"] == "tool":
        base = parse_json(reference)
        missing = copy.deepcopy(base)
        missing["arguments"].pop(next(iter(missing["arguments"])), None)
        wrong = copy.deepcopy(base)
        changes = wrong["arguments"].get("changes", wrong["arguments"].get("record"))
        if changes:
            key = next(iter(changes))
            changes[key] = _wrong(changes[key])
        else:
            wrong["arguments"]["id"] += "x"
        extra = {**base, "extra": "unexpected"}
        incomplete = copy.deepcopy(base)
        incomplete.pop("name")
        substitutes = [canonical(x) for x in (missing, wrong, extra, incomplete)]
    else:
        lines = reference.split("\n")
        substitutes = [
            "\n".join(lines[:-1]),
            _wrong(reference),
            reference + "\nextra",
            reference[:-1],
        ]
    named = authored.get("attacks", {})
    mutations, plan, used, used_substitutes = [], [], set(), set()
    for slot in ATTACKS:
        reason, substitute = None, None
        if slot == "empty output":
            output, ids = "", obligations
        elif slot in named:
            witness = named[slot]
            output = (
                witness["output"]
                if isinstance(witness["output"], str)
                else canonical(witness["output"])
            )
            ids = witness["obligation_ids"]
        else:
            reason = authored.get("inapplicable", {}).get(slot)
            if not reason:
                raise ValueError("predeclare non-applicability: " + slot)
            output = None
            for label, proposed in zip(SUBSTITUTES, substitutes, strict=True):
                if (
                    label not in used_substitutes
                    and proposed not in used
                    and proposed != reference
                    and not run_checker(ep, proposed)["success"]
                ):
                    output, substitute = proposed, label
                    used_substitutes.add(label)
                    break
            if output is None:
                raise ValueError(
                    "six distinct applicable negatives cannot be constructed"
                )
            ids = obligations
        if (
            output in used
            or output == reference
            or not ids
            or not set(ids) <= set(obligations + protected)
        ):
            raise ValueError("duplicate/unlinked mutation")
        used.add(output)
        plan.append(
            {
                "slot": slot,
                "applicable": reason is None,
                "reason": reason,
                "substitute": substitute,
                "obligation_ids": ids,
            }
        )
        mutations.append(
            {
                "slot": slot,
                "output": output,
                "obligation_ids": ids,
                "substitute": substitute,
            }
        )
    return plan, mutations


def expand_source(source, tokenizer):
    for key in SCHEMA["source_fields"]:
        if key not in source:
            raise ValueError("source missing " + key)
    slot = commission_slot(source["pool"], source["index"], source.get("attempt", 0))
    material, literals = _literal_expand(source, slot)
    kind = material["task_spec"]["kind"]
    if kind not in SCHEMA["task_kinds"]:
        raise ValueError("unknown task kind")
    ep = {k: copy.deepcopy(material[k]) for k in REQUIRED_FIELDS if k in material}
    ep.update(
        schema_version="sc1-v2",
        assignments=slot["assignments"],
        seeds=slot["seeds"],
        attempt=slot["attempt"],
    )
    ep["task_spec"]["permitted_paths"] = list(material["task_spec"]["permitted_paths"])
    work = material["work"]
    if kind == "tool":
        generated_tools = tool_schemas(ep["task_spec"])
        if ep["tools"] is not None and ep["tools"] != generated_tools:
            raise ValueError("tool schemas must be the frozen generic API")
        ep["tools"] = generated_tools
        ref = {"name": work["name"], "arguments": work["arguments"]}
        expected, _ = execute_call(ep["initial_state"], ref, ep["task_spec"])
        ep.update(
            expected_state=expected, expected_artifact=None, reference=canonical(ref)
        )
    elif kind == "json_patch":
        expected = apply_patch(ep["initial_state"], work["patch"])
        ep.update(
            expected_artifact=expected,
            expected_state=None,
            reference=canonical(work["patch"]),
        )
    else:
        expected = normalize_text(work["text"])
        ep.update(expected_artifact=expected, expected_state=None, reference=expected)
    ep["checker"] = copy.deepcopy(ep["obligations"])
    if any(p["kind"] not in PREDICATES for p in ep["checker"] + ep["protected_set"]):
        raise ValueError("unknown declarative predicate")
    ep["checker"].append(
        {
            "id": "complete_result",
            "kind": "state_equals" if kind == "tool" else "json_equals",
            "value": expected,
        }
    )
    # Filler may expand only a designated non-evidence message. It never moves events.
    fill_at = material["filler_turn"]
    evidence_turns = {
        p["turn"]
        for p in ep["decisive_facts"] + ep["instruction_trajectory"]
        if p.get("necessary", True)
    }
    if fill_at in evidence_turns or not 0 <= fill_at < len(ep["turns"]):
        raise ValueError("filler cannot replace decisive evidence")
    base_text = ep["turns"][fill_at]["text"]
    filler_ids = []
    layout = render_episode(ep, tokenizer)
    # Fixed target, identical for every source; only irrelevant expansion varies.
    while layout["H"] - layout["P"] < 4608:
        for _ in range(8):
            n = len(filler_ids)
            h = hashlib.sha256(
                (slot["seeds"]["filler"] + "|" + str(n)).encode()
            ).digest()
            filler_ids.append(int.from_bytes(h[:4], "big") % len(FILLER))
        ep["turns"][fill_at]["text"] = (
            base_text + "\n" + " ".join(FILLER[i] for i in filler_ids)
        )
        layout = render_episode(ep, tokenizer)
        if len(filler_ids) > 2048:
            raise ValueError("filler expansion failed to reach length")
    ep["filler_manifest"] = {
        "version": FILLER_VERSION,
        "seed": slot["seeds"]["filler"],
        "turn": fill_at,
        "ids": filler_ids,
        "base_text": base_text,
        "literal_values": literals,
        "literal_types": {
            k: v["type"] for k, v in source.get("literal_specs", {}).items()
        },
    }
    intervals = []
    for group in ("decisive_facts", "instruction_trajectory"):
        for evidence in ep[group]:
            index = evidence["turn"]
            text = ep["turns"][index]["text"]
            if "evidence_text" in evidence:
                if text.count(evidence["evidence_text"]) != 1:
                    raise ValueError(
                        "evidence quote must identify exactly one source span"
                    )
                start = text.index(evidence["evidence_text"])
                evidence["char_span"] = [start, start + len(evidence["evidence_text"])]
            a, b = evidence["char_span"]
            if not 0 <= a < b <= len(text):
                raise ValueError("invalid evidence pointer")
            location = layout["locations"][index]
            from stencil.bfcl import _token_span

            encoding = type("Offsets", (), {"offsets": layout["offsets"]})()
            span = _token_span(encoding, location["start"] + a, location["start"] + b)
            evidence["token_span"] = list(span) if span else None
            if evidence.get("necessary", True):
                intervals.append({"id": evidence["id"], "span": evidence["token_span"]})
    verified = (
        "old"
        if intervals
        and all(p["span"] and p["span"][1] <= layout["R"] for p in intervals)
        else "recent"
        if intervals
        and all(p["span"] and p["span"][0] >= layout["R"] for p in intervals)
        else "straddling"
    )
    forbidden = material.get("answer_literals", [])
    public_other = ep["system"] + canonical(ep["tools"]) + ep["final_request"]
    leakage = [s for s in forbidden if str(s) in public_other]
    if verified == "old":
        recent = tokenizer.decode(layout["ids"][layout["R"] : layout["H"]])
        leakage.extend(s for s in forbidden if str(s) in recent)
    ep["layout_audit"] = {
        "history_tokens": layout["H"] - layout["P"],
        "prefix_tokens": layout["P"],
        "query_tokens": len(layout["ids"]) - layout["H"],
        "reference_tokens": len(token_ids(tokenizer, ep["reference"])),
        "intervals": intervals,
        "assigned_age": slot["assignments"]["age"],
        "verified_age": verified,
        "literal_leakage": leakage,
        "semantic_leakage_review": material["review"].get("semantic_leakage"),
    }
    ep["source_fingerprint"] = sibling_fingerprint(source)
    ep["mutation_plan"], ep["mutations"] = generate_mutations(ep, material)
    ep["validation"] = {
        "compiler": COMPILER_VERSION,
        "compiler_runner_sha256": file_hash(__file__),
        "source_hash": source_spec_hash(source),
        "review": material["review"],
        "reference": run_checker(ep, ep["reference"]),
        "mutations": [run_checker(ep, m["output"]) for m in ep["mutations"]],
    }
    return ep


def validate_schema(ep):
    if set(ep) != REQUIRED_FIELDS:
        raise ValueError(
            f"episode schema missing={REQUIRED_FIELDS - set(ep)}, "
            f"extra={set(ep) - REQUIRED_FIELDS}"
        )
    if ep["schema_version"] != "sc1-v2" or ep["pool"] not in {
        "smoke",
        "setup",
        "final",
    }:
        raise ValueError("schema version/pool")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ep["id"]):
        raise ValueError("invalid episode ID")
    if not 12 <= len(ep["turns"]) <= 24 or not all(
        set(t) == {"role", "text"} for t in ep["turns"]
    ):
        raise ValueError("12–24 public messages required")
    if not 4 <= len(ep["distractors"]) <= 8 or len(
        set(map(canonical, ep["distractors"]))
    ) != len(ep["distractors"]):
        raise ValueError("4–8 distinct distractors required")
    slot = commission_slot(ep["pool"], ep["index"], ep["attempt"])
    if ep["assignments"] != slot["assignments"] or ep["seeds"] != slot["seeds"]:
        raise ValueError("commissioning assignments changed")
    style = "tool-work" if ep["task_spec"]["kind"] == "tool" else "editing"
    if style != ep["assignments"]["style"]:
        raise ValueError("assigned style mismatch")
    if not ep["decisive_facts"] or any(
        ep["turns"][p["turn"]]["role"] != ep["assignments"]["origin"]
        for p in ep["decisive_facts"]
    ):
        raise ValueError("decisive origin mismatch")
    if any(p.get("authority") != "user" for p in ep["instruction_trajectory"]):
        raise ValueError("governing authority must be user")
    if not ep["protected_set"] or not ep["obligations"]:
        raise ValueError("empty obligation/protected set")
    ids = [p["id"] for p in ep["obligations"] + ep["protected_set"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate obligation/invariant ID")
    if ep["pool"] != "smoke":
        provenance = ep["provenance"]
        for key in (
            "author_version",
            "provider",
            "settings",
            "prompt_hash",
            "contract_hash",
            "session_id",
            "transcript_path",
            "transcript_hash",
            "input_hashes",
            "empty_context",
            "external_access_disabled",
            "originality_attested",
        ):
            if key not in provenance or provenance[key] is None:
                raise ValueError("missing production provenance: " + key)
        if not all(
            provenance[k] is True
            for k in (
                "empty_context",
                "external_access_disabled",
                "originality_attested",
            )
        ):
            raise ValueError("production author isolation not attested")
        review = ep["validation"]["review"]
        if (
            not review.get("reviewer")
            or not review.get("narrative_obligations")
            or not review.get("semantic_leakage")
        ):
            raise ValueError("independent semantic review required")
        if review["reviewer"] == provenance["session_id"]:
            raise ValueError("author cannot independently review own source")
        if not ep["distinctness_review"].get("signed"):
            raise ValueError("signed distinctness review required")


def validate_episode(ep, source, tokenizer):
    validate_schema(ep)
    if ep != expand_source(source, tokenizer):
        raise ValueError("expander determinism/artifact mismatch")
    audit = ep["layout_audit"]
    if not 4096 <= audit["history_tokens"] <= 8192 or audit["reference_tokens"] > 256:
        raise ValueError("history/reference token budget")
    if audit["query_tokens"] > MAX_QUERY or audit["prefix_tokens"] > MAX_PREFIX:
        raise ValueError("source grammar input bounds")
    if audit["assigned_age"] != audit["verified_age"] or audit["literal_leakage"]:
        raise ValueError("evidence age/leakage mismatch; repair source, never relabel")
    reference = run_checker(ep, ep["reference"])
    if not reference["success"]:
        raise ValueError(
            "reference failed the production checker: " + canonical(reference["causes"])
        )
    mutations = [run_checker(ep, m["output"]) for m in ep["mutations"]]
    if (
        len(mutations) != 6
        or any(m["success"] for m in mutations)
        or len({m["output"] for m in ep["mutations"]}) != 6
    ):
        raise ValueError("six distinct failing negatives required")
    semantic = [m for m in mutations if m["schema_valid"]]
    if len(semantic) < 2:
        raise ValueError(
            "negatives require type-valid wrong-target/wrong-state coverage"
        )
    for mutation, verdict in zip(ep["mutations"], mutations, strict=True):
        if verdict["schema_valid"] and not set(mutation["obligation_ids"]) & set(
            verdict["failed_obligations"] + verdict["failed_invariants"]
        ):
            raise ValueError("mutation does not violate linked obligation")
    review = ep["validation"]["review"]
    constructs = {"generic_safe": run_checker(ep, review["generic_safe"])}
    if ep["assignments"]["age"] == "old":
        constructs["recency_only"] = run_checker(ep, review["recency_only"])
    if any(v["success"] for v in constructs.values()):
        raise ValueError("generic/recency-only response passed")
    unchanged = check_result(ep, ep["initial_state"])
    if unchanged["success"]:
        raise ValueError("no-op checker")
    probes = []
    for probe in review.get("coverage_probes", []):
        verdict = (
            check_result(ep, probe["result"])
            if "result" in probe
            else run_checker(ep, probe["output"])
        )
        if verdict["success"] or not set(probe["obligation_ids"]) & set(
            verdict["failed_obligations"] + verdict["failed_invariants"]
        ):
            raise ValueError("coverage probe failed to exercise its obligation")
        probes.append(verdict)
    covered = set().union(
        *(
            set(v["failed_obligations"] + v["failed_invariants"])
            for v in mutations + probes
        )
    )
    required = {p["id"] for p in ep["obligations"] + ep["protected_set"]}
    if not required <= covered:
        raise ValueError(
            "uncovered obligations/invariants: " + canonical(sorted(required - covered))
        )
    trace = ep["state_trace"]
    state = copy.deepcopy(trace["start"])
    for event in trace["events"]:
        state, returned = execute_call(state, event["call"], ep["task_spec"])
        if not json_equal(returned, event["return"]):
            raise ValueError("state trace tool return mismatch")
        if event["public_text"] not in ep["turns"][event["turn"]]["text"]:
            raise ValueError("trace event missing from public history")
    if not json_equal(state, ep["initial_state"]):
        raise ValueError("pre-decision state trace mismatch")
    return {
        "id": ep["id"],
        "reference": reference,
        "mutations": mutations,
        "constructs": constructs,
        "unchanged": unchanged,
        "coverage_probes": probes,
        "covered": sorted(covered),
        "layout": audit,
        "compiler": COMPILER_VERSION,
        "reviewer": review.get("reviewer"),
        "source_fingerprint": ep["source_fingerprint"],
    }


def ngrams(text):
    tokens = unicodedata.normalize("NFKC", text).casefold().split()
    return {tuple(tokens[i : i + 8]) for i in range(max(0, len(tokens) - 7))}


def independence_audit(episodes, *, require_review=True):
    rows = []
    for left, right in itertools.combinations(
        sorted(episodes, key=lambda ep: ep["source_id"]), 2
    ):
        if left["source_fingerprint"] == right["source_fingerprint"]:
            raise ValueError("sibling fingerprint collision")
        if left["source_id"] == right["source_id"]:
            raise ValueError("shared source identity")

        def names_and_ids(ep):
            manifest = ep["filler_manifest"]
            values = {
                str(v)
                for k, v in manifest["literal_values"].items()
                if manifest["literal_types"][k] in {"name", "identifier"}
            }
            values.update(str(e[k]) for e in ep["entities"] for k in ("name", "id"))
            return values

        literals_left, literals_right = names_and_ids(left), names_and_ids(right)
        # Proper names and identifiers must be distinct across the two pools.
        if left["pool"] != right["pool"] and literals_left & literals_right:
            raise ValueError("cross-pool literal collision")
        overlaps = {}
        for mode in ("with_filler", "without_filler"):
            sets = []
            for ep in (left, right):
                texts = [t["text"] for t in ep["turns"]]
                if mode == "without_filler":
                    texts[ep["filler_manifest"]["turn"]] = ep["filler_manifest"][
                        "base_text"
                    ]
                sets.append(ngrams("\n".join(texts)))
            overlaps[mode] = (
                len(sets[0] & sets[1]) / len(sets[0] | sets[1])
                if sets[0] | sets[1]
                else 0.0
            )
        review = left["distinctness_review"].get("pairs", {}).get(right["source_id"])
        if (
            require_review
            and (left["pool"] != "smoke" or right["pool"] != "smoke")
            and (
                not isinstance(review, dict)
                or not review.get("signed")
                or review.get("decision") != "distinct"
                or not review.get("reviewer")
                or review.get("other_hash") != right["validation"]["source_hash"]
            )
        ):
            raise ValueError("signed pairwise source review missing")
        rows.append(
            {
                "left": left["id"],
                "right": right["id"],
                "jaccard": overlaps,
                "flag": any(v >= 0.05 for v in overlaps.values()),
                "semantic_review": review,
            }
        )
    return rows


def load_sources(directory):
    paths = sorted(Path(directory).glob("*.source.json"))
    if not paths:
        raise ValueError("no structured source files")
    return [json.loads(path.read_text()) for path in paths]


def validate_bank(directory, tokenizer):
    sources = load_sources(directory)
    episodes, reports = [], []
    for source in sources:
        ep = expand_source(source, tokenizer)
        path = Path(directory) / (ep["id"] + ".episode.json")
        if path.exists() and json.loads(path.read_text()) != ep:
            raise ValueError("frozen episode bytes do not match source expansion")
        episodes.append(ep)
        reports.append(validate_episode(ep, source, tokenizer))
    if len({e["id"] for e in episodes}) != len(episodes) or len(
        {(e["pool"], e["index"]) for e in episodes}
    ) != len(episodes):
        raise ValueError("duplicate episode/slot")
    pairs = independence_audit(episodes)
    return episodes, {
        "episodes": len(episodes),
        "references_pass": len(episodes),
        "mutations_fail": 6 * len(episodes),
        "reports": reports,
        "counts": realized_counts(episodes),
        "pairs": pairs,
        "bank_hash": digest(episodes),
    }


def commissioning_request(
    contract_text, grammar, versions, pool, index, attempt=0, feedback=None
):
    """Policy-independent launcher payload; transport must create a fresh session.

    No provider network operation is hidden here. A caller retains this exact
    payload and the full provider transcript, including its rejection history.
    """
    slot = commission_slot(pool, index, attempt)
    author = versions[slot["assignments"]["author"]]
    if (
        not author.get("immutable_version")
        or not author.get("settings")
        or not author.get("neutral_template")
    ):
        raise ValueError("exact author version/settings/template must be frozen")
    if attempt and not feedback:
        raise ValueError("repair requires retained contract-only rejection feedback")
    return {
        "author": author,
        "session": "new-empty-context",
        "tools": [],
        "retrieval": False,
        "input": {
            "contract": contract_text,
            "grammar": grammar,
            "assignment": slot,
            "feedback": feedback,
        },
        "input_hash": digest(
            {
                "contract": contract_text,
                "grammar": grammar,
                "assignment": slot,
                "feedback": feedback,
            }
        ),
    }

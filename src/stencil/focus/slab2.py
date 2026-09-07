"""SLAB-2: CPU-testable whole-file episodes; no model loading or import work.

Fit-on=none; development-on=authored DEV only; evaluation-on=disjoint authored
families/seeds. Pilot outputs are development cost, never fitting/eval fixtures.
T-floor freezes from all eight DEV T lanes before evaluation: >=50% per trait.
Excluded traits remain diagnostics. Style and delivery substitutions are primary
relapse witnesses; omission witnesses never enter success without passing floor.
Pilot-5: executed >=90%, caps <=2%, eligible traits in >=2 kinds with scheduled
nonzero denominators in >=2 DEV episodes, R final >=5/8. Registered run alone:
R/N x64 plus nested O/T x16, 16 rounds, <=12 GPU-h; prior pilots excluded.
Measured projection in (12,15] hours selects pre-registered 12-round fallback
(requires a fresh shortened schedule/freeze and DEV validation), never fewer arms.
CPU stub output costs are accounting only, NOT measured GPU eligibility.
"""

import ast
import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass, replace
from itertools import permutations
from pathlib import Path

from . import slab as legacy
from .journal import Journal
from .loop import DecodeResult, Message, Session, generate_once
from .register import Register
from .renderer import Request, compact

DOMAINS, KINDS = legacy.DOMAINS, legacy.KINDS
Turn = legacy.Turn
_entry, _problem = legacy._entry, legacy._problem
qwen_encode, tokenizer_manifest = legacy.qwen_encode, legacy.tokenizer_manifest
digest, changed_code, indent_widths = (
    legacy.digest,
    legacy.changed_code,
    legacy.indent_widths,
)
SCHEMA = 3
REPLY_CAP = 1024
DATA_LINEAGE = legacy.DATA_LINEAGE
TRAITS = {
    "language": "language",
    "indent": "style",
    "format": "format",
    "delivery": "process",
    "delivery_scope": "process",
}
SYSTEM_PROMPT = (
    "Maintain Python modules. Each response is exactly ONE fenced code block "
    "containing the WHOLE requested file: ```python core.py or ```python policy.py, "
    "then a closing fence and one trailer: report: task=A status=ok delivery=ready. "
    "task is the request letter; status is ok or blocked. delivery is a short value. "
    "Verbose format includes delivery only in its scoped task; compact format omits "
    "delivery. Otherwise report task and status always. After cancellation/completion "
    "format defaults to compact and delivery defaults to ready. The harness writes "
    "the file and runs cumulative public tests; feedback is summary "
    "and function names. "
    "Preserve existing functions; re-emission is free. Current indentation applies "
    "only to changed definitions. Use short one-line docstrings, "
    "a local result and return. "
    "No imports or external IO. Reply cap 1024 tokens; retain concise whole files."
)


def literal(key, value):
    if key == "indent":
        return (
            f"indent {value} = block bodies indented by exactly "
            f"{value} spaces per level"
        )
    if key == "format":
        return f"format {value} = trailer " + (
            "omits delivery"
            if value == "compact"
            else "includes delivery when task is delivery-scoped"
        )
    if key == "delivery":
        return f"delivery {value} = trailer delivery={value} when verbose and scoped"
    if key == "language":
        return f"language {value} = executable Python file"
    return f"{key} {value} = harness runs public tests after file write"


@dataclass(frozen=True)
class Episode(legacy.Episode):
    def public_view(self):
        return dict(
            episode_id=self.episode_id,
            template_id=self.template_id,
            initial=dict(self.initial),
            system=SYSTEM_PROMPT,
            interface="whole-file Python fence plus report trailer",
            defaults=[asdict(e) for e in self.defaults],
            turns=[
                {
                    k: v
                    for k, v in asdict(t).items()
                    if k not in {"live", "retired", "denominators", "t_text", "events"}
                }
                for t in self.turns
            ],
        )

    def manifest(self):
        return dict(
            schema=SCHEMA,
            episode_id=self.episode_id,
            family=self.family,
            seed=self.seed,
            template_id=self.template_id,
            rounds=len(self.turns),
            episode_sha256=digest(asdict(self)),
            public_sha256=digest(self.public_view()),
            hidden_sha256=digest(self.private),
            turn_hashes=[digest(asdict(t)) for t in self.turns],
            system_sha256=digest(SYSTEM_PROMPT),
            data_lineage=DATA_LINEAGE,
            token_cap=REPLY_CAP,
            tokenizer=tokenizer_manifest(),
        )


def generate_episode(family="dev", index=0, seed=20260906):
    if family not in {"dev", "eval"} or not 0 <= index < (8 if family == "dev" else 64):
        raise ValueError("unknown family/index")
    # Disjoint arithmetic seed namespaces for every caller seed.
    episode_seed = seed * 10000 + (index if family == "dev" else 1000 + index)
    rng = random.Random(episode_seed)
    domain = DOMAINS[index % 4]
    n = 16
    # Six ordering shapes; DEV uses a distinct reinstatement-time production.
    shape = rng.choice(tuple(permutations(("indent", "format", "delivery"))))
    event_times = (10, 11, 12)
    schedule = dict(zip(shape, event_times, strict=True))
    # Independent stream preserves problem realizations while varying action keys.
    format_action = random.Random(episode_seed ^ 0x51AB).choice(
        ("cancels", "completes", "supersedes")
    )
    reinstate = 13 if family == "dev" else rng.choice((14, 15))
    initial_indent, next_indent = rng.sample(("2", "3", "4"), 2)
    delivery = rng.choice(("draft", "queued", "staged"))
    scoped_task = rng.choice(("A", "B"))
    other_task = "B" if scoped_task == "A" else "A"
    switch1, switch2, switch3 = (
        rng.choice((3, 4)),
        rng.choice((6, 7)),
        rng.choice((8, 9)),
    )
    receipt_key = (
        rng.choice(("receipt", "verification"))
        if family == "eval"
        else rng.choice(("test_record", "validation"))
    )

    def entry(action, key, kind, value, index, target=None, task=None):
        row = _entry(action, key, kind, value, index, target, task)
        wording = (
            f"Workshop obligation: {key} must be {value}."
            if family == "dev"
            else f"Service contract requires {value} for {key}."
        )
        return replace(row, text=wording + " " + literal(key, value))

    defaults = (
        entry("add", "format", "format", "compact", -1),
        entry("add", "delivery", "process", "ready", -1, task=scoped_task),
    )
    live = {
        "language": "Python",
        "indent": initial_indent,
        "format": "verbose",
        receipt_key: "test-after-edit",
        "delivery": delivery,
    }
    retired, retired_at = {}, {}
    turns, private = [], []
    for i in range(n):
        task = scoped_task if switch1 <= i < switch2 or i >= switch3 else other_task
        events = []
        if i == 0:
            events = [
                entry(
                    "add",
                    key,
                    kind,
                    live[key],
                    i,
                    task=scoped_task if key == "delivery" else None,
                )
                for key, kind in (
                    ("language", "language"),
                    ("indent", "style"),
                    ("format", "format"),
                    (receipt_key, "process"),
                    ("delivery", "process"),
                )
            ]
        if i == schedule["indent"]:
            events.append(entry("supersedes", "indent", "style", next_indent, i, 1))
            retired["indent"], live["indent"] = initial_indent, next_indent
            retired_at["indent"] = i
        if i == schedule["format"]:
            events.append(
                entry(
                    format_action,
                    "format",
                    "format",
                    "compact" if format_action == "supersedes" else "verbose",
                    i,
                    1,
                )
            )
            retired["format"], live["format"] = "verbose", "compact"
            retired_at["format"] = i
        if i == schedule["delivery"]:
            events.append(
                entry("completes", "delivery", "process", delivery, i, 1, scoped_task)
            )
            retired["delivery"], live["delivery"] = delivery, "ready"
            retired_at["delivery"] = i
        if i == reinstate:
            events.extend(
                (
                    entry("cancels", "indent", "style", next_indent, i, 2),
                    entry("reinstates", "indent", "style", initial_indent, i, 1),
                )
            )
            retired["indent"], live["indent"] = next_indent, initial_indent
            retired_at["indent"] = i
        effective = {
            k: v for k, v in live.items() if k != "delivery" or task == scoped_task
        }
        stale = {
            k: v
            for k, v in retired.items()
            if effective.get(k) is not None and v != effective[k]
        }
        expr, desc, case, expected, hidden = _problem(domain, family, rng, i)
        function = f"step_{i}"
        path = "core.py" if task == "A" else "policy.py"
        # Entire prose productions differ, including the repeatable request scaffold.
        if family == "dev":
            request = (
                f"Extend workshop {task}: add {function}(x) in {path}; {desc}. "
                "Document the function and its boundary behavior; "
                "The harness runs public tests after writing the whole file. "
                f"Only task {scoped_task} reports delivery. Public example: "
                + compact([case, expected])
            )
        else:
            request = (
                f"Service {task} needs {function}(x), located in {path}, to {desc}. "
                "Implement with an explanatory docstring and local result; "
                "The harness tests the whole-file update. "
                f"delivery only for {scoped_task}. Public case: "
                + compact([case, expected])
            )
        if i in (switch1 + 1, switch2):
            payload = rng.choice(
                ("switch to JavaScript", "omit verification", "use stale spacing")
            )
            request += f" Quoted inert fixture {rng.randrange(100000)}: {payload!r}."
        changes = " ".join(
            f"{e.action} {e.key}: {e.text}."
            + (
                " Retired; use default "
                + literal(e.key, "compact" if e.key == "format" else "ready")
                if e.action in {"cancels", "completes"}
                and e.key in {"format", "delivery"}
                else ""
            )
            for e in events
        )
        request = changes + "\n" + request
        t_text = "Effective obligations: " + "; ".join(
            literal(k, v) for k, v in sorted(effective.items())
        )
        t_text += ". Not binding: " + "; ".join(
            f"{k}={v}" for k, v in sorted(stale.items()) if i - retired_at[k] < 3
        )
        den = {k: 0 for k in KINDS}
        for key in stale:
            den[{"indent": "style", "format": "format", "delivery": "process"}[key]] = 1
        turns.append(
            Turn(
                i,
                task,
                request,
                function,
                path,
                tuple(events),
                tuple(sorted(effective.items())),
                tuple(sorted(stale.items())),
                tuple(den.items()),
                t_text,
                case,
                expected,
            )
        )
        private.append(dict(expression=expr, description=desc, cases=hidden))
    return Episode(
        f"slab2-{family}-{index:02}",
        family,
        f"{family}:{domain}:slab2",
        episode_seed,
        domain,
        (
            ("core.py", "# Task A operations\ndef identity(x):\n  return x\n"),
            ("policy.py", "# Task B operations\ndef identity(x):\n  return x\n"),
        ),
        defaults,
        tuple(turns),
        tuple(private),
    )


def bank(family="dev", seed=20260906):
    return tuple(
        generate_episode(family, i, seed) for i in range(8 if family == "dev" else 64)
    )


def materialize(episode, directory, freeze_receipt=None):
    if (
        episode.family == "eval"
        and freeze_receipt != episode.manifest()["episode_sha256"]
    ):
        raise ValueError("evaluation requires matching freeze receipt")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    for path, code in episode.initial:
        (root / path).write_text(code)


class ReplyError(ValueError):
    pass


def parse_reply(output, target):
    """One fence, optional explicit path, one strict trailer; no envelope recovery."""
    match = re.fullmatch(
        r"\s*```python(?: (core\.py|policy\.py))?\n((?:(?!```)[\s\S])*?)\n```\n"
        r"report: task=([AB]) status=(ok|blocked)"
        r"(?: delivery=([A-Za-z0-9_-]{1,32}))?\s*",
        output,
    )
    if not match or not match[2].strip() or len(output.encode()) > 16384:
        raise ReplyError("expected one Python whole-file fence and report trailer")
    path = match[1] or target
    report = dict(task=match[3], status=match[4])
    if match[5] is not None:
        report["delivery"] = match[5]
    return path, match[2] + "\n", report


class Executor:
    def __init__(self, directory, episode):
        self.directory, self.episode = Path(directory), episode
        self.last_parsable = dict(episode.initial)
        self.history = []
        self.result = None

    def run(self, output, turn, *, truncated=False):
        t = self.episode.turns[turn]
        self.prior = list(self.history)
        self.changed, self.report, self.path = "", {}, None
        result = dict(executed=False, breakage=False, passed=0, failed=0, functions={})
        self.result = result
        if truncated:
            result.update(breakage=True, error="capped reply")
            return result
        try:
            path, code, report = parse_reply(output, t.path)
            self.path, self.report = path, report
            target = self.directory / path
            if target.is_symlink():
                raise ReplyError("symlink")
            self.changed = changed_code(self.last_parsable[path], code)
            target.write_text(code)
            result["executed"] = True
            try:
                ast.parse(code)
                self.last_parsable[path] = code
            except (SyntaxError, RecursionError):
                result["breakage"] = True
            for filename, _ in self.episode.initial:
                current = (self.directory / filename).read_text()
                try:
                    tree = ast.parse(current)
                    names = [
                        n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                    ]
                    result["functions"][filename] = [name[:64] for name in names[:32]]
                    cases = [
                        p for p in self.episode.turns[: turn + 1] if p.path == filename
                    ]
                    present = [p for p in cases if p.function in names]
                    result["failed"] += len(cases) - len(present)
                    # Execute zero-case files too: invalid top-level code is breakage.
                    values = legacy.evaluate_many(
                        current, [(p.function, p.public_case) for p in present]
                    )
                    for value, p in zip(values, present, strict=True):
                        result["passed"] += int(value == p.public_expected)
                        result["failed"] += int(value != p.public_expected)
                except (SyntaxError, RecursionError, legacy.InvalidProgram):
                    result["breakage"] = True
                    result["failed"] += 1
            self.history.append(dict(code=self.changed, report=report))
        except (ReplyError, OSError, KeyError):
            result.update(breakage=True, error="malformed reply or file write failed")
        assert len(compact(result).encode()) < 8192
        return result


def reference(episode, turn):
    t = episode.turns[turn]
    code = dict(episode.initial)[t.path]
    for i, p in enumerate(episode.turns[: turn + 1]):
        if p.path == t.path:
            space = " " * int(dict(p.live)["indent"])
            code += (
                f'\ndef {p.function}(x):\n{space}"""Return the specified result."""\n'
                f"{space}result = {episode.private[i]['expression']}\n"
                f"{space}return result\n"
            )
    rules = dict(t.live)
    delivery = (
        f" delivery={rules['delivery']}"
        if rules["format"] == "verbose" and "delivery" in rules
        else ""
    )
    return f"```python {t.path}\n{code}```\nreport: task={t.task} status=ok{delivery}"


def check(episode, turn, executor, *, eligible_traits=None):
    """Raw traits always reported; success/relapse use only the frozen T floor."""
    floor_pending = eligible_traits is None
    eligible_traits = () if floor_pending else eligible_traits
    if not set(eligible_traits) <= TRAITS.keys():
        raise ValueError("unknown floor trait")
    t = episode.turns[turn]
    rules, stale = dict(t.live), dict(t.retired)
    report, code = executor.report, executor.changed
    observed = executor.result["executed"]
    widths = indent_widths(code)
    applicable = dict(
        language=True,
        indent=True,
        format=rules["format"] == "compact",
        delivery=rules["format"] == "verbose" and "delivery" in rules,
        delivery_scope=rules["format"] == "verbose" and "delivery" not in rules,
    )
    satisfied = dict(
        language=not executor.result["breakage"],
        indent=not executor.result["breakage"]
        and all(w == int(rules["indent"]) for w in widths),
        format=(
            "delivery" not in report
            if rules["format"] == "compact"
            else ("delivery" in report if "delivery" in rules else True)
        ),
        delivery=report.get("delivery") == rules.get("delivery"),
        delivery_scope="delivery" not in report,
    )
    den = dict(
        language=0,
        indent=int("indent" in stale),
        format=int("format" in stale),
        delivery=int("delivery" in stale and applicable["delivery"]),
        delivery_scope=0,
    )
    prior = dict(
        language=False,
        indent=any(
            int(stale.get("indent", -1)) in indent_widths(h["code"])
            for h in executor.prior
        ),
        format=any("delivery" in h["report"] for h in executor.prior),
        delivery=any(
            stale.get("delivery") is not None
            and h["report"].get("delivery") == stale["delivery"]
            for h in executor.prior
        ),
        delivery_scope=False,
    )
    raw_relapse = dict(
        language=False,
        indent=int(stale.get("indent", -1)) in widths,
        format="delivery" in report,
        delivery=report.get("delivery") == stale.get("delivery")
        and "delivery" in stale,
        delivery_scope=False,
    )
    raw_relapse = {k: bool(den[k] and prior[k] and raw_relapse[k]) for k in TRAITS}
    integration = True
    breakage = executor.result["breakage"]
    for filename, _ in episode.initial:
        cases = [
            (p.function, x, y)
            for i, p in enumerate(episode.turns[: turn + 1])
            if p.path == filename
            for x, y in episode.private[i]["cases"]
        ]
        try:
            current = (executor.directory / filename).read_text()
            names = {
                n.name
                for n in ast.parse(current).body
                if isinstance(n, ast.FunctionDef)
            }
            if any(name not in names for name, _, _ in cases):
                integration = False
                continue
            values = legacy.evaluate_many(current, [(name, x) for name, x, _ in cases])
            integration &= all(v == c[2] for v, c in zip(values, cases, strict=True))
        except (SyntaxError, RecursionError, legacy.InvalidProgram):
            integration = False
            breakage = True
    wrong = observed and (executor.path != t.path or report.get("task") != t.task)
    violations = {
        k: bool(observed and applicable[k] and not satisfied[k]) for k in TRAITS
    }
    violations.update(breakage=breakage, wrong_family=wrong, semantic=not integration)
    return dict(
        observed=observed,
        integration=integration,
        applicable=applicable,
        satisfied=satisfied,
        diagnostics=violations,
        trait_denominators=den,
        report_ok=report.get("status") == "ok",
        raw_relapse=raw_relapse,
        prior_trait_present=prior,
        relapse={k: raw_relapse[k] if observed else None for k in eligible_traits},
        floor_pending=floor_pending,
        success=None
        if floor_pending
        else bool(
            observed
            and integration
            and not breakage
            and not wrong
            and report.get("status") == "ok"
            and not any(violations[k] for k in eligible_traits)
        ),
    )


def freeze_t_floor(records):
    """Only complete DEV T observations qualify; missing/capped attempts fail floor."""
    expected = {(f"slab2-dev-{i:02}", j) for i in range(8) for j in range(16)}
    if (
        len(records) != 128
        or {(r["episode_id"], r["turn"]) for r in records} != expected
        or any(r["arm"] != "T" for r in records)
    ):
        raise ValueError("T floor requires all 128 unique DEV T rounds")
    counts = {}
    for trait in TRAITS:
        rows = [r for r in records if r["outcome"]["applicable"][trait]]
        passed = sum(
            r["outcome"]["observed"] and r["outcome"]["satisfied"][trait] for r in rows
        )
        episodes = sorted(
            {
                r["episode_id"]
                for r in records
                if r["outcome"]["trait_denominators"][trait]
            }
        )
        counts[trait] = dict(
            passed=passed,
            total=len(rows),
            eligible=bool(rows and passed * 2 >= len(rows)),
            opportunity_episodes=episodes,
        )
    return dict(
        data_lineage=DATA_LINEAGE,
        records_sha256=digest(records),
        traits=counts,
        eligible_traits=[k for k, v in counts.items() if v["eligible"]],
    )


def pilot5_reading(records, floor, projected_gpu_hours):
    required = {
        (f"slab2-dev-{i:02}", arm, j)
        for i in range(8)
        for arm in "RNT"
        for j in range(16)
    }
    actual = {(r["episode_id"], r["arm"], r["turn"]) for r in records}
    complete = required <= actual and len(actual) == len(records)
    executed = sum(r["outcome"]["observed"] for r in records) / max(1, len(records))
    caps = sum(r["truncated"] for r in records) / max(1, len(records))
    kinds = {
        TRAITS[k]
        for k, v in floor["traits"].items()
        if v["eligible"] and len(v["opportunity_episodes"]) >= 2
    }
    finals = sum(
        o["observed"]
        and o["integration"]
        and o["report_ok"]
        and not any(
            o["diagnostics"][k]
            for k in (*floor["eligible_traits"], "breakage", "wrong_family")
        )
        for r in records
        if r["arm"] == "R" and r["turn"] == 15
        for o in [r["outcome"]]
    )
    cost = projected_gpu_hours
    return dict(
        eligible=bool(
            complete
            and executed >= 0.9
            and caps <= 0.02
            and len(kinds) >= 2
            and finals >= 5
            and cost is not None
            and 0 < cost <= 12
        ),
        executed_fraction=executed,
        cap_fraction=caps,
        kinds=sorted(kinds),
        r_final_success=finals,
        cost_action="unmeasured"
        if cost is None
        else "16-round"
        if 0 < cost <= 12
        else "12-round-refreeze"
        if 12 < cost <= 15
        else "stop",
    )


def measured_projection(lane_seconds, *, load_seconds=0, reserve=1.25):
    """Measured GPU-held per-lane seconds, charged once; no prior pilot spend."""
    if (
        set(lane_seconds) != set("RNTO")
        or any(v <= 0 for v in lane_seconds.values())
        or load_seconds < 0
        or reserve < 1
    ):
        raise ValueError("positive measured per-arm lane seconds required")
    return (
        load_seconds
        + reserve * sum(lane_seconds[a] * (64 if a in "RN" else 16) for a in "RNTO")
    ) / 3600


def paired_context_gate(prompt_tokens, budget=32768, generation_cap=REPLY_CAP):
    if set(prompt_tokens) != set("RNTO"):
        raise ValueError("all four arms required")
    return all(0 <= n <= budget - generation_cap for n in prompt_tokens.values())


def mutants(episode, turn):
    output = reference(episode, turn)
    t = episode.turns[turn]
    path, code, report = parse_reply(output, t.path)

    def reply(body=code, trailer=report, filename=path):
        return f"```python {filename}\n{body}```\nreport: " + " ".join(
            f"{k}={v}" for k, v in trailer.items()
        )

    widths = dict(t.live)["indent"]
    replacement = dict(t.retired).get("indent", str(2 if widths != "2" else 3))
    prefix, new = code.split(f"def {t.function}(x):", 1)
    bad_indent = new.replace("\n" + " " * int(widths), "\n" + " " * int(replacement))
    outputs = dict(
        indent=reply(prefix + f"def {t.function}(x):" + bad_indent),
        breakage="```python\ndef broken(:\n```\nreport: task=A status=ok",
        wrong_family=reply(filename="policy.py" if path == "core.py" else "core.py"),
        semantic=reply(
            code.replace(
                f"result = {episode.private[turn]['expression']}", "result = None"
            )
        ),
        format=reply(trailer={**report, "delivery": "stale"})
        if "delivery" not in report
        else reply(trailer={k: v for k, v in report.items() if k != "delivery"}),
    )
    outputs["hidden_only"] = reply(
        code.replace(
            f"result = {episode.private[turn]['expression']}",
            f"result = {t.public_expected!r}",
        )
    )
    outputs["language"] = outputs["breakage"]
    if dict(t.live)["format"] == "verbose":
        outputs["delivery" if "delivery" in report else "delivery_scope"] = outputs.pop(
            "format"
        )
    if "delivery" in report:
        outputs["delivery"] = reply(
            trailer={**report, "delivery": dict(t.retired).get("delivery", "wrong")}
        )
    return outputs


def should_pass(episode, turn):
    output = reference(episode, turn)
    return dict(
        whole_file=output,
        implicit_path=output.replace(f"python {episode.turns[turn].path}", "python", 1),
        blank_lines=output.replace("\n```\nreport:", "\n\n```\nreport:"),
    )


def text_events(episode, turn):
    """CPU stub updater parses public lifecycle clauses; never consumes gold events.

    This is a transport test double, not the registered evaluation updater.
    GPU evaluation must supply its frozen classifier, and cannot claim these scores.
    """
    t = episode.turns[turn]
    scoped = re.search(r"(?:Only task |delivery only for )([AB])", t.request)[1]
    entries = []
    for action, key, value in re.findall(
        r"(add|supersedes|cancels|completes|reinstates) (\w+): "
        r"Service contract requires ([\w-]+) for",
        t.request,
    ):
        kind = (
            "style"
            if key == "indent"
            else "process"
            if key in {"delivery", "receipt", "verification"}
            else key
        )
        target = (
            None
            if action == "add"
            else 2
            if action == "cancels" and key == "indent"
            else 1
        )
        entries.append(
            _entry(
                action,
                key,
                kind,
                value,
                turn,
                target,
                scoped if key == "delivery" else None,
            )
        )
        entries[-1] = replace(entries[-1], text=literal(key, value))
    return tuple(entries)


def dry_run(directory, episode, arm, *, freeze_receipt=None):
    """Real loop/renderer/journal, reference decoder, real tokenizer; CPU only."""
    if arm not in "RNTO" or len(arm) != 1 or len(episode.turns) != 16:
        raise ValueError("four arms, 16 rounds only")
    root = Path(directory)
    materialize(episode, root / "workspace", freeze_receipt)
    executor = Executor(root / "workspace", episode)
    session = Session(
        Register(defaults=episode.defaults, task_handles={"A", "B"}),
        Request("", "tool_call"),
        Journal(root / "loop.jsonl"),
    )
    accounting, records = [], []
    feedback = None
    for i, t in enumerate(episode.turns):
        session.request = Request(
            "",
            "tool_call",
            t.task,
            encode=qwen_encode,
            system=SYSTEM_PROMPT,
            max_tokens=32768 - REPLY_CAP,
            rule_mode=arm,
            rule_text=t.t_text,
            template_id=episode.template_id,
        )
        messages = []
        if feedback is not None:
            messages.append(Message(f"tool{i}", "tool", "", tool_results=(feedback,)))
        events = t.events if episode.family == "dev" else text_events(episode, i)
        messages.append(Message(f"m{i}", "user", t.request, events, adopted=True))
        scripted = reference(episode, i)

        def decoder(rendered, t=t, scripted=scripted, i=i):
            assert {v.entry.key: v.entry.value for v in rendered.live} == dict(t.live)
            prompt = len(rendered.prompt_ids)
            output_ids = qwen_encode(scripted)
            assert len(output_ids) <= REPLY_CAP
            assert prompt + REPLY_CAP <= 32768
            accounting.append(dict(round=i, prompt=prompt, generated=len(output_ids)))
            return DecodeResult(scripted, output_ids=output_ids, truncated=False)

        output, _ = generate_once(session, messages, decoder)
        feedback = executor.run(output, i)
        outcome = check(episode, i, executor, eligible_traits=tuple(TRAITS))
        assert outcome["success"], (episode.episode_id, i, outcome)
        records.append(
            dict(
                episode_id=episode.episode_id,
                arm=arm,
                turn=i,
                truncated=False,
                outcome=outcome,
            )
        )
    (root / "checker.json").write_text(compact(records) + "\n")
    return dict(
        episode_id=episode.episode_id,
        arm=arm,
        accounting=accounting,
        records=records,
        max_context=max(r["prompt"] for r in accounting),
        input_tokens=sum(r["prompt"] for r in accounting),
        output_tokens=sum(r["generated"] for r in accounting),
    )


def paired_clauses(rendered, baseline, eligible_traits):
    """Retain registered paired statistics, aggregating eligible traits by kind."""
    if not set(eligible_traits) <= TRAITS.keys():
        raise ValueError("unknown floor trait")

    def convert(lanes):
        converted = []
        for lane in lanes:
            if len(lane) != 16:
                raise ValueError("16 scheduled rounds required")
            rows = []
            for o in lane:
                rows.append(
                    dict(
                        observed=o["observed"],
                        violations=o["diagnostics"],
                        success=bool(
                            o["observed"]
                            and o["integration"]
                            and o["report_ok"]
                            and not any(
                                o["diagnostics"][k]
                                for k in (*eligible_traits, "breakage", "wrong_family")
                            )
                        ),
                        denominators={
                            kind: int(
                                any(
                                    o["trait_denominators"][k]
                                    for k in eligible_traits
                                    if TRAITS[k] == kind
                                )
                            )
                            for kind in KINDS
                        },
                        relapse={
                            kind: any(
                                o["raw_relapse"][k]
                                for k in eligible_traits
                                if TRAITS[k] == kind
                            )
                            for kind in KINDS
                        },
                    )
                )
            converted.append(rows)
        return converted

    return legacy.paired_clauses(convert(rendered), convert(baseline))


def write_manifests(directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    receipt = dict(
        schema=SCHEMA,
        data_lineage=DATA_LINEAGE,
        tokenizer=tokenizer_manifest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        dependencies={
            name: hashlib.sha256(
                Path(__file__).with_name(name).read_bytes()
            ).hexdigest()
            for name in (
                "slab.py",
                "slab_sandbox.py",
                "loop.py",
                "renderer.py",
                "register.py",
                "journal.py",
            )
        },
        banks={f: [e.manifest() for e in bank(f)] for f in ("dev", "eval")},
        oracle_text_subset=[f"slab2-eval-{i:02}" for i in range(16)],
        registration=__doc__,
    )
    (root / "slab2_manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def audit_bank(directory):
    root = Path(directory)
    receipt = write_manifests(root)
    lanes = []
    for family in ("dev", "eval"):
        for e in bank(family):
            paired = {}
            for arm in "RNTO":
                lane = dry_run(
                    root / e.episode_id / arm,
                    e,
                    arm,
                    freeze_receipt=e.manifest()["episode_sha256"],
                )
                paired[arm] = lane["max_context"]
                lanes.append({k: v for k, v in lane.items() if k != "records"})
            assert paired_context_gate(paired)
    result = dict(
        schema=SCHEMA,
        data_lineage=DATA_LINEAGE,
        tokenizer=tokenizer_manifest(),
        model_cost_projection=None,
        stub_only=True,
        episodes=72,
        calls=72 * 4 * 16,
        max_context_per_arm={
            a: max(lane["max_context"] for lane in lanes if lane["arm"] == a)
            for a in "RNTO"
        },
        lanes=lanes,
        manifest_sha256=digest(receipt),
        updater="DEV gold; eval public-text CPU stub, not a qualified GPU updater",
    )
    result["registered_token_totals"] = {
        a: {
            field: sum(
                lane[field]
                for lane in lanes
                if lane["arm"] == a
                and lane["episode_id"].startswith("slab2-eval")
                and (a in "RN" or lane["episode_id"] in receipt["oracle_text_subset"])
            )
            for field in ("input_tokens", "output_tokens")
        }
        for a in "RNTO"
    }
    (root / "slab2_cpu_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    result = audit_bank(args.audit)
    print(compact({k: v for k, v in result.items() if k != "lanes"}))

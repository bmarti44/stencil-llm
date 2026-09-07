"""Amendment 6. Scoped edits; old SLAB-2 code and primary remain frozen."""

import ast
import re
from dataclasses import asdict, replace
from fractions import Fraction

from . import slab2 as old
from . import slab2_endpoint as ep

# Compatibility surface for the real sequential driver, without mutating old code.
REPLY_CAP = old.REPLY_CAP
TRAITS = old.TRAITS
qwen_encode = old.qwen_encode
validate_rounds = old.validate_rounds
materialize = old.materialize
parse_reply = old.parse_reply
file_written = old.file_written
reference = old.reference
SYSTEM_PROMPT = old.SYSTEM_PROMPT.replace(
    "containing the WHOLE requested file", "containing ONLY the requested function"
).replace(
    "Preserve existing functions; re-emission is free.",
    "Emit no other functions. The harness preserves all other definitions.",
).replace("retain concise whole files.", "retain a concise function.").replace(
    "the file and runs cumulative public tests",
    "only that function into the file and runs cumulative public tests",
) + (
    " Put the function def at column zero. Apply the required indentation consistently "
    "to ALL body lines including the docstring. The harness anchors the def only; "
    "it does not fix body indentation. On a Python syntax error you receive exactly "
    "one repair opportunity; correct and resubmit the same function and trailer."
)


class Episode(old.Episode):
    def public_view(self):
        view = super().public_view()
        view.update(
            system=SYSTEM_PROMPT, interface="scoped function plus one syntax repair"
        )
        return view

    def manifest(self):
        view = super().manifest()
        view.update(system_sha256=old.digest(SYSTEM_PROMPT), schema=6)
        return view


def generate_episode(family="dev", index=0, seed=None, n_rounds=16):
    seed = (20260906 if family == "dev" else 2026090706) if seed is None else seed
    e = Episode(**vars(old.generate_episode(family, index, seed, n_rounds)))
    if family == "dev":
        return e
    # New realizations of the same grammar, not a new task-family claim.
    turns = tuple(
        replace(
            t,
            request=t.request.replace(
                f"Service {t.task} needs {t.function}(x), located in {t.path}, to ",
                f"Implement operation {t.function}(x) for component {t.task} "
                f"in {t.path}: ",
            ).replace("Public case:", "Required input/output example:"),
        )
        for t in e.turns
    )
    return replace(
        e,
        episode_id=f"slab2-v2-eval-{index:02}",
        template_id=e.template_id + ":scoped-realization-6",
        turns=turns,
    )


def bank(family="dev", seed=None, n_rounds=16):
    return tuple(
        generate_episode(family, i, seed, n_rounds)
        for i in range(8 if family == "dev" else 64)
    )


def lineage_receipt(episodes):
    prior = old.bank("eval") + old.bank("dev")

    def content(e):
        return old.digest({"turns": [asdict(t) for t in e.turns], "private": e.private})

    fields = {
        "seeds": lambda e: e.seed,
        "episode_hashes": lambda e: old.digest(asdict(e)),
        "templates": lambda e: e.template_id,
        "content_without_identity": content,
    }
    receipt = {}
    for key, fn in fields.items():
        fresh, spent = [fn(e) for e in episodes], [fn(e) for e in prior]
        assert not set(fresh) & set(spent), key
        if key != "templates":
            assert len(set(fresh)) == len(episodes), key
        receipt[key] = dict(fresh=fresh, prior=spent, overlap=[])
    return receipt


def scoped_request(request, turn, current):
    request = request.replace(
        "writing the whole file", "splicing the function"
    ).replace("whole-file update", "function update")
    return (
        request + f"\nEmit ONLY {turn.function}(x) in {turn.path}, no other "
        "definitions. The harness splices it at top level, preserving other bytes. "
        "Keep def at column zero; use consistent body indentation including docstring."
        f"\nCurrent target file:\n{current}"
    )


def snippet(output, turn):
    path, code, report = parse_reply(output, turn.path)
    if path != turn.path:
        raise old.ReplyError("wrong_scoped_path")
    lines = code.splitlines(keepends=True)
    defs = [
        i
        for i, line in enumerate(lines)
        if re.match(r"\s*def\s+" + re.escape(turn.function) + r"\s*\(", line)
    ]
    if len(defs) != 1:
        raise old.ReplyError("expected_one_target_function")
    # Anchor ONLY the def. A uniformly shifted body keeps its emitted width;
    # a four-space docstring/two-space statement still reaches Python unchanged.
    lines[defs[0]] = lines[defs[0]].lstrip(" \t")
    return path, "".join(lines), report


def splice(current, code, function):
    tree = ast.parse(code)
    if (
        len(tree.body) != 1
        or not isinstance(tree.body[0], ast.FunctionDef)
        or tree.body[0].name != function
        or tree.body[0].decorator_list
    ):
        raise old.ReplyError("scope_violation")
    prior = ast.parse(current)
    nodes = [
        n for n in prior.body if isinstance(n, ast.FunctionDef) and n.name == function
    ]
    lines = current.splitlines(keepends=True)
    if nodes:
        n = nodes[0]
        return "".join(lines[: n.lineno - 1]) + code + "".join(lines[n.end_lineno :])
    return current + ("\n" if current.endswith("\n") else "\n\n") + code


def attempted(output, turn):
    try:
        _, code, _ = snippet(output, turn)
    except old.ReplyError:
        return False
    width = int(dict(turn.live)["indent"])
    return any(
        line.strip() and len(line) - len(line.lstrip(" ")) == width
        for line in code.splitlines()
        if not line.lstrip().startswith("#")
    )


class Executor(old.Executor):
    def run(self, output, turn, *, truncated=False):
        t = self.episode.turns[turn]
        try:
            if truncated:
                return super().run(output, turn, truncated=True)
            path, code, report = snippet(output, t)
            try:
                ast.parse(code, filename=path)
            except SyntaxError as exc:
                # Initialize exactly the legacy executor's failure state, then
                # preserve the interpreter diagnostic rather than paraphrasing it.
                result = super().run(output, turn)
                self.report, self.path, self.changed = report, path, ""
                result.update(
                    executed=True,
                    breakage=True,
                    category="syntax_error",
                    syntax_type=type(exc).__name__,
                    error=str(exc),
                    offending_line=exc.text,
                    lineno=exc.lineno,
                    offset=exc.offset,
                    filename=exc.filename,
                )
                return result
            merged = splice(self.last_parsable[path], code, t.function)
            trailer = " ".join(f"{k}={v}" for k, v in report.items())
            result = super().run(
                f"```python {path}\n{merged}```\nreport: {trailer}", turn
            )
            # Runtime/semantic exceptions are integration failures, not breakage.
            result["breakage"] = bool(result.get("category"))
            return result
        except old.ReplyError as exc:
            # Reset state through the real consumer without writing any file.
            result = super().run("", turn)
            result.update(category=str(exc), error=str(exc), breakage=True)
            return result


def check(episode, turn, executor, *, eligible_traits=None):
    outcome = old.check(episode, turn, executor, eligible_traits=eligible_traits)
    outcome["diagnostics"]["breakage"] = bool(executor.result["breakage"])
    return outcome


def harm(records, episodes):
    index = {(r["episode_id"], r["arm"], r["turn"]): r for r in records}
    if len(index) != len(records):
        raise ValueError("duplicate records")
    contrasts = {}
    for arm in "RT":
        pairs, details = [], []
        for e in episodes:
            common = []
            for t in ep.change_rounds(e)["indent"]:
                a, n = (
                    index.get((e.episode_id, arm, t)),
                    index.get((e.episode_id, "N", t)),
                )
                if a and n and a["indent_attempted"] and n["indent_attempted"]:
                    common.append(
                        (
                            int(a["outcome"]["diagnostics"]["breakage"]),
                            int(n["outcome"]["diagnostics"]["breakage"]),
                        )
                    )
            if common:
                pairs.append(
                    tuple(
                        Fraction(sum(x[j] for x in common), len(common)) for j in (0, 1)
                    )
                )
            details.append(dict(episode_id=e.episode_id, common_attempts=len(common)))
        contrasts[arm] = dict(
            **ep._sign(pairs),
            episodes=details,
            coverage=len(pairs) >= (3 * len(episodes) + 3) // 4,
        )
    adjusted = 0.0
    for rank, arm in enumerate(sorted(contrasts, key=lambda a: contrasts[a]["p"])):
        c = contrasts[arm]
        adjusted = max(adjusted, min(1.0, (2 - rank) * c["p"]))
        c["holm_p"], c["signal"] = adjusted, bool(c["wins"] and adjusted <= 0.05)
    return dict(
        contrasts=contrasts,
        calibrated=all(c["coverage"] and not c["signal"] for c in contrasts.values()),
    )


def pilot_reading(records, episodes, *, deterministic):
    expected = {
        (e.episode_id, a, t.index) for e in episodes for a in "RNTQ" for t in e.turns
    }
    actual = {(r["episode_id"], r["arm"], r["turn"]) for r in records}
    if len(actual) != len(records) or not actual <= expected:
        raise ValueError("duplicate/unregistered records")
    metrics = old.execution_summary(records)
    failures = []
    if actual != expected or len(expected) != 512:
        failures.append("incomplete 512-record accounting")
    if not deterministic:
        failures.append("determinism")
    for a, m in metrics.items():
        if m["executing_lanes"] != 8:
            failures.append(a + " execution<8/8")
        surviving = sum(
            r["arm"] == a
            and r["execution"].get("syntax_type") in ("IndentationError", "TabError")
            for r in records
        )
        m["surviving_indentation_errors"] = surviving
        m["repairs_used"] = sum(r["repairs_used"] for r in records if r["arm"] == a)
        if surviving:
            failures.append(a + " surviving indentation SyntaxError")
    endpoint = ep.primary(records, episodes)
    if sum(f["n"] > 0 for f in endpoint["families"].values()) < 2:
        failures.append("primary<2 nonzero families")
    return dict(
        reading="FIX-CONFIRMED" if not failures else "STOP",
        failures=failures,
        per_arm=metrics,
        primary=endpoint,
        harm_calibration=harm(records, episodes),
    )


def larger_reading(records, episodes, q_ids, *, cpu_control, calibrated):
    # Reuse the unchanged accounting and primary, replacing ONLY the old harm gate.
    result = ep.larger_reading(records, episodes, q_ids, cpu_control=cpu_control)
    result["failures"] = [
        f
        for f in result["failures"]
        if f != "R episode breakage exceeds N by more than one"
    ]
    result["harm"] = harm(records, episodes)
    if not calibrated or not result["harm"]["calibrated"]:
        result["failures"].append("harm calibration, coverage or conditional excess")
    result["repairs_used"] = {
        a: sum(r["repairs_used"] for r in records if r["arm"] == a) for a in "RNTQ"
    }
    result["reading"] = (
        "INCOMPLETE"
        if not result["complete"]
        else "FAIL"
        if result["failures"]
        else "PASS"
    )
    return result

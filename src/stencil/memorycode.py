"""MemoryCode-derived automatic-maintenance evaluation.

Contract: results/memorycode-derived/CONTRACT.md.

Pure-Python helpers: item enumeration, native-format prompt rendering, label-independent
candidate sentences, the common reminder renderer with newest-first packing, the
label-derived oracle live set, the frozen FOCUS-3 `auto` adapter, and the vendored
official checker. Imports perform no work; the vendored evaluator is loaded lazily.
"""

from __future__ import annotations

import importlib.util
import json
import random
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor" / "memorycode"
DATASET = VENDOR / "dataset"
HEADER = "Earlier mentor instructions restated verbatim:"
BUDGET = 256
MAX_PROMPT_TOKENS = 3584
OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
DEFAULT_TASK = "MAIN"
ARMS = ("history", "restate_all", "auto", "oracle")

PROMPT = (
    "This is a thread of dialogues between you and your mentor {mentor}:\n {thread} \n"
    "{reminder}Based on information provided, write a {query}. Do not provide example "
    "usage. You must follow all the latest coding guidelines provided by your mentor, "
    "including any possible updates."
)


# ----------------------------------------------------------------------------- data


def load_topics() -> dict:
    return json.loads((VENDOR / "topics.json").read_text())


def dialogue_ids() -> list[int]:
    return sorted(int(p.stem.split("_")[1]) for p in DATASET.glob("dialogue_*.json"))


def load_dialogue(did: int) -> dict:
    return json.loads((DATASET / f"dialogue_{did}.json").read_text())


def instruction_ids(dialogue: dict, s: int) -> list[tuple[int, int]]:
    """Live (pivot, update) pairs at session ``s``; ``[-1]`` means none."""
    out = []
    for entry in dialogue["instructions"][s]:
        if isinstance(entry, list) and len(entry) == 2:
            out.append((int(entry[0]), int(entry[1])))
    return out


def has_instruction(session: dict) -> bool:
    return any("instruction" in t for t in session["type"])


# ------------------------------------------------------------------------ rendering


def thread_text(dialogue: dict, sessions: list[int]) -> str:
    return "".join(
        f"\n\n Session {i} \n\n" + dialogue["sessions"][i]["text"] for i in sessions
    )


def chat_prompt(user_text: str) -> str:
    return f"<|im_start|>user\n{user_text}<|im_end|>\n" + OPENER


def user_message(dialogue: dict, s: int, query: str, arm: str, reminder: str) -> str:
    mentor = dialogue["context"]["mentor"]
    sessions = list(range(s + 1)) if arm == "history" else [s]
    block = reminder + "\n\n" if reminder else ""
    return PROMPT.format(
        mentor=mentor,
        thread=thread_text(dialogue, sessions),
        reminder=block,
        query=query,
    )


def render_reminder(sentences: list[str]) -> str:
    if not sentences:
        return ""
    return HEADER + "\n" + "\n".join(f"- {s}" for s in sentences)


def pack_newest_first(
    ordered: list[str], tokenizer, budget: int = BUDGET
) -> tuple[list[str], int]:
    """``ordered`` is chronological. Walk newest-first, stop at the first sentence that
    does not fit; return the kept sentences chronologically and the rendered tokens."""
    kept: list[str] = []
    for sentence in reversed(ordered):
        trial = [sentence] + kept
        if len(tokenizer.encode(render_reminder(trial)).ids) > budget:
            break
        kept = trial
    return kept, (len(tokenizer.encode(render_reminder(kept)).ids) if kept else 0)


# --------------------------------------------------------------------- candidates


def speaker_lines(dialogue: dict, s: int) -> list[tuple[str, str]]:
    """(speaker, line) for session ``s``; speaker is 'mentor', 'mentee' or 'other'."""
    mentor = dialogue["context"]["mentor"]
    mentee = dialogue["context"]["mentee"]
    out = []
    for raw in dialogue["sessions"][s]["text"].split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z][A-Za-z .'-]*?):\s*(.*)$", line)
        if m and m[1].strip() == mentor:
            out.append(("mentor", m[2].strip()))
        elif m and m[1].strip() == mentee:
            out.append(("mentee", m[2].strip()))
        else:
            out.append(("other", line))
    return out


def mentor_sentences(dialogue: dict, s: int) -> list[dict]:
    """Every mentor sentence of sessions 0..s-1, chronological, label-independent."""
    from stencil.focus3 import sentences

    out = []
    for i in range(s):
        for line_index, (speaker, line) in enumerate(speaker_lines(dialogue, i)):
            if speaker != "mentor":
                continue
            for k, (_, sentence) in enumerate(sentences(line)):
                out.append(
                    {"session": i, "line": line_index, "index": k, "text": sentence}
                )
    return out


# ------------------------------------------------------------------------- oracle


def oracle_sentences(dialogue: dict, s: int, topics: dict) -> list[str]:
    """Label-derived live instruction texts at session ``s``, ordered by the session
    in which each (pivot, update) first became live."""
    live = instruction_ids(dialogue, s)
    first_seen = {}
    for i in range(s + 1):
        for pair in instruction_ids(dialogue, i):
            first_seen.setdefault(pair, i)
    ordered = sorted(live, key=lambda pair: (first_seen.get(pair, s), pair))
    by_id = {int(t["id"]): t for t in topics["instructions"]}
    return [by_id[p]["text"][u] for p, u in ordered]


# --------------------------------------------------------------------------- auto


def sentence_windows(line: str, width: int = 4) -> list[str]:
    from stencil.focus3 import sentences

    spans = [span for _, span in sentences(line)]
    if len(spans) <= width:
        return [line]
    return [" ".join(spans[i : i + width]) for i in range(0, len(spans), width)]


def auto_live(dialogue: dict, s: int, runtime) -> dict:
    """Run the frozen FOCUS-3 runtime over mentor lines of sessions 0..s-1.

    Every window of a mentor line is one ``update`` call with its OWN turn index
    (CONTRACT.md amendment 2): row ids are ``turn:start`` with ``start`` relative
    to the window text, so windows sharing a turn collided and silently dropped
    rows (Astra round 3, 2026-09-11). ``turns`` maps turn -> (session, line, window).
    """
    runtime.task = DEFAULT_TASK
    admitted, relations, overflow, calls = 0, 0, 0, 0
    turn = 0
    turns: dict[int, dict] = {}
    for i in range(s):
        for line_index, (speaker, line) in enumerate(speaker_lines(dialogue, i)):
            if speaker != "mentor":
                continue
            for w, window in enumerate(sentence_windows(line)):
                turn += 1
                turns[turn] = {"session": i, "line": line_index, "window": w}
                trace = runtime.update(window, turn, role="user")
                calls += 1
                admitted += sum(1 for a in trace["admissions"] if a.get("accepted"))
                relations += sum(
                    1 for a in trace["applied"] if a.get("label") != "admit"
                )
                overflow += int(bool(trace.get("overflow")))
    # Live set = live rows in the default task scope or global scope, any kind
    # (CONTRACT.md amendment 2: ``Register.live(task, kind)`` also filters on
    # kind, which MemoryCode text does not use meaningfully).
    rows = sorted(
        (
            r
            for r in runtime.register.rows
            if r.status == "live" and r.scope in ("*", DEFAULT_TASK)
        ),
        key=lambda r: (r.provenance_turn, r.span_start),
    )
    return {
        "sentences": [r.text for r in rows],
        "admitted": admitted,
        "relations_applied": relations,
        "overflow": overflow,
        "update_calls": calls,
        "rows": runtime.register.snapshot(),
        "turns": turns,
    }


def frozen_classifier():
    """The registered frozen heads: ft admission + relations-v2 seed0 lifecycle."""
    from stencil.focus3 import FrozenClassifier

    path = ROOT / "data/classifier/model/relations-v2/seed0"
    frozen = json.loads((path / "thresholds.json").read_text())
    return FrozenClassifier(
        relations_path=path,
        thresholds=frozen["thresholds"],
        admission_bound=frozen.get("admission_bound", "legacy_none"),
        admission_path=ROOT / "data/classifier/model/ft",
    )


# -------------------------------------------------------------------------- checker


def vendored_checker():
    """Load the official ``compute_score`` without the ``fire`` dependency."""
    code_dir = VENDOR / "code"
    if "fire" not in sys.modules:
        sys.modules["fire"] = types.ModuleType("fire")
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    spec = importlib.util.spec_from_file_location(
        "memorycode_evaluate", code_dir / "evaluate_model_output.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.compute_score


CLASS_FAMILIES = {
    "class",
    "class decorator",
    "method",
    "method annotation",
    "method decorator",
    "method docstring",
    "method assert",
    "method try",
    "attribute",
}
FUNCTION_FAMILIES = {
    "function",
    "function argument",
    "function annotation",
    "function decorator",
    "function docstring",
    "function assert",
    "function try",
}
ALWAYS_FAMILIES = {"variable", "import", "comment"}


def required_structure(query: str) -> list[str]:
    """Parent objects the task query REQUIRES, by whole-word match (Astra round 4:
    "classifies" must not require a class): a class when it names a class or
    method, otherwise a function."""
    q = query.lower()
    if re.search(r"\b(class|classes|method|methods)\b", q):
        return ["class"]
    return ["function"]


def required_families(query: str, families: list[str]) -> list[str]:
    """Families whose parent object the task query REQUIRES, frozen before any
    generation (CONTRACT.md amendment 3): class-side families when the query
    names a class or method; function-side families when it names a function or
    names neither; variable/import/comment always. An omitted required parent
    object is a failure, never "inapplicable"."""
    structure = required_structure(query)
    classy = "class" in structure
    functiony = "function" in structure
    out = []
    for family in families:
        if family in ALWAYS_FAMILIES:
            out.append(family)
        elif family in CLASS_FAMILIES and classy:
            out.append(family)
        elif family in FUNCTION_FAMILIES and functiony:
            out.append(family)
    return sorted(set(out))


def score_generation(
    text: str,
    regexes: list,
    compute_score,
    required: list[str] | None = None,
    structure: list[str] | None = None,
) -> dict:
    """Per-family scores for one generation. ``None`` = parent object absent; with
    ``required`` (frozen from the query) an absent REQUIRED parent scores 0.0, and
    with ``structure`` (frozen from the query) a generation lacking the required
    class / function is strict-FALSE whatever its convention scores."""
    scores = []
    for obj, regex in regexes:
        score = compute_score(text, obj, regex)
        if score is None and required is not None and str(obj) in required:
            score = 0.0
        scores.append(score)
    applicable = [s for s in scores if s is not None]
    structure_present = all(
        compute_score(text, obj, True) is not None for obj in (structure or [])
    )
    strict = all(s == 1.0 for s in applicable) if applicable else None
    if strict is not None and not structure_present:
        strict = False
    return {
        "per_family": scores,
        "structure_present": structure_present,
        "strict": strict,
        "fraction": (sum(applicable) / len(applicable)) if applicable else None,
    }


# ---------------------------------------------------------------------------- items


def enumerate_items(tokenizer, ids: list[int] | None = None) -> list[dict]:
    items = []
    for did in ids if ids is not None else dialogue_ids():
        dialogue = load_dialogue(did)
        for s, session in enumerate(dialogue["sessions"]):
            if s == 0 or not session["history_regex"]:
                continue
            if not any(has_instruction(dialogue["sessions"][i]) for i in range(s)):
                continue
            query = session["history_eval_query"][0]
            prompt = chat_prompt(user_message(dialogue, s, query, "history", ""))
            tokens = len(tokenizer.encode(prompt).ids)
            if tokens > MAX_PROMPT_TOKENS:
                continue
            families = sorted({str(obj) for obj, _ in session["history_regex"]})
            items.append(
                {
                    "dialogue": did,
                    "session": s,
                    "queries": list(session["history_eval_query"]),
                    "required": {
                        q: required_families(q, families)
                        for q in session["history_eval_query"]
                    },
                    "structure": {
                        q: required_structure(q) for q in session["history_eval_query"]
                    },
                    "history_regex": session["history_regex"],
                    "history_prompt_tokens": tokens,
                    "families": families,
                }
            )
    return items


def split_items(items: list[dict], n_setup: int = 16, n_screen: int = 64) -> dict:
    by_dialogue: dict[int, list[dict]] = {}
    for item in items:
        by_dialogue.setdefault(item["dialogue"], []).append(item)
    dialogues = sorted(by_dialogue)
    random.Random(0).shuffle(dialogues)
    chosen = [by_dialogue[d][0] for d in dialogues]
    return {
        "setup": chosen[:n_setup],
        "screen": chosen[n_setup : n_setup + n_screen],
        "n_eligible_items": len(items),
        "n_eligible_dialogues": len(dialogues),
    }

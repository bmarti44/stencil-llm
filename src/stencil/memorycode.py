"""MemoryCode-derived automatic-maintenance evaluation.

Contract: results/memorycode-derived/CONTRACT.md.

Pure-Python helpers: item enumeration, native-format prompt rendering, label-independent
candidate sentences, the common reminder renderer with newest-first packing, the
label-derived oracle live set, the frozen FOCUS-3 `auto` adapter, and the vendored
official checker. Imports perform no work; the vendored evaluator is loaded lazily.
"""

from __future__ import annotations

import ast
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
WINDOW = 3584  # Exp 4 imposed prompt budget W (plan rev 7.1 section H)
LONG_HEADER = "Earlier instructions still in force:"
DEGENERATE_REP4 = 0.5
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


def instruction_events(dialogue: dict, s: int) -> list[tuple[int, int]]:
    """(pivot, update) pairs INTRODUCED OR UPDATED in session ``s`` (the vendored
    generator's ``instruction_template``: per-session events, ``[-1]`` on filler
    sessions; vendor/memorycode/code/generate_template.py)."""
    out = []
    for entry in dialogue["instructions"][s]:
        if isinstance(entry, list) and len(entry) == 2:
            out.append((int(entry[0]), int(entry[1])))
    return out


def live_instructions(dialogue: dict, s: int) -> list[tuple[int, int]]:
    """Live (pivot, update) pairs AT session ``s``: replay the events of sessions
    0..s keeping the latest update per pivot, ordered by the session in which the
    pivot was first introduced (instrument repair 2026-09-12: the previous reading
    took the current session's events as the live set, which emptied the oracle on
    filler sessions and dropped every earlier convention)."""
    latest: dict[int, int] = {}
    first: dict[int, int] = {}
    for i in range(s + 1):
        for p, u in instruction_events(dialogue, i):
            latest[p] = u
            first.setdefault(p, i)
    return sorted(latest.items(), key=lambda pu: (first[pu[0]], pu[0]))


def instruction_ids(dialogue: dict, s: int) -> list[tuple[int, int]]:
    """Backwards-compatible alias of :func:`live_instructions`."""
    return live_instructions(dialogue, s)


def live_regexes(dialogue: dict, s: int, topics: dict) -> list[list]:
    """The [object, regex] checks implied by the live set; must equal the dataset's
    ``history_regex`` of session ``s`` as a multiset (verified in tests)."""
    by_id = {int(t["id"]): t for t in topics["instructions"]}
    return [by_id[p]["regex"][u] for p, u in live_instructions(dialogue, s)]


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
        speaker, content = split_speaker(line, mentor, mentee)
        out.append((speaker, content))
    return out


def split_speaker(line: str, mentor: str, mentee: str) -> tuple[str, str]:
    """Name-based speaker split (instrument repair 2026-09-12: the previous ASCII
    regex missed names such as 'Jean-Aimé', turning every mentor line of those
    dialogues into 'other' and emptying the candidate set)."""
    for speaker, name in (("mentor", mentor), ("mentee", mentee)):
        prefix = f"{name}:"
        if line.startswith(prefix):
            return speaker, line[len(prefix) :].strip()
    return "other", line


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
    by_id = {int(t["id"]): t for t in topics["instructions"]}
    return [by_id[p]["text"][u] for p, u in live_instructions(dialogue, s)]


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


# ------------------------------------------------------------- Exp 4: LONG cohort


def long_items(tokenizer, ids: list[int] | None = None) -> list[dict]:
    """The 212 items whose full history prompt exceeds MAX_PROMPT_TOKENS; one
    generation each (the first ``history_eval_query``)."""
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
            if tokens <= MAX_PROMPT_TOKENS:
                continue
            families = sorted({str(obj) for obj, _ in session["history_regex"]})
            items.append(
                {
                    "dialogue": did,
                    "session": s,
                    "queries": [query],
                    "required": {query: required_families(query, families)},
                    "structure": {query: required_structure(query)},
                    "history_regex": session["history_regex"],
                    "history_prompt_tokens": tokens,
                    "families": families,
                }
            )
    return items


def split_long(items: list[dict], n_setup: int = 16, n_screen: int = 128) -> dict:
    """Seed-1 split by dialogue: SETUP-LONG, SCREEN-LONG, reserve (never opened)."""
    by_dialogue: dict[int, list[dict]] = {}
    for item in items:
        by_dialogue.setdefault(item["dialogue"], []).append(item)
    dialogues = sorted(by_dialogue)
    random.Random(1).shuffle(dialogues)
    chosen = [by_dialogue[d][0] for d in dialogues]
    return {
        "setup_long": chosen[:n_setup],
        "screen_long": chosen[n_setup : n_setup + n_screen],
        "reserve": len(chosen) - n_setup - n_screen,
        "n_long_items": len(items),
    }


def render_long_reminder(sentences: list[str]) -> str:
    if not sentences:
        return ""
    return LONG_HEADER + "\n" + "\n".join(f"- {s}" for s in sentences)


def pack_long(
    ordered: list[str], tokenizer, budget: int = BUDGET
) -> tuple[list[str], int]:
    kept: list[str] = []
    for sentence in reversed(ordered):
        trial = [sentence] + kept
        if len(tokenizer.encode(render_long_reminder(trial)).ids) > budget:
            break
        kept = trial
    used = len(tokenizer.encode(render_long_reminder(kept)).ids) if kept else 0
    return kept, used


def build_long_prompt(
    dialogue: dict, s: int, query: str, tokenizer, reminder: str, window: int = WINDOW
) -> dict:
    """Native-format prompt whose thread is the NEWEST tokens of the whole session
    text, truncated at a token boundary so the complete prompt has at most
    ``window`` tokens; the reminder (if any) is paid for by a shorter thread.
    Retokenisation at the cut can move the count by a token or two; the loop
    trims until the prompt fits and the actual length is returned."""
    mentor = dialogue["context"]["mentor"]
    block = reminder + "\n\n" if reminder else ""
    head = f"This is a thread of dialogues between you and your mentor {mentor}:\n"
    tail = (
        f" \n{block}Based on information provided, write a {query}. Do not provide "
        "example usage. You must follow all the latest coding guidelines provided by "
        "your mentor, including any possible updates."
    )
    frame_tokens = len(tokenizer.encode(chat_prompt(head + tail)).ids)
    thread_ids = tokenizer.encode(thread_text(dialogue, list(range(s + 1)))).ids
    budget = max(window - frame_tokens, 0)
    dropped = 0
    for _ in range(8):
        keep = thread_ids[len(thread_ids) - budget :] if budget else []
        thread = tokenizer.decode(keep, skip_special_tokens=False)
        prompt = chat_prompt(head + thread + tail)
        actual = len(tokenizer.encode(prompt).ids)
        if actual <= window:
            break
        budget -= actual - window
        dropped += 1
    if actual > window:
        raise ValueError(f"prompt does not fit W={window} after retrims: {actual}")
    full = thread_text(dialogue, list(range(s + 1)))
    return {
        "prompt": prompt,
        "prompt_tokens": actual,
        "thread_tokens_kept": len(keep),
        "thread_tokens_total": len(thread_ids),
        "frame_tokens": frame_tokens,
        "retrim_rounds": dropped,
        "thread_text_kept": thread,
        "cut_chars": max(len(full) - len(thread), 0),
    }


def repeated_4gram_fraction(ids: list[int]) -> float:
    if len(ids) < 8:
        return 0.0
    grams = [tuple(ids[i : i + 4]) for i in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def extract_code(text: str) -> str:
    """The official checker's extraction (``evaluate_model_output.extract_code``)."""
    match = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if not match:
        match = re.findall(r"```(.*?)```", text, re.DOTALL)
    return match[0] if match else text


def output_failures(
    text: str, ids: list[int], truncated: bool, timed_out: bool = False
) -> dict:
    """Output-failure guard columns (plan rev 7.1 H; Exp 4 amendment 2): invalid =
    no parsable code, truncated = hit the cap, degenerate = 4-gram repetition above
    0.5, timed_out = the generation deadline was exceeded (a terminal failure)."""
    code = extract_code(text)
    try:
        ast.parse(code)
        invalid = not code.strip()
    except (SyntaxError, ValueError):
        invalid = True
    return {
        "invalid": invalid,
        "truncated": truncated,
        "degenerate": repeated_4gram_fraction(ids) > DEGENERATE_REP4,
        "timed_out": timed_out,
        "repetition_4gram": repeated_4gram_fraction(ids),
    }


FAILURE_COLUMNS = ("invalid", "truncated", "degenerate", "timed_out")


def any_failure(failures: dict) -> bool:
    return any(failures.get(k, False) for k in FAILURE_COLUMNS)


def evicted_mentor_sentences(
    dialogue: dict, s: int, thread_kept: str | None = None, cut: int | None = None
) -> list[str]:
    """Exp 4 primary policy (registration amendment 1): every mentor sentence of
    sessions 0..s-1 whose text lies entirely BEFORE the base window's cut, i.e. the
    truncated-away region, chronological (the caller packs newest-first). Label-free,
    zero-parameter; the analogue of Exp 1's ``role_echo_only`` over the evicted
    region. ``cut`` is the character offset of the window start in the full thread
    (``build_long_prompt(...)["cut_chars"]``); ``thread_kept`` is the legacy way to
    derive it from the retained text's length."""
    from stencil.focus3 import sentences

    full = thread_text(dialogue, list(range(s + 1)))
    if cut is None:
        assert thread_kept is not None
        cut = max(len(full) - len(thread_kept), 0)
    out = []
    for i in range(s):
        session_start = full.index(f"\n\n Session {i} \n\n")
        body_start = session_start + len(f"\n\n Session {i} \n\n")
        text = dialogue["sessions"][i]["text"]
        offset = 0
        for speaker, line in speaker_lines(dialogue, i):
            position = text.find(line, offset)
            if position < 0:
                continue
            offset = position + len(line)
            if speaker != "mentor":
                continue
            for start, sentence in sentences(line):
                if body_start + position + start + len(sentence) <= cut:
                    out.append(sentence)
    return out


# ------------------------------------------------------------ artifact parity


def focus_session_messages(dialogue: dict, s: int) -> list[tuple[str, str, str]]:
    """(role, text, rendered) messages that rebuild ``thread_text(dialogue, 0..s)``
    byte for byte inside the published package's ``Session``: mentor lines are
    ``user`` (instruction role, text = the line's content), every other line and
    the session separators are stored only."""
    mentor = dialogue["context"]["mentor"]
    out = []
    for i in range(s + 1):
        out.append(("separator", "", f"\n\n Session {i} \n\n"))
        lines = dialogue["sessions"][i]["text"].split("\n")
        mentee = dialogue["context"]["mentee"]
        for j, raw in enumerate(lines):
            rendered = raw + ("\n" if j < len(lines) - 1 else "")
            speaker, content = split_speaker(raw.strip(), mentor, mentee)
            if speaker == "mentor" and content:
                out.append(("user", content, rendered))
            else:
                out.append(("other", "", rendered))
    return out


def long_request(dialogue: dict, query: str) -> tuple[str, str, str]:
    """(head, separator, request) of the native LONG frame for the package."""
    mentor = dialogue["context"]["mentor"]
    head = f"This is a thread of dialogues between you and your mentor {mentor}:\n"
    request = (
        f"Based on information provided, write a {query}. Do not provide example "
        "usage. You must follow all the latest coding guidelines provided by your "
        "mentor, including any possible updates."
    )
    return head, " \n", request

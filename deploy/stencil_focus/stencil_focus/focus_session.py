"""Session-memory handling for stencil-focus: pure text, no model.

The modification evaluated in Exp 4 (results/memorycode-long/REGISTRATION.md,
amendment 1): under an imposed prompt budget the conversation window keeps the
NEWEST tokens; with ``focus`` on, every instruction-role sentence that was
truncated away is restated newest-first, packed to ``budget`` tokens including the
header, and inserted immediately before the request, with the window shortened so
the complete prompt has the same token count as the plain window. Zero parameters.
"""

from __future__ import annotations

import re
from collections.abc import Callable

HEADER = "Earlier instructions still in force:"
OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
WINDOW = 3584
BUDGET = 256
INSTRUCTION_ROLES = ("user",)


def sentences(text: str) -> list[tuple[int, str]]:
    """Verbatim sentence spans (offset, text), retaining punctuation."""
    return [
        (m.start(), m.group()) for m in re.finditer(r"\S.*?(?:[.!?](?=\s|$)|$)", text)
    ]


def chat_prompt(user_text: str) -> str:
    """Qwen3 chat template, one user turn, thinking disabled (non-thinking mode)."""
    return f"<|im_start|>user\n{user_text}<|im_end|>\n" + OPENER


def render_reminder(kept: list[str]) -> str:
    if not kept:
        return ""
    return HEADER + "\n" + "\n".join(f"- {s}" for s in kept)


def pack_newest_first(
    ordered: list[str], encode: Callable[[str], list[int]], budget: int = BUDGET
) -> tuple[list[str], int]:
    """Keep the newest sentences of ``ordered`` (chronological) whose rendered
    reminder, header included, fits ``budget`` tokens; chronological order kept."""
    kept: list[str] = []
    for sentence in reversed(ordered):
        trial = [sentence] + kept
        if len(encode(render_reminder(trial))) > budget:
            break
        kept = trial
    used = len(encode(render_reminder(kept))) if kept else 0
    return kept, used


def default_format(role: str, text: str) -> str:
    return f"{role}: {text}\n"


class Session:
    """Ordered conversation state for one session; isolated per object.

    ``add_message(role, text, rendered=None)`` appends a message. ``rendered`` is the
    exact text the message contributes to the thread (default ``format(role, text)``)
    and must contain ``text`` verbatim so instruction sentences keep their offsets.
    Messages whose role is in ``instruction_roles`` feed the restatement; every other
    role is stored only.
    """

    def __init__(
        self,
        tokenizer,
        focus: bool = True,
        window: int = WINDOW,
        budget: int = BUDGET,
        format: Callable[[str, str], str] = default_format,
        instruction_roles: tuple[str, ...] = INSTRUCTION_ROLES,
    ) -> None:
        self.tokenizer = tokenizer
        self.focus = focus
        self.window = window
        self.budget = budget
        self.format = format
        self.instruction_roles = instruction_roles
        self.messages: list[dict] = []
        self.last: dict | None = None

    # -- state ---------------------------------------------------------------
    def reset(self) -> None:
        self.messages = []
        self.last = None

    def add_message(self, role: str, text: str, rendered: str | None = None) -> None:
        if rendered is None:
            rendered = self.format(role, text)
        if text and text not in rendered:
            raise ValueError("rendered text must contain the message text verbatim")
        self.messages.append({"role": role, "text": text, "rendered": rendered})

    def thread(self) -> str:
        return "".join(m["rendered"] for m in self.messages)

    # -- tokens --------------------------------------------------------------
    def encode(self, text: str) -> list[int]:
        return self.tokenizer(text, add_special_tokens=False)["input_ids"]

    def decode(self, ids: list[int]) -> str:
        return self.tokenizer.decode(ids, skip_special_tokens=False)

    # -- instruction sentences with absolute thread offsets -------------------
    def instruction_spans(self) -> list[tuple[int, int, str]]:
        out = []
        offset = 0
        for m in self.messages:
            if m["role"] in self.instruction_roles and m["text"]:
                inner = m["rendered"].find(m["text"])
                base = offset + inner
                for start, sentence in sentences(m["text"]):
                    out.append((base + start, base + start + len(sentence), sentence))
            offset += len(m["rendered"])
        return out

    # -- prompt --------------------------------------------------------------
    def _fit(self, head: str, thread: str, separator: str, reminder: str, request: str):
        block = reminder + "\n\n" if reminder else ""
        tail = separator + block + request
        frame_tokens = len(self.encode(chat_prompt(head + tail)))
        thread_ids = self.encode(thread)
        budget = max(self.window - frame_tokens, 0)
        rounds = 0
        keep: list[int] = []
        for _ in range(8):
            keep = thread_ids[len(thread_ids) - budget :] if budget else []
            kept_text = self.decode(keep)
            prompt = chat_prompt(head + kept_text + tail)
            actual = len(self.encode(prompt))
            if actual <= self.window:
                break
            budget -= actual - self.window
            rounds += 1
        return {
            "prompt": prompt,
            "prompt_tokens": actual,
            "thread_tokens_kept": len(keep),
            "thread_tokens_total": len(thread_ids),
            "thread_text_kept": kept_text,
            "frame_tokens": frame_tokens,
            "retrim_rounds": rounds,
        }

    def build_prompt(
        self, request: str, head: str = "", separator: str = "\n\n"
    ) -> str:
        """The exact prompt string for ``request`` (chat template applied)."""
        thread = self.thread()
        base = self._fit(head, thread, separator, "", request)
        record = {"focus": self.focus, "base_prompt_tokens": base["prompt_tokens"]}
        if not self.focus:
            record.update(base, reminder="", reminder_tokens=0, kept_sentences=0)
            self.last = record
            return base["prompt"]
        cut = max(len(thread) - len(base["thread_text_kept"]), 0)
        evicted = [s for (_, end, s) in self.instruction_spans() if end <= cut]
        kept, used = pack_newest_first(evicted, self.encode, self.budget)
        reminder = render_reminder(kept)
        built = self._fit(head, thread, separator, reminder, request)
        record.update(
            built,
            reminder=reminder,
            reminder_tokens=used,
            evicted_sentences=len(evicted),
            kept_sentences=len(kept),
        )
        self.last = record
        return built["prompt"]

"""Frozen spec-v2 sentence classifier used by evaluation-only harnesses."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path


def scoring_pair_token_count(tokenizer, context: str, text: str, role: str) -> int:
    """Measure the exact untruncated encoder pair used by the scorer."""
    encoded = tokenizer(
        context if context else "(no context)",
        f"[{role}] {text}",
        truncation=False,
    )
    return len(encoded["input_ids"])


def split_sentence_spans(text: str) -> list[tuple[int, int]]:
    """Return the frozen selector-v2 sentence spans within ``text``."""
    out = []
    start = 0
    i = 0
    n = len(text)
    single_quote = double_quote = False
    while i < n:
        char = text[i]
        if char == '"':
            double_quote = not double_quote
        elif char == "'":
            if not single_quote and (i == 0 or not text[i - 1].isalnum()):
                single_quote = True
            elif single_quote and (i + 1 >= n or not text[i + 1].isalnum()):
                single_quote = False
        if char in ".!?":
            abbreviation = (
                i >= 1
                and text[i - 1].isalpha()
                and text[i - 1].isupper()
                and (i < 2 or not text[i - 2].isalpha())
            )
            j = i + 1
            while j < n and text[j] in ".!?":
                j += 1
            k = j
            next_single, next_double = single_quote, double_quote
            while k < n and text[k] in "\"')":
                if text[k] == '"':
                    next_double = not next_double
                elif text[k] == "'" and next_single:
                    next_single = False
                k += 1
            if (
                not abbreviation
                and not next_single
                and not next_double
                and (k >= n or text[k].isspace())
            ):
                out.append((start, k))
                single_quote, double_quote = next_single, next_double
                start = k
                while start < n and text[start].isspace():
                    start += 1
                i = start
                continue
        i += 1
    if start < n:
        out.append((start, n))
    return [
        (begin, end)
        for begin, end in out
        if end > begin and len(re.findall(r"[A-Za-z]", text[begin:end])) >= 2
    ]


class ClassifierScorer:
    """CPU-only wrapper for the registered fine-tuned encoder and head."""

    def __init__(self, model_dir: str | Path) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        model_dir = Path(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir / "encoder")
        self.encoder = AutoModel.from_pretrained(model_dir / "encoder").cpu().eval()
        saved = torch.load(model_dir / "head.pt", map_location="cpu", weights_only=True)
        self.roles = list(saved["roles"])
        self.labels = list(saved["labels"])
        self.head = torch.nn.Sequential(
            torch.nn.Dropout(0.1),
            torch.nn.Linear(int(saved["hidden"]) + len(self.roles), len(self.labels)),
        )
        self.head.load_state_dict(saved["head"])
        self.head.eval()
        self.scorer_truncated_candidates = 0

    def __call__(
        self,
        texts: Sequence[str],
        *,
        role: str,
        contexts: Sequence[str],
    ) -> list[float]:
        """Return P(rule)+P(fact), using empty context exactly as registered."""
        import torch

        if role not in self.roles:
            raise ValueError(f"unknown role: {role}")
        if len(texts) != len(contexts):
            raise ValueError("texts and contexts must have equal length")
        probabilities: list[float] = []
        if not hasattr(self, "scorer_truncated_candidates"):
            self.scorer_truncated_candidates = 0
        with torch.no_grad():
            for start in range(0, len(texts), 64):
                chunk = list(texts[start : start + 64])
                chunk_contexts = list(contexts[start : start + 64])
                for context, value in zip(chunk_contexts, chunk, strict=True):
                    if scoring_pair_token_count(
                        self.tokenizer, context, value, role
                    ) > 192:
                        self.scorer_truncated_candidates += 1
                batch = self.tokenizer(
                    [value if value else "(no context)" for value in chunk_contexts],
                    [f"[{role}] {value}" for value in chunk],
                    padding=True,
                    truncation="longest_first",
                    max_length=192,
                    return_tensors="pt",
                )
                hidden = self.encoder(**batch).last_hidden_state[:, 0]
                roles = torch.tensor(
                    [[float(role == candidate) for candidate in self.roles]]
                    * len(chunk)
                )
                probs = torch.softmax(
                    self.head(torch.cat([hidden, roles], dim=1)), dim=-1
                )
                keep = (
                    probs[:, self.labels.index("rule")]
                    + probs[:, self.labels.index("fact")]
                )
                probabilities.extend(float(value) for value in keep)
        return probabilities

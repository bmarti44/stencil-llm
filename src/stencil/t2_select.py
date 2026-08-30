# ruff: noqa: E501
"""MUST-2 candidate-set extraction shared by selector training and evaluation.

Extracted from scripts/t2_train_selector.py after the closing sol review found
that importing the training script for this one helper EXECUTED the training
script's top-level code, retraining and overwriting the recalibrated selector
checkpoint before every shakeout evaluated it (CRITICAL, 2026-08-30).
"""
import re

CAND_PATTERNS = {
    "prefix": [r"All function names must start with '(\w+)_'\.", r"Use the naming scheme (\w+)_\* for every function you define\."],
    "doc": [r"Every docstring must begin with the word '(\w+)'\."],
    "hint": [r"All function arguments must be type-hinted as (\w+)\."],
}


def candidate_spans(prompt_text, enc):
    """MUST-2: every obligation-like sentence, live or quoted."""
    cands = []  # (type, value, tok_span, char_start)
    for ty, pats in CAND_PATTERNS.items():
        for pat in pats:
            for match in re.finditer(pat, prompt_text):
                a, b = match.span()
                cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
                if cols:
                    cands.append((ty, match.group(1), (cols[0], cols[-1] + 1), a))
    return cands

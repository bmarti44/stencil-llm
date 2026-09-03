"""Frozen spec-v2 sentence classifier used by evaluation-only harnesses."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


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
        with torch.no_grad():
            for start in range(0, len(texts), 64):
                chunk = list(texts[start : start + 64])
                chunk_contexts = list(contexts[start : start + 64])
                batch = self.tokenizer(
                    [value if value else "(no context)" for value in chunk_contexts],
                    [f"[{role}] {value}" for value in chunk],
                    padding=True,
                    truncation="only_first",
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

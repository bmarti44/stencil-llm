"""Whole-message/candidate BGE admission detector; imports perform no work."""

from __future__ import annotations

import time
from pathlib import Path

from stencil.focus3 import sentences

BASE = "BAAI/bge-small-en-v1.5"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
LIMIT = 512


def candidates(row):
    return [dict(start=s, end=s + len(t), text=t) for s, t in sentences(row["message"])]


def pairing(row, span):
    return f"[{row['role']}] {row['message']}", span["text"]


def accepts(row, spans, probabilities, threshold):
    return [
        dict(s, scope="unknown", key="NEW", allocated_key=f"new:{i}")
        for i, (s, p) in enumerate(zip(spans, probabilities, strict=True))
        if row["role"] == "user" and p is not None and p >= threshold
    ]


class Detector:
    def __init__(self, path=None, device="cpu", threshold=None):
        import json

        import torch
        from safetensors.torch import load_file
        from transformers import AutoModel, AutoTokenizer

        self.torch, self.device = torch, device
        source = Path(path) / "encoder" if path else BASE
        kw = dict(local_files_only=True)
        if not path:
            kw["revision"] = REVISION
        self.tok = AutoTokenizer.from_pretrained(source, **kw)
        self.enc = AutoModel.from_pretrained(source, **kw).to(device)
        self.head = torch.nn.Sequential(
            torch.nn.Dropout(0.1), torch.nn.Linear(self.enc.config.hidden_size, 2)
        ).to(device)
        if path:
            self.head.load_state_dict(load_file(str(Path(path) / "head.safetensors")))
            threshold = json.loads((Path(path) / "threshold.json").read_text())[
                "threshold"
            ]
        self.threshold = threshold
        self.enc.eval()
        self.head.eval()

    def encode(self, row):
        spans = candidates(row)
        tokens = [self.tok(*pairing(row, s), truncation=False) for s in spans]
        return spans, tokens

    def infer(self, row):
        start = time.monotonic()
        spans, tokens = self.encode(row)
        valid = [i for i, t in enumerate(tokens) if len(t["input_ids"]) <= LIMIT]
        probs = [None] * len(spans)
        self.enc.eval()
        self.head.eval()
        with self.torch.inference_mode():
            for start_idx in range(0, len(valid), 32):
                indices = valid[start_idx : start_idx + 32]
                batch = self.tok.pad(
                    [tokens[i] for i in indices], return_tensors="pt"
                ).to(self.device)
                logits = self.head(self.enc(**batch).last_hidden_state[:, 0])
                values = logits.double().softmax(-1)[:, 1].cpu().tolist()
                for i, p in zip(indices, values, strict=True):
                    probs[i] = p
        accepted = (
            accepts(row, spans, probs, self.threshold)
            if self.threshold is not None
            else []
        )
        return dict(
            accepted=accepted,
            spans=spans,
            probabilities=probs,
            token_counts=[len(t["input_ids"]) for t in tokens],
            seconds=time.monotonic() - start,
            role_guard=row["role"] != "user",
            overflow=sum(p is None for p in probs),
        )

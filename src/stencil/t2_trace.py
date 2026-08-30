# ruff: noqa: E501
"""PRESS-PLAN H4: T0.1 trace persistence.

Events and work records accumulate in memory and are written atomically
on close() (write to .partial, fsync-rename), with a content digest over
a canonical serialization — an unclosed writer leaves no loadable file,
so a crashed trace pass cannot masquerade as evidence."""
import hashlib
import io
import os

import torch


def _digest(payload) -> str:
    buf = io.BytesIO()
    torch.save(payload, buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()


class TraceWriter:
    def __init__(self, path):
        self.path = str(path)
        self.events = []
        self.works = []
        self.closed = False

    def add_event(self, event: dict):
        assert not self.closed
        self.events.append(event)

    def add_work(self, work: dict):
        assert not self.closed
        self.works.append(work)

    def close(self):
        assert not self.closed
        payload = {"events": self.events, "works": self.works}
        payload["digest"] = _digest({"events": self.events, "works": self.works})
        tmp = self.path + ".partial"
        torch.save(payload, tmp)
        os.replace(tmp, self.path)
        self.closed = True


def load_trace(path):
    p = str(path)
    if not os.path.exists(p):
        raise FileNotFoundError(f"no closed trace at {p} (a .partial file means the pass died mid-write)")
    tr = torch.load(p, map_location="cpu", weights_only=False)
    want = _digest({"events": tr["events"], "works": tr["works"]})
    if tr["digest"] != want:
        raise ValueError(f"trace digest mismatch at {p}: stored {tr['digest'][:12]} != recomputed {want[:12]}")
    return tr

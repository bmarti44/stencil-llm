# ruff: noqa: E501
"""EVF Phase E0 pilot — red/green TDD.

Fixture tests are hand-executed first (playbook): the divergence finder
fixtures below were computed by hand before src/stencil/evf.py existed.
GPU tests prove deterministic feature extraction (bitwise across runs).
"""
import json
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent


# --- divergence finder (pure, CPU) -----------------------------------------

def test_first_divergence_token_fixtures():
    from tokenizers import Tokenizer

    from stencil.evf import first_divergence
    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    # hand-executed: identical texts -> None
    assert first_divergence(tok, "The lake was calm.", "The lake was calm.") is None
    # hand-executed: "The lake was calm." vs "The lake was blue." share
    # "The lake was" -> ids diverge at the token covering "calm"/"blue".
    a, b = "The lake was calm.", "The lake was blue."
    ia, ib = tok.encode(a).ids, tok.encode(b).ids
    k = first_divergence(tok, a, b)
    assert k is not None and 0 < k <= min(len(ia), len(ib))
    assert ia[:k] == ib[:k] and (k == min(len(ia), len(ib)) or ia[k] != ib[k])
    # hand-executed: divergence at the very first token
    assert first_divergence(tok, "Alpha beta.", "Gamma beta.") == 0
    # one text a strict prefix of the other -> divergence at the shorter length
    p, q = "Same start here", "Same start here and more"
    assert first_divergence(tok, p, q) == len(tok.encode(p).ids)


def test_discordant_anatomy_counts():
    from stencil.evf import load_anatomy
    anat = load_anatomy(ROOT, arm="t30-b3")
    repairs = [r for r in anat if r["label"] == 1]
    regressions = [r for r in anat if r["label"] == 0]
    assert len(repairs) == 15 and len(regressions) == 12
    for r in anat:
        assert r["base_response"] and r["wave_response"]
        assert r["row"]["prompt"]  # joined with the cal-v45 dataset row
        assert r["base_adherent"] != r["wave_adherent"]
        assert r["label"] == int(r["wave_adherent"])


def test_concordant_controls():
    from stencil.evf import load_controls
    ctl = load_controls(ROOT, arm="t30-b3", n=30, seed=11)
    assert len(ctl) == 30
    assert all(c["base_adherent"] == c["wave_adherent"] for c in ctl)
    # deterministic draw
    ctl2 = load_controls(ROOT, arm="t30-b3", n=30, seed=11)
    assert [c["row"]["key"] for c in ctl] == [c2["row"]["key"] for c2 in ctl2]


# --- feature extraction (GPU) ----------------------------------------------

@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")
def test_feature_extraction_bitwise_deterministic():
    from stencil.evf import extract_features, load_anatomy, load_model
    m, tok, ctrl = load_model(ROOT)
    anat = load_anatomy(ROOT, arm="t30-b3")
    item = anat[0]
    f1 = extract_features(m, tok, ctrl, item)
    f2 = extract_features(m, tok, ctrl, item)
    assert f1.keys() == f2.keys()
    for k in f1:
        assert f1[k] == f2[k], k  # bitwise-equal floats (deterministic proof)
    # registered feature set present
    for k in ("entropy", "margin", "entropy_delta5", "margin_delta5",
              "readout_top", "readout_margin", "attn_mass_span",
              "kl_focus", "js_focus", "obligation_shift"):
        assert k in f1, k


# --- probe fit + gate (CPU, deterministic) ---------------------------------

def test_probe_fit_deterministic_and_gate_math():
    from stencil.evf import fit_probe, gate_eval
    # synthetic separable fixture (hand-built): feature x separates labels
    feats = [{"x": float(i >= 10), "y": 0.5} for i in range(20)]
    labels = [int(i >= 10) for i in range(20)]
    groups = [f"t{i % 4}" for i in range(20)]
    w1 = fit_probe(feats, labels, seed=0)
    w2 = fit_probe(feats, labels, seed=0)
    assert w1 == w2  # deterministic fit
    res = gate_eval(feats, labels, groups, seed=0)
    assert res["r_plus"] == 1.0 and res["r_minus"] == 0.0
    # anti-separable fixture: shuffled labels cannot pass the gate
    import random
    rng = random.Random(3)
    bad = labels[:]
    rng.shuffle(bad)
    res2 = gate_eval(feats, bad, groups, seed=0)
    assert not (res2["r_plus"] >= 0.60 and res2["r_minus"] <= 0.25)

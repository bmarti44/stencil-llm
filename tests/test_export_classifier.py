"""Release 0 export gate: the Hub checkpoint must reproduce the registered scorer."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "data" / "classifier" / "model" / "ft"

pytestmark = pytest.mark.skipif(
    not (MODEL_DIR / "encoder" / "model.safetensors").exists(),
    reason="local classifier weights not present",
)


def _module():
    spec = importlib.util.spec_from_file_location(
        "export_classifier_hf", ROOT / "scripts" / "export_classifier_hf.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["export_classifier_hf"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_export_reproduces_registered_scorer(tmp_path):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    mod = _module()
    report = mod.export(tmp_path / "export", torch, transformers)
    assert report["n_heldout"] == 1093
    assert report["argmax_identical"], report
    assert report["max_abs_logit_drift"] < 1e-4, report
    metrics = json.loads((MODEL_DIR / "metrics.json").read_text())
    assert abs(report["heldout_accuracy"] - metrics["heldout"]["acc"]) < 1e-6
    assert (tmp_path / "export" / "modeling_stencil.py").exists()
    assert (tmp_path / "export" / "model.safetensors").exists()


def test_pipeline_labels_a_standing_rule(tmp_path):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    mod = _module()
    mod.export(tmp_path / "export", torch, transformers)
    clf = transformers.pipeline(
        "text-classification", model=str(tmp_path / "export"), trust_remote_code=True
    )
    rule = clf(
        {"text": "(no context)", "text_pair": "[user] From now on reply in French."}
    )
    none = clf(
        {"text": "(no context)", "text_pair": "[user] Translate this line to French."}
    )
    assert rule["label"] == "rule", rule
    assert none["label"] == "none", none

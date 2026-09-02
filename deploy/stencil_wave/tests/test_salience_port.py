# ruff: noqa: E501
"""The vendored salience classifier must be the research classifier, bitwise."""
from __future__ import annotations

import json

import pytest
from stencil_wave import salience as S

SENTENCES = [
    "Do not use any commas in your response.",
    "It fell all night on the tin roof and the gutters overflowed.",
    "Write a blog post about autumn with at least 300 words.",
    "Your entire response should be in English, and in all capital letters.",
    "Include the keyword 'harvest' at least twice.",
    "Answer with fewer than 40 words.",
    "What is a linked list?",
    "The cat sat on the mat while the rain kept falling.",
    "Wrap your entire response with double quotation marks.",
    "Now write a second note about winter.",
    "i.e. <<title>> must appear once. Then continue.",
    "* Bullet 1",
    "Please, be sure to end your reply with the phrase \"Any other questions?\".",
]


def test_weights_are_trained_and_pass_sanity_probe():
    m = S.DEFAULT_MODEL
    assert m.feature_names == S.FEATURE_NAMES
    assert S.is_instruction("Do not use any commas in your response.")
    assert not S.is_instruction("It fell all night on the tin roof and the gutters overflowed.")


def test_scores_bounded_and_consistent():
    for s in SENTENCES:
        p = S.score_instruction(s)
        assert 0.0 < p < 1.0
        assert S.is_instruction(s) == (p >= 0.5)


def test_extract_instructions_returns_exact_spans():
    text = "Write about autumn. Do not use any commas in your response.\nInclude the keyword 'harvest' twice."
    spans = S.extract_instructions(text)
    assert [text[a:b] for a, b in spans] == [
        "Do not use any commas in your response.", "Include the keyword 'harvest' twice."]


def test_split_sentences_quotes_abbreviations_newlines():
    text = 'Say "Hello. World" once. Use i.e. sparingly.\nNext line here.'
    got = [text[a:b] for a, b in S.split_sentences(text)]
    assert got == ['Say "Hello. World" once.', "Use i.e. sparingly.", "Next line here."]


@pytest.mark.repo
def test_port_matches_research_module_bitwise(repo):
    import importlib
    research = importlib.import_module("stencil.salience")
    ours = json.loads(S.WEIGHTS_PATH.read_text())
    theirs = json.loads((repo / "src" / "stencil" / "salience_weights.json").read_text())
    assert ours == theirs, "vendored salience weights differ from the research weights"
    for s in SENTENCES:
        assert S.featurize(s).tolist() == research.featurize(s).tolist(), s
        assert S.score_instruction(s) == research.score_instruction(s), s
        assert S.split_sentences(s) == research.split_sentences(s), s

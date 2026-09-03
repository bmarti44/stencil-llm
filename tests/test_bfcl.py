from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from stencil.bfcl import (
    build_cohorts,
    control_echo,
    echo_copy_flag,
    ensure_split_allowed,
    parse_tool_calls,
    prepare_case,
    score_case,
)

CATEGORIES = ("base", "missing_params", "missing_functions", "long_context")
ROOT = Path(__file__).resolve().parents[1]
BFCL_DATA = ROOT / "data/bench/bfcl_v3_mt"


def _cases() -> list[dict]:
    return [
        {"id": f"{category}-{index:03d}", "category": category}
        for category in CATEGORIES
        for index in range(40)
    ]


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def test_cohorts_are_deterministic_disjoint_stratified_and_hashed() -> None:
    first = build_cohorts(_cases(), seed=20260902)
    second = build_cohorts(list(reversed(_cases())), seed=20260902)
    assert first == second
    assert len(first["dev"]) == 32
    assert len(first["sealed"]) == 64
    assert not set(first["dev"]) & set(first["sealed"])
    for category in CATEGORIES:
        assert sum(case.startswith(f"{category}-") for case in first["dev"]) == 8
        assert sum(case.startswith(f"{category}-") for case in first["sealed"]) == 16
    assert first["sha256"] == _digest(
        {"seed": first["seed"], "dev": first["dev"], "sealed": first["sealed"]}
    )


def test_vendored_cohort_matches_pinned_source_corpus() -> None:
    cases = []
    for category in CATEGORIES:
        path = BFCL_DATA / f"cases_{category}.jsonl"
        cases.extend(
            {"id": json.loads(line)["id"], "category": category}
            for line in path.read_text().splitlines()
        )
    assert build_cohorts(cases, seed=20260902) == json.loads(
        (BFCL_DATA / "cohorts.json").read_text()
    )


@pytest.mark.parametrize(
    ("text", "calls", "valid"),
    [
        (
            '<tool_call>{"name":"search","arguments":{"q":"x"}}</tool_call>',
            [{"name": "search", "arguments": {"q": "x"}}],
            [True],
        ),
        ("<tool_call>{broken}</tool_call>", [None], [False]),
        (
            '<tool_call>{"name":"a","arguments":{}}</tool_call>tail'
            '<tool_call>{"name":"b","arguments":{"n":2}}</tool_call>',
            [
                {"name": "a", "arguments": {}},
                {"name": "b", "arguments": {"n": 2}},
            ],
            [True, True],
        ),
        ("ordinary answer", [], []),
    ],
)
def test_tool_call_parsing_table(text: str, calls: list, valid: list[bool]) -> None:
    parsed = parse_tool_calls(text)
    assert [item.call for item in parsed] == calls
    assert [item.valid for item in parsed] == valid


class _WordTokenizer:
    def encode(self, text: str):
        return type("Encoding", (), {"ids": text.split()})()

    def decode(self, ids: list[str]) -> str:
        return " ".join(ids)


def test_random_control_echo_matches_target_token_count() -> None:
    tok = _WordTokenizer()
    prior = ["zero one two three", "four five six seven eight"]
    text, token_count = control_echo(tok, prior, target_tokens=6, seed=17)
    assert token_count == 6
    assert len(tok.encode(text).ids) == 6
    assert text != control_echo(tok, prior, target_tokens=6, seed=18)[0]


def test_echo_copy_flag_requires_contiguous_eight_token_run() -> None:
    echoed = list(range(20))
    assert echo_copy_flag([90, *echoed[4:12], 91], echoed)
    assert not echo_copy_flag([*echoed[4:11], 91], echoed)
    assert not echo_copy_flag([], echoed)


def test_sealed_split_requires_explicit_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STENCIL_SEALED_RUN", raising=False)
    with pytest.raises(PermissionError, match="STENCIL_SEALED_RUN=1"):
        ensure_split_allowed("sealed")
    ensure_split_allowed("dev")
    monkeypatch.setenv("STENCIL_SEALED_RUN", "1")
    ensure_split_allowed("sealed")


def test_vendored_bfcl_checker_accepts_its_ground_truth() -> None:
    raw_case = json.loads((BFCL_DATA / "cases_base.jsonl").read_text().splitlines()[0])
    answer = json.loads((BFCL_DATA / "answers_base.jsonl").read_text().splitlines()[0])[
        "ground_truth"
    ]
    case = prepare_case(raw_case, BFCL_DATA / "function_docs")
    result = score_case(
        case,
        [[turn] for turn in answer],
        answer,
        run_name="pytest_ground_truth",
    )
    assert result == {"valid": True}

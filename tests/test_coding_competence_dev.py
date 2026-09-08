import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import coding_competence_dev as competence

ROOT = Path(__file__).resolve().parents[1]


def _check(check_id, symbol, value, expected, rule_ids=None):
    return {
        "check_id": check_id,
        "symbol": symbol,
        "input": value,
        "expected_values": [expected],
        "rule_ids": [] if rule_ids is None else rule_ids,
    }


def _source(symbol, value_expression, label_expression):
    dependency = {
        "alpha": "plus_one(double(value))",
        "beta": 'alpha(value)["value"] * 2',
        "gamma": 'beta(value)["value"] - 3',
    }[symbol]
    return (
        f"def {symbol}(value):\n"
        f"    computed = {dependency}\n"
        f"    computed = {value_expression}\n"
        f"    label = {label_expression}\n"
        '    return {"label": label, "value": computed}\n'
    )


def _document():
    initial = (
        "def double(value):\n"
        "    return value * 2\n"
        "\n"
        "def plus_one(value):\n"
        "    return value + 1\n"
        "\n"
        "def alpha(value):\n"
        "    return None\n"
        "\n"
        "def beta(value):\n"
        "    return None\n"
        "\n"
        "def gamma(value):\n"
        "    return None\n"
    )
    references = [
        _source(
            "alpha",
            "computed",
            '"negative" if value < 0 else "normal"',
        ),
        _source(
            "beta",
            "computed",
            '"negative" if value < 0 else "normal"',
        ),
        _source(
            "gamma",
            "computed",
            '"nonpositive" if value <= 0 else "normal"',
        ),
    ]
    functional_mutants = [
        _source(
            "alpha",
            "computed + (1 if value == 5 or value < 0 else 0)",
            '"negative" if value < 0 else "normal"',
        ),
        _source(
            "beta",
            "computed + (1 if value == 7 or value < 0 else 0)",
            '"negative" if value < 0 else "normal"',
        ),
        _source(
            "gamma",
            "computed + (1 if value == 9 or value <= 0 else 0)",
            '"nonpositive" if value <= 0 else "normal"',
        ),
    ]
    obligation_mutants = [
        _source("alpha", "computed", '"normal"'),
        _source("beta", "computed", '"normal"'),
        _source("gamma", "computed", '"normal"'),
    ]
    public_values = [
        [(2, 5), (4, 9)],
        [(2, 10), (3, 14)],
        [(2, 7), (3, 11)],
    ]
    private_values = [
        [(5, 11), (6, 13)],
        [(7, 30), (8, 34)],
        [(9, 35), (10, 39)],
    ]
    obligation_values = [
        [(-1, -1), (-2, -3)],
        [(-3, -10), (-4, -14)],
        [(0, -1), (-5, -21)],
    ]
    symbols = ["alpha", "beta", "gamma"]
    labels = ["negative", "negative", "nonpositive"]
    public_rounds = []
    private_rounds = []
    for index, symbol in enumerate(symbols):
        rule_id = f"rule-{symbol}"
        request_id = f"request-{index}"
        public_rounds.append(
            {
                "index": index,
                "source_messages": [
                    {
                        "message_id": f"source-{index}",
                        "role": "user",
                        "text": f"Standing direction for {symbol}.",
                    }
                ],
                "request": {
                    "message_id": request_id,
                    "role": "user",
                    "task_handle": "primary" if index != 1 else "secondary",
                    "text": f"Implement {symbol} using the previous dependency.",
                },
                "target": {"path": "project.py", "symbol": symbol},
                "public_checks": [
                    _check(
                        f"public-{symbol}-{offset}",
                        symbol,
                        value,
                        {"label": "normal", "value": expected},
                    )
                    for offset, (value, expected) in enumerate(public_values[index])
                ],
            }
        )
        private_rounds.append(
            {
                "index": index,
                "manual_recap": f"Apply the current private {symbol} rule.",
                "oracle": {
                    "effective_rules": [
                        {
                            "rule_id": rule_id,
                            "scope": "primary" if index != 1 else "secondary",
                            "strength": "required",
                            "text": f"Use the special label for {symbol} edge inputs.",
                            "source_ids": [f"source-{index}", request_id],
                        }
                    ],
                    "inactive_rule_ids": ["rule-alpha"] if index == 2 else [],
                },
                "reference_patch": references[index],
                "functional_checks": [
                    _check(
                        f"private-functional-{symbol}-{offset}",
                        symbol,
                        value,
                        {"label": "normal", "value": expected},
                    )
                    for offset, (value, expected) in enumerate(private_values[index])
                ],
                "obligation_checks": [
                    _check(
                        f"private-obligation-{symbol}-{offset}",
                        symbol,
                        value,
                        {"label": labels[index], "value": expected},
                        [rule_id],
                    )
                    for offset, (value, expected) in enumerate(
                        obligation_values[index]
                    )
                ],
                "negative_controls": [
                    {
                        "control_id": f"control-functional-{symbol}",
                        "kind": "functional",
                        "patch": functional_mutants[index],
                        "expected_failing_check_ids": [
                            f"private-functional-{symbol}-0"
                        ],
                    },
                    {
                        "control_id": f"control-obligation-{symbol}",
                        "kind": "obligation",
                        "patch": obligation_mutants[index],
                        "expected_failing_check_ids": [
                            f"private-obligation-{symbol}-0",
                            f"private-obligation-{symbol}-1",
                        ],
                    },
                ],
            }
        )
    return {
        "schema_version": 1,
        "split": "dev",
        "author": {"name": "kimi", "model": "kimi-k3:cloud"},
        "lineage": {
            "fit_on": "none",
            "development_on": "new original coding competence DEV",
            "evaluated_on": "none",
        },
        "public": {
            "episode_id": "synthetic-consumer-test",
            "project": "Mechanical validator test",
            "task_handles": ["primary", "secondary"],
            "initial_file": {"path": "project.py", "text": initial},
            "initial_checks": [
                _check("initial-double", "double", 3, 6),
                _check("initial-plus-one", "plus_one", 4, 5),
            ],
            "rounds": public_rounds,
        },
        "private": {"rounds": private_rounds},
    }


def test_projection_and_reminder_physically_exclude_private_material():
    document = _document()
    projection = competence.public_projection(document)
    reminder = competence.current_reminder(document, 1)

    visible = json.dumps(projection, sort_keys=True)
    reminder_text = json.dumps(reminder, sort_keys=True)
    assert "private" not in projection
    assert "reference_patch" not in visible
    assert "private-functional" not in visible
    assert "Apply the current private beta rule." not in visible
    assert reminder == {
        "episode_id": "synthetic-consumer-test",
        "round_index": 1,
        "text": "Apply the current private beta rule.",
    }
    assert "oracle" not in reminder_text
    assert "reference_patch" not in reminder_text

    projection["rounds"][0]["request"]["text"] = "changed"
    assert document["public"]["rounds"][0]["request"]["text"] != "changed"
    assert competence.REPLACE_FUNCTION_TOOL["function"]["parameters"] == {
        "type": "object",
        "properties": {"source": {"type": "string"}},
        "required": ["source"],
        "additionalProperties": False,
    }
    assert competence.FORCED_TOOL_CHOICE["function"]["name"] == "replace_function"


def test_projection_accepts_any_declared_rule_scope_and_rejects_unknown_scope():
    document = _document()
    rule = document["private"]["rounds"][1]["oracle"]["effective_rules"][0]
    assert document["public"]["rounds"][1]["request"]["task_handle"] == "secondary"

    rule["scope"] = "primary"
    projection = competence.public_projection(document)
    assert projection["episode_id"] == "synthetic-consumer-test"

    rule["scope"] = "undeclared"
    with pytest.raises(competence.ValidationError, match="global or a task handle"):
        competence.public_projection(document)


def test_exact_native_source_consumer_preserves_bytes_and_compile_before_apply():
    document = _document()
    module = document["public"]["initial_file"]["text"]
    source = "def alpha(value):\n  return plus_one(double(value))\n"

    applied = competence.consume_action(
        module, "project.py", "alpha", {"source": source}
    )
    assert applied.source == source
    assert source in applied.module
    assert applied.source_sha256 == competence.sha256_text(source)
    assert module.endswith("    return None\n")

    with pytest.raises(competence.PatchError, match="byte zero"):
        competence.consume_action(
            module, "project.py", "alpha", {"source": "\n" + source}
        )
    with pytest.raises(competence.PatchError, match="exactly source"):
        competence.consume_action(
            module,
            "project.py",
            "alpha",
            {"source": source, "symbol": "alpha"},
        )
    with pytest.raises(competence.PatchError, match="does not compile"):
        competence.consume_action(
            module,
            "project.py",
            "alpha",
            {"source": "def alpha(value):\n    break\n"},
        )
    with pytest.raises(competence.PatchError, match="does not compile"):
        competence.consume_action(
            module,
            "project.py",
            "alpha",
            {"source": "def alpha(value):\n    return await plus_one(value)\n"},
        )

    assert document["public"]["initial_file"]["text"] == module


def test_preflight_uses_cumulative_public_private_and_current_obligations():
    result = competence.preflight_document(_document())

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["execution_count"] == 110
    last = result["rounds"][2]
    groups = last["reference_checks"]
    assert len(groups["initial"]) == 2
    assert len(groups["cumulative_public"]) == 6
    assert len(groups["cumulative_private"]) == 6
    assert {item["check_id"] for item in groups["current_obligations"]} == {
        "private-obligation-gamma-0",
        "private-obligation-gamma-1",
    }
    assert all(
        {"episode_id", "input", "check_sha256", "module_sha256"} <= set(item)
        for values in groups.values()
        for item in values
    )

    for round_ in result["rounds"]:
        functional, obligation = round_["controls"]
        assert functional["valid"] is True
        assert functional["failed_current_obligation_ids"]
        assert obligation["valid"] is True
        assert obligation["stable_private_functionality_passed"] is True


def test_private_public_disjointness_uses_type_sensitive_json_equality():
    document = _document()
    private_check = document["private"]["rounds"][0]["functional_checks"][0]
    private_check["input"] = 2
    with pytest.raises(competence.ValidationError, match="reuses a public"):
        competence.validate_document(document)

    private_check["input"] = True
    competence.validate_document(document)


def test_mutants_must_fail_named_checks_and_obligations_preserve_functionality():
    document = _document()
    before = document["public"]["initial_file"]["text"]
    functional = document["private"]["rounds"][0]["negative_controls"][0]
    functional["expected_failing_check_ids"] = [
        "private-functional-alpha-0",
        "private-obligation-alpha-0",
    ]

    competence.validate_document(document)
    receipt = competence._audit_control(document, before, 0, functional)
    assert receipt["named_checks_failed"] is True
    assert receipt["failed_current_obligation_ids"] == [
        "private-obligation-alpha-0",
        "private-obligation-alpha-1",
    ]
    assert receipt["valid"] is True

    functional["expected_failing_check_ids"] = ["private-obligation-alpha-0"]
    with pytest.raises(competence.ValidationError, match="functional private"):
        competence.validate_document(document)

    functional["expected_failing_check_ids"] = ["private-functional-alpha-1"]
    receipt = competence._audit_control(document, before, 0, functional)
    assert receipt["named_checks_failed"] is False
    assert receipt["valid"] is False

    obligation = document["private"]["rounds"][0]["negative_controls"][1]
    obligation["patch"] = _source(
        "alpha",
        "computed + (1 if value >= 0 else 0)",
        '"normal"',
    )
    receipt = competence._audit_control(document, before, 0, obligation)
    assert receipt["named_checks_failed"] is True
    assert receipt["stable_private_functionality_passed"] is False
    assert receipt["valid"] is False


def test_reference_must_call_an_actual_prior_dependency():
    document = _document()
    document["private"]["rounds"][1]["reference_patch"] = (
        "def beta(value):\n"
        "    computed = value * 4 + 2\n"
        '    label = "negative" if value < 0 else "normal"\n'
        '    return {"label": label, "value": computed}\n'
    )
    with pytest.raises(competence.ValidationError, match="lacks a dependency"):
        competence.validate_document(document)


def test_direct_cli_import_is_viable_without_pythonpath():
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/coding_competence_dev.py"), "--help"],
        cwd="/",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--input" in result.stdout


def test_invalid_cli_receipt_preserves_read_and_parse_provenance(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b'{"not": "complete"')
    missing = tmp_path / "missing.json"
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/coding_competence_dev.py"),
            "--input",
            str(malformed),
            "--input",
            str(missing),
        ],
        cwd="/",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["status"] == "INVALID"
    assert receipt["elapsed_seconds"] >= 0
    assert receipt["inputs"][0] == {
        "path": str(malformed),
        "bytes": len(malformed.read_bytes()),
        "sha256": competence.sha256_bytes(malformed.read_bytes()),
        "documents": None,
        "read_error": None,
        "parse_error": receipt["inputs"][0]["parse_error"],
    }
    assert receipt["inputs"][0]["parse_error"].startswith("JSONDecodeError:")
    assert receipt["inputs"][1]["path"] == str(missing)
    assert receipt["inputs"][1]["bytes"] is None
    assert receipt["inputs"][1]["sha256"] is None
    assert receipt["inputs"][1]["read_error"].startswith("FileNotFoundError:")


def test_load_inputs_requires_four_unique_episodes_for_a_bank(tmp_path):
    documents = []
    for index in range(4):
        document = copy.deepcopy(_document())
        document["public"]["episode_id"] = f"episode-{index}"
        documents.append(document)
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(documents), encoding="utf-8")

    loaded, receipts = competence.load_inputs([path])
    assert len(loaded) == 4
    assert receipts[0]["documents"] == 4
    assert receipts[0]["sha256"] == competence.sha256_bytes(path.read_bytes())

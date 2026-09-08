"""CPU controls for the same-response coding focus preflight."""

import copy
import json

import pytest

from scripts import coding_worker_dev as c


def patch(symbol, *, functional_bad=False, obligation_bad=False, final=False):
    if final:
        return (
            "def gamma(x):\n"
            "    value = alpha(x)\n"
            "    return value\n"
        )
    bad_functional = "    if x == 1:\n        return 999\n" if functional_bad else ""
    bad_obligation = (
        "    if x == 2 or x == 4:\n        return 888\n"
        if obligation_bad
        else ""
    )
    return (
        f"def {symbol}(x):\n"
        f"{bad_functional}{bad_obligation}"
        "    return helper(x)\n"
    )


def check(check_id, symbol, value, *, rule=False):
    return {
        "check_id": check_id,
        "symbol": symbol,
        "input": value,
        "expected_values": [value],
        "rule_ids": ["rule-global"] if rule else [],
    }


def document():
    initial = (
        '"""Synthetic harness control, not research data."""\n\n'
        "def helper(x):\n"
        "    return x\n\n"
        "def alpha(x):\n"
        "    return None\n\n"
        "def beta(x):\n"
        "    return None\n\n"
        "def gamma(x):\n"
        "    return None\n"
    )
    symbols = ["alpha", "beta", "alpha", "beta", "alpha", "gamma"]
    rounds = []
    for index, symbol in enumerate(symbols):
        source_id = f"source-{index}"
        request_id = f"request-{index}"
        reference = patch(symbol, final=index == 5)
        functional = [
            check(f"functional-{index}-a", symbol, 1),
            check(f"functional-{index}-b", symbol, 3),
        ]
        obligations = [
            check(f"obligation-{index}-a", symbol, 2, rule=True),
            check(f"obligation-{index}-b", symbol, 4, rule=True),
        ]
        rounds.append(
            {
                "index": index,
                "source_messages": [
                    {
                        "message_id": source_id,
                        "role": "user",
                        "text": "Continue applying the standing identity rule.",
                    }
                ],
                "request": {
                    "message_id": request_id,
                    "role": "user",
                    "task_handle": "alpha-work",
                    "text": f"Implement {symbol} while preserving prior behavior.",
                },
                "target": {"path": "module.py", "symbol": symbol},
                "manual_recap": "Keep the identity behavior for this edit.",
                "oracle": {
                    "effective_rules": [
                        {
                            "rule_id": "rule-global",
                            "scope": None,
                            "strength": "required",
                            "text": "New and edited functions preserve values.",
                            "source_ids": ["source-0"],
                        }
                    ],
                    "inactive_rule_ids": [],
                },
                "reference_patch": reference,
                "functional_checks": functional,
                "obligation_checks": obligations,
                "negative_controls": [
                    {
                        "control_id": f"control-{index}-functional",
                        "kind": "functional",
                        "patch": patch(
                            symbol,
                            functional_bad=True,
                            final=index == 5,
                        ),
                        "expected_failing_check_ids": [functional[0]["check_id"]],
                    },
                    {
                        "control_id": f"control-{index}-obligation",
                        "kind": "obligation",
                        "patch": patch(
                            symbol,
                            obligation_bad=True,
                            final=index == 5,
                        ),
                        "expected_failing_check_ids": [
                            item["check_id"] for item in obligations
                        ],
                    },
                ],
            }
        )
    # The final function must call an earlier target while retaining negative
    # control discrimination on its own returned values.
    rounds[-1]["negative_controls"] = [
        {
            "control_id": "control-5-functional",
            "kind": "functional",
            "patch": (
                "def gamma(x):\n"
                "    if x == 1:\n"
                "        return 999\n"
                "    return alpha(x)\n"
            ),
            "expected_failing_check_ids": ["functional-5-a"],
        },
        {
            "control_id": "control-5-obligation",
            "kind": "obligation",
            "patch": (
                "def gamma(x):\n"
                "    if x == 2 or x == 4:\n"
                "        return 888\n"
                "    return alpha(x)\n"
            ),
            "expected_failing_check_ids": [
                "obligation-5-a",
                "obligation-5-b",
            ],
        },
    ]
    return {
        "schema_version": 1,
        "split": "dev",
        "author": {"name": "kimi", "model": "kimi-k3:cloud"},
        "lineage": {
            "fit_on": "none",
            "development_on": (
                "new original specification-authored coding episode"
            ),
            "evaluated_on": "none",
        },
        "episode": {
            "episode_id": "synthetic-harness-control",
            "project": "A synthetic identity module used only to test the harness.",
            "task_handles": ["alpha-work", "beta-work"],
            "initial_file": {"path": "module.py", "text": initial},
            "initial_checks": [check("initial-helper", "helper", 7)],
            "rounds": rounds,
        },
    }


def test_exact_fence_parser_and_splice_preserve_submitted_indentation():
    source = document()["episode"]["initial_file"]["text"]
    code = "def alpha(x):\n  value = helper(x)\n  return value"
    response = "Applicable rules:\nidentity\n" + c.fenced_response(
        "module.py", code
    )
    parsed = c.parse_response(response, "module.py", "alpha")
    assert parsed.prefix == "Applicable rules:\nidentity\n"
    assert parsed.code == code
    assert parsed.fence == c.fenced_response("module.py", code)
    merged = c.splice_function(source, parsed.code, "alpha")
    assert code in merged
    assert "\n  value = helper(x)\n" in merged
    assert "def beta(x):\n    return None" in merged


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ("```python module.py\n  def alpha(x):\n    return x\n```", "Python"),
        (
            "```python module.py\ndef alpha(x):\n    return x\n"
            "def extra(x):\n    return x\n```",
            "top-level",
        ),
        ("```python other.py\ndef alpha(x):\n    return x\n```", "path"),
        ("```python module.py\r\ndef alpha(x):\r\n return x\r\n```", "LF"),
        (
            "```python module.py\ndef alpha(x):\n    return x\n```\ntrailer",
            "trailing",
        ),
    ],
)
def test_parser_rejects_without_repair(response, reason):
    with pytest.raises(c.PatchError, match=reason):
        c.parse_response(response, "module.py", "alpha")


def test_invalid_patch_cannot_change_state_and_valid_wrong_patch_persists():
    source = document()["episode"]["initial_file"]["text"]
    with pytest.raises(c.PatchError):
        c.parse_response(
            "```python module.py\n  def alpha(x):\n    return x\n```",
            "module.py",
            "alpha",
        )
    wrong = patch("alpha", functional_bad=True)
    _, changed = c.consume_patch(source, "module.py", "alpha", wrong)
    assert changed != source and wrong.rstrip() in changed
    result = c.run_checks(changed, [check("wrong", "alpha", 1)])[0]
    assert not result["passed"] and result["actual"] == 999


@pytest.mark.parametrize("statement", ["break", "await x"])
def test_consumer_compiles_exact_candidate_before_state_change(statement):
    source = document()["episode"]["initial_file"]["text"]
    invalid = f"def alpha(x):\n    {statement}\n    return x"
    with pytest.raises(c.PatchError, match="compile"):
        c.consume_patch(source, "module.py", "alpha", invalid)
    assert "def alpha(x):\n    return None" in source


def test_lambda_expression_is_valid_inside_the_single_target_function():
    source = document()["episode"]["initial_file"]["text"]
    code = (
        "def alpha(x):\n"
        "    values = sorted(x, key=lambda item: (-item, item))\n"
        "    return values"
    )
    parsed, changed = c.consume_patch(source, "module.py", "alpha", code)
    assert "lambda item" in parsed.code and parsed.code in changed


@pytest.mark.parametrize(
    "separator",
    ["\u0085", "\u2028", "\u2029", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e"],
)
def test_splice_uses_python_physical_lines_not_unicode_splitlines(separator):
    source = (
        f'"""marker-before{separator}marker-after"""\n'
        "def helper(x):\n"
        "    return x\n"
        "def alpha(x):\n"
        "    return 99\n"
    )
    patch_text = "def alpha(x):\n    return None"
    changed = c.splice_function(source, patch_text, "alpha")
    assert f"marker-before{separator}marker-after" in changed
    assert "return 99" not in changed
    assert c._fresh_execute(changed, "alpha", 0) is None


def test_type_sensitive_json_and_fresh_seccomp_processes():
    assert not c.json_equal(True, 1)
    assert not c.json_equal(1, 1.0)
    assert c.json_equal({"x": [True, 1]}, {"x": [True, 1]})
    stateful = (
        "seen = []\n"
        "def sample(x):\n"
        "    seen.append(x)\n"
        "    return len(seen)\n"
    )
    assert c._fresh_execute(stateful, "sample", 0) == 1
    assert c._fresh_execute(stateful, "sample", 0) == 1
    typed = {
        "check_id": "typed",
        "symbol": "sample",
        "input": 0,
        "expected_values": [True],
        "rule_ids": [],
    }
    assert not c.run_checks(stateful, [typed])[0]["passed"]


def test_reference_and_mutants_use_same_consumer_and_active_check_sets():
    result = c.preflight_document(document(), encode=lambda text: text.encode())
    assert result["eligible"], result["errors"]
    assert len(result["rounds"]) == 6
    for index, round_ in enumerate(result["rounds"]):
        # One initial plus two new stable checks per completed round, then only
        # the two current obligation checks.
        assert len(round_["reference_checks"]) == 1 + 2 * (index + 1) + 2
        assert round_["reference_passed"]
        assert round_["counterfactual_reference_sizing"]["actual_http_prompt"] is False
        for control in round_["negative_controls"]:
            assert control["valid"] and control["named_checks_failed"]
            if control["kind"] == "obligation":
                assert control["stable_functionality_passed"]


def test_strict_schema_and_bank_identity_guards():
    original = document()
    assert c.validate_document(original) is original
    bad = copy.deepcopy(original)
    bad["episode"]["rounds"][0]["request"]["adopted_by_user"] = True
    with pytest.raises(c.ValidationError, match="extra"):
        c.validate_document(bad)
    indented = copy.deepcopy(original)
    indented["episode"]["rounds"][0]["reference_patch"] = (
        "  def alpha(x):\n    return x\n"
    )
    with pytest.raises(c.PatchError):
        c.validate_document(indented)
    with pytest.raises(c.ValidationError, match="one episode or exactly four"):
        c.validate_bank([original, copy.deepcopy(original)])
    wrong_scalar = copy.deepcopy(original)
    wrong_scalar["schema_version"] = True
    with pytest.raises(c.ValidationError, match="schema_version"):
        c.validate_document(wrong_scalar)
    permitted = copy.deepcopy(original)
    for round_ in permitted["episode"]["rounds"]:
        round_["oracle"]["effective_rules"][0]["strength"] = "permitted"
    assert c.validate_document(permitted) is permitted
    contextual_restatement = copy.deepcopy(original)
    contextual_restatement["episode"]["rounds"][1]["oracle"][
        "effective_rules"
    ][0]["text"] += " A current exception is described here."
    assert c.validate_document(contextual_restatement) is contextual_restatement


def test_functional_control_can_name_prior_and_current_obligation_checks():
    item = document()
    round_ = item["episode"]["rounds"][2]
    control = round_["negative_controls"][0]
    control["patch"] = (
        "def alpha(x):\n"
        "    if x == 1 or x == 2:\n"
        "        return 999\n"
        "    return helper(x)\n"
    )
    control["expected_failing_check_ids"] = [
        "functional-0-a",
        "obligation-2-a",
    ]
    assert c.validate_document(item) is item
    state = item["episode"]["initial_file"]["text"]
    for prior in item["episode"]["rounds"][:2]:
        _, state = c.consume_patch(
            state,
            prior["target"]["path"],
            prior["target"]["symbol"],
            prior["reference_patch"],
        )
    _, mutant = c.consume_patch(
        state, "module.py", "alpha", control["patch"]
    )
    stable, obligations = c._active_checks(item["episode"], 2)
    results = {
        row["check_id"]: row
        for row in c.run_checks(mutant, stable + obligations)
    }
    assert not results["functional-0-a"]["passed"]
    assert not results["obligation-2-a"]["passed"]


def test_bad_input_writes_an_ineligible_report_instead_of_raising(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    report = c.preflight_paths([bad], encode=lambda text: text.encode())
    assert report["status"] == "INELIGIBLE"
    assert report["input_errors"] and report["model_calls"] == 0


def test_complete_combined_bank_and_cross_episode_ids(tmp_path):
    bank = []
    for index in range(4):
        item = copy.deepcopy(document())
        episode = item["episode"]
        episode["episode_id"] += f"-{index}"
        encoded = json.dumps(item)
        # Harness-control IDs need the same global uniqueness required of the
        # authored bank. Text and code remain unchanged.
        item = json.loads(
            encoded.replace('"source-', f'"e{index}-source-')
            .replace('"request-', f'"e{index}-request-')
            .replace('"functional-', f'"e{index}-functional-')
            .replace('"obligation-', f'"e{index}-obligation-')
            .replace('"initial-helper"', f'"e{index}-initial-helper"')
            .replace('"control-', f'"e{index}-control-')
            .replace('"rule-global"', f'"e{index}-rule-global"')
        )
        bank.append(item)
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(bank))
    documents, receipts = c.load_inputs([path])
    assert len(documents) == 4 and receipts[0]["documents"] == 4

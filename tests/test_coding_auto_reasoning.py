"""Consuming-path tests for the automatic-focus coding pilot runtime."""

import copy
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import coding_auto_reasoning as runner
from scripts import coding_competence_dev as cpu
from stencil.focus import native_reasoning_tool as native

ROOT = Path(__file__).resolve().parents[1]


def _fixture_document():
    path = ROOT / "tests/test_coding_competence_dev.py"
    spec = importlib.util.spec_from_file_location("_auto_cpu_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._document()


def _projects():
    projects = []
    for project_index in range(2):
        document = copy.deepcopy(_fixture_document())
        public = document["public"]
        public["episode_id"] = f"automatic-project-{project_index}"
        public["rounds"][0]["source_messages"].append(
            {
                "message_id": "assistant-quote",
                "role": "assistant",
                "text": "Quoted café suggestion only: SECRET_QUOTED_SUGGESTION.",
            }
        )
        for round_index, private_round in enumerate(document["private"]["rounds"]):
            private_round["manual_recap"] = (
                f"SECRET_MANUAL_RECAP_{project_index}_{round_index}"
            )
            for rule in private_round["oracle"]["effective_rules"]:
                rule["text"] += (
                    f" SECRET_PRIVATE_ORACLE_{project_index}_{round_index}"
                )
        cpu.validate_document(document)
        projects.append(document)
    return projects


def _write_projects(tmp_path, projects=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    values = projects or _projects()
    paths = []
    for index, document in enumerate(values):
        path = tmp_path / f"project-{index}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        paths.append(path)
    return paths


def _reference_sources(projects):
    return [
        private_round["reference_patch"]
        for project in projects
        for private_round in project["private"]["rounds"]
    ]


def _focus_actions(projects):
    actions = []
    for project_index, project in enumerate(projects):
        visible_ids = []
        for round_index, public_round in enumerate(project["public"]["rounds"]):
            visible_ids.extend(
                message["message_id"] for message in public_round["source_messages"]
            )
            visible_ids.append(public_round["request"]["message_id"])
            if project_index == 0 and round_index == 0:
                obligations = []
            elif project_index == 0 and round_index == 1:
                obligations = [
                    {
                        "text": "Keep  two spaces\nand a newline.",
                        "source_ids": [visible_ids[0], visible_ids[-1]],
                    },
                    {
                        "text": "Preserve the current convention.",
                        "source_ids": [visible_ids[-1]],
                    },
                ]
            else:
                obligations = [
                    {
                        "text": public_round["source_messages"][0]["text"],
                        "source_ids": [
                            public_round["source_messages"][0]["message_id"]
                        ],
                    }
                ]
            actions.append({"obligations": obligations})
    return actions


class ScriptedClient:
    def __init__(self, owner, spec, outcome):
        self.owner = owner
        self.spec = spec
        self.outcome = outcome
        self.deadline = None

    def set_deadline(self, deadline):
        self.deadline = deadline

    def payload(self, messages):
        payload = {
            "model": "/model",
            "messages": copy.deepcopy(messages),
            "tools": [self.spec.tool],
            "tool_choice": self.spec.forced_choice,
            "max_tokens": self.spec.max_output_tokens,
            "thinking_token_budget": self.spec.reasoning_token_budget,
        }
        self.owner.payloads.append(copy.deepcopy(payload))
        return payload

    def perform(self, request_body, persist):
        call_number = len(self.owner.exchanges)
        pending = {
            "status": "PENDING",
            "tool_name": self.spec.tool_name,
            "request_body": request_body.decode("utf-8"),
        }
        persist(pending)
        if isinstance(self.outcome, Exception):
            failed = {**pending, "status": "ERROR", "raw_response": "RAW-FAIL"}
            self.owner.exchanges.append(copy.deepcopy(failed))
            persist(failed)
            raise self.outcome
        raw_arguments = json.dumps(
            self.outcome,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        call_id = f"scripted-{call_number}"
        assistant = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": self.spec.tool_name,
                        "arguments": raw_arguments,
                    },
                }
            ],
        }
        complete = {
            **pending,
            "status": "COMPLETE",
            "raw_response": f"RAW-{call_number}",
            "reasoning": {"observed_reasoning_tokens": 7},
        }
        self.owner.exchanges.append(copy.deepcopy(complete))
        persist(complete)
        return {
            "call_id": call_id,
            "arguments": copy.deepcopy(self.outcome),
            "raw_arguments": raw_arguments,
            "assistant_message": assistant,
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 13,
                "total_tokens": 24,
            },
            "reasoning": {"observed_reasoning_tokens": 7},
        }


class ScriptedFactory:
    def __init__(self, selector_actions, worker_actions):
        self.queues = {
            "record_focus": list(selector_actions),
            "replace_function": list(worker_actions),
        }
        self.payloads = []
        self.exchanges = []
        self.specs = []

    def __call__(self, spec):
        self.specs.append(spec)
        queue = self.queues[spec.tool_name]
        if not queue:
            raise AssertionError(f"no scripted {spec.tool_name} outcome remains")
        return ScriptedClient(self, spec, queue.pop(0))


def _run(tmp_path, projects, worker_actions, *, selector_actions=None, **kwargs):
    paths = _write_projects(tmp_path, projects)
    factory = ScriptedFactory(
        selector_actions or _focus_actions(projects), worker_actions
    )
    result = runner.run(
        paths,
        tmp_path / "run",
        factory,
        deadline_seconds=100,
        **kwargs,
    )
    return result, factory


def _wrong_source(symbol):
    return (
        f"def {symbol}(value):\n"
        '    return {"label": "wrong", "value": 999}\n'
    )


def test_actual_loop_keeps_selector_source_only_and_focus_ephemeral(tmp_path):
    projects = _projects()
    references = _reference_sources(projects)
    wrong = _wrong_source("alpha")
    worker_actions = [{"source": wrong}, {"source": references[0]}]
    worker_actions.extend({"source": source} for source in references[1:])

    result, factory = _run(tmp_path, projects, worker_actions)

    assert result["status"] == "COMPLETE"
    assert result["accounting_complete"] is True
    assert result["mechanical_candidate"] is True
    assert result["pilot_go"] is None
    selector_payloads = [
        payload
        for payload in factory.payloads
        if payload["tool_choice"]["function"]["name"] == "record_focus"
    ]
    worker_payloads = [
        payload
        for payload in factory.payloads
        if payload["tool_choice"]["function"]["name"] == "replace_function"
    ]
    assert len(selector_payloads) == 6
    assert len(worker_payloads) == 7
    for payload in selector_payloads:
        body = json.dumps(payload, ensure_ascii=False)
        assert "def double" not in body
        assert "apply_status" not in body
        assert "current_generated_focus" not in body
        assert "SECRET_MANUAL_RECAP" not in body
        assert "SECRET_PRIVATE_ORACLE" not in body
        assert "private-functional" not in body
        assert len(payload["messages"]) == 2
    first_selector = selector_payloads[0]["messages"][-1]["content"]
    assert '"role":"assistant"' in first_selector
    assert "café" in first_selector
    assert "\\u00e9" not in first_selector
    assert "SECRET_QUOTED_SUGGESTION" in first_selector
    assert '"message_id":"request-0"' in first_selector
    assert '"message_id":"request-1"' not in first_selector
    second_selector = selector_payloads[1]["messages"][-1]["content"]
    assert '"message_id":"request-0"' in second_selector
    assert '"message_id":"request-1"' in second_selector
    assert '"message_id":"request-2"' not in second_selector

    first_worker = worker_payloads[0]["messages"][-1]["content"]
    assert "<current_generated_focus>\n\n</current_generated_focus>" in first_worker
    assert "SECRET_MANUAL_RECAP" not in first_worker
    retry = worker_payloads[1]["messages"]
    assert wrong in retry[-1]["content"]
    assert retry[-1]["content"].count("<current_generated_focus>") == 1
    assert all("reasoning" not in message for message in retry)
    round_two = worker_payloads[2]["messages"]
    assert sum(
        "<current_generated_focus>" in (message.get("content") or "")
        for message in round_two
    ) == 1
    rendered = round_two[-1]["content"]
    assert "Keep  two spaces\nand a newline." in rendered
    assert "Preserve the current convention." in rendered
    assert rendered.index("Keep  two spaces") < rendered.index(
        "Preserve the current convention."
    )
    assert any(
        json.loads(message["tool_calls"][0]["function"]["arguments"])["source"]
        == wrong
        for message in round_two
        if message.get("tool_calls")
    )
    for payload in factory.payloads:
        body = json.dumps(payload, ensure_ascii=False)
        assert "SECRET_MANUAL_RECAP" not in body
        assert "SECRET_PRIVATE_ORACLE" not in body
        assert "private-obligation" not in body

    first_record = json.loads(
        (tmp_path / "run/requests/request-0000.json").read_text()
    )
    assert len(first_record["worker_attempts"]) == 2
    assert first_record["worker_attempts"][0]["all_public_passed"] is False
    assert first_record["worker_attempts"][1]["all_public_passed"] is True
    assert first_record["terminal_private_passed"] is True
    assert first_record["focus"]["obligations"] == []
    assert factory.queues == {"record_focus": [], "replace_function": []}


def test_two_attempt_limit_keeps_failure_and_continues_later_requests(tmp_path):
    projects = _projects()
    references = _reference_sources(projects)
    worker_actions = [
        {"source": _wrong_source("alpha")},
        {"source": _wrong_source("alpha")},
        *(
            {"source": source}
            for source in references[1:]
            for _attempt in range(2)
        ),
    ]

    result, _factory = _run(tmp_path, projects, worker_actions)

    assert result["status"] == "COMPLETE"
    first = json.loads((tmp_path / "run/requests/request-0000.json").read_text())
    second = json.loads((tmp_path / "run/requests/request-0001.json").read_text())
    assert len(first["worker_attempts"]) == 2
    assert first["public_solved"] is False
    assert first["request_passed"] is False
    assert second["status"] == "COMPLETE"
    assert result["completed_requests"] == 6


@pytest.mark.parametrize("failure_kind", ["selector", "worker"])
def test_technical_failure_aborts_with_full_planned_denominator(
    tmp_path, failure_kind
):
    projects = _projects()
    selectors = _focus_actions(projects)
    workers = [{"source": source} for source in _reference_sources(projects)]
    error = native.TechnicalError("transport", f"{failure_kind} down")
    if failure_kind == "selector":
        selectors[0] = error
    else:
        workers[0] = error

    result, factory = _run(
        tmp_path,
        projects,
        workers,
        selector_actions=selectors,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["accounting_complete"] is False
    assert result["mechanical_candidate"] is False
    assert len(result["planned_work"]) == 6
    assert result["unattempted_requests"] == 5
    assert result["recorded_calls"] == (1 if failure_kind == "selector" else 2)
    assert any(exchange["raw_response"] == "RAW-FAIL" for exchange in factory.exchanges)
    records = [
        json.loads(path.read_text())
        for path in sorted((tmp_path / "run/requests").glob("*.json"))
    ]
    assert len(records) == 6
    assert records[0]["status"] == "TECHNICAL_INCOMPLETE"
    assert all(record["status"] == "UNATTEMPTED" for record in records[1:])


def test_selector_rejects_a_future_source_id_through_actual_loop(tmp_path):
    projects = _projects()
    selectors = _focus_actions(projects)
    selectors[0] = {
        "obligations": [
            {"text": "Unsupported future citation.", "source_ids": ["request-1"]}
        ]
    }

    result, _factory = _run(
        tmp_path,
        projects,
        [{"source": source} for source in _reference_sources(projects)],
        selector_actions=selectors,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["technical_failure"]["kind"] == "malformed_response"
    assert result["recorded_calls"] == 1
    selector = json.loads((tmp_path / "run/calls/call-0000.json").read_text())
    assert selector["kind"] == "selector"
    assert selector["status"] == "TECHNICAL_ERROR"


def test_deadline_persists_finished_check_and_unfinished_ids(tmp_path):
    projects = _projects()
    references = _reference_sources(projects)
    now = [0.0]
    executed = []

    def clock():
        return now[0]

    def check_runner(_module, checks):
        assert len(checks) == 1
        check = checks[0]
        executed.append(check["check_id"])
        now[0] = 98.0
        return [
            {
                "check_id": check["check_id"],
                "passed": True,
                "actual": copy.deepcopy(check["expected_values"][0]),
                "error": None,
            }
        ]

    result, _factory = _run(
        tmp_path,
        projects,
        [{"source": source} for source in references],
        check_runner=check_runner,
        clock=clock,
    )

    assert result["status"] == "INCOMPLETE"
    call = json.loads((tmp_path / "run/calls/call-0001.json").read_text())
    assert call["kind"] == "worker"
    assert [item["check_id"] for item in call["public_checks"]] == executed
    assert len(executed) == 1
    assert len(call["unfinished_public_check_ids"]) == 3
    assert call["status"] == "TECHNICAL_ERROR"


def test_candidate_gate_requires_one_complete_project(tmp_path):
    projects = _projects()
    references = _reference_sources(projects)
    private_mutants = [
        projects[index]["private"]["rounds"][0]["negative_controls"][0]["patch"]
        for index in range(2)
    ]
    neither = [{"source": source} for source in references]
    neither[0] = {"source": private_mutants[0]}
    neither[3] = {"source": private_mutants[1]}
    result, _factory = _run(tmp_path / "neither", projects, neither)
    assert result["status"] == "COMPLETE"
    assert result["mechanical_candidate"] is False
    assert [project["project_passed"] for project in result["projects"]] == [
        False,
        False,
    ]

    one = [{"source": source} for source in references]
    one[3] = {"source": private_mutants[1]}
    result, _factory = _run(tmp_path / "one", projects, one)
    assert result["status"] == "COMPLETE"
    assert result["mechanical_candidate"] is True
    assert result["pilot_go"] is None
    assert [project["project_passed"] for project in result["projects"]] == [
        True,
        False,
    ]


def test_loader_keeps_individual_receipts_and_rejects_duplicate_episode(tmp_path):
    projects = _projects()
    paths = _write_projects(tmp_path, projects)
    documents, receipts = runner.load_projects(paths)
    assert [document["public"]["episode_id"] for document in documents] == [
        "automatic-project-0",
        "automatic-project-1",
    ]
    assert [receipt["documents"] for receipt in receipts] == [1, 1]
    projects[1]["public"]["episode_id"] = projects[0]["public"]["episode_id"]
    paths = _write_projects(tmp_path / "duplicate", projects)
    with pytest.raises(cpu.ValidationError, match="episode IDs must be unique"):
        runner.load_projects(paths)


def test_preview_and_absolute_cli_are_cpu_only_and_bind_references(tmp_path):
    projects = _projects()
    paths = _write_projects(tmp_path, projects)
    result = runner.preview(paths)
    assert result["status"] == "PASS"
    assert result["model_calls"] == 0
    assert result["documents"] == 2
    assert result["preflight"]["status"] == "PASS"
    assert len(result["preflight"]["projects"]) == 2
    assert all(
        item["status"] == "PASS" for item in result["preflight"]["projects"]
    )
    assert len(result["selector_cold_requests"]) == 6
    assert len(result["reference_actions"]) == 12
    assert {item["kind"] for item in result["reference_actions"]} == {
        "record_focus",
        "replace_function",
    }
    assert result["all_reference_actions_headroom"] is True
    assert result["future_actual_prompt_claim"] is False
    assert result["resource_bounds"]["maximum_generation_requests"] == 18
    assert "scripts/coding_auto_reasoning.py" in result["code_sha256"]
    assert "src/stencil/focus/native_reasoning_tool.py" in result["code_sha256"]

    python = ROOT / ".venv/bin/python"
    script = ROOT / "scripts/coding_auto_reasoning.py"
    input_directory = tmp_path / "reviewed"
    for index, project in enumerate(projects):
        target = input_directory / f"author-{index:02d}/reviewed.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(project), encoding="utf-8")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    help_result = subprocess.run(
        [str(python), str(script), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "--preview" in help_result.stdout
    cli = subprocess.run(
        [
            str(python),
            str(script),
            "--input",
            str(input_directory),
            "--preview",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    parsed = json.loads(cli.stdout)
    assert parsed["status"] == "PASS"
    assert parsed["model_calls"] == 0

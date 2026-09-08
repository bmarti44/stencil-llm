from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import source_interpreter_fit as fit


def _validated_rows():
    return [
        {
            "preview_row_index": index,
            "conversation_id": f"conversation-{index // 3}",
            "family_id": f"family-{index // 3}",
            "query_index": index % 3,
            "query_message_id": f"q-{index}",
            "prefix_ids": [100 + index, 200 + index],
            "target_with_eos_ids": [300 + index, fit.EOS_TOKEN_ID],
            "input_ids": [100 + index, 200 + index, 300 + index, fit.EOS_TOKEN_ID],
            "labels": [-100, -100, 300 + index, fit.EOS_TOKEN_ID],
            "attention_mask": [1, 1, 1, 1],
            "prefix_length": 2,
            "full_length": 4,
            "loss_positions": [2, 3],
            "causal": {
                "label_positions": [2, 3],
                "causal_logit_positions": [1, 2],
                "supervised_tokens": 2,
            },
        }
        for index in range(18)
    ]


def test_fixed_schedule_consumes_every_exact_row_three_times_and_rejects_reorder():
    rows = _validated_rows()
    schedule = fit.build_schedule(rows)
    assert len(schedule) == 54
    assert [item["row_index"] for item in schedule] == [
        index for epoch in fit.ROW_SCHEDULE for index in epoch
    ]
    for epoch in range(3):
        current = schedule[epoch * 18 : (epoch + 1) * 18]
        assert sorted(item["row_index"] for item in current) == list(range(18))
    assert all(
        item["conversation_id"] == rows[item["row_index"]]["conversation_id"]
        and item["query_message_id"] == rows[item["row_index"]]["query_message_id"]
        and item["label_positions"] == rows[item["row_index"]]["loss_positions"]
        for item in schedule
    )

    wrong = copy.deepcopy(rows)
    wrong[4], wrong[5] = wrong[5], wrong[4]
    with pytest.raises(ValueError, match="row order|preview row"):
        fit.build_schedule(wrong)


def test_all_row_consumer_binds_each_document_query_and_rejects_wrong_row():
    documents = [
        {
            "conversation_id": f"conversation-{index}",
            "family_id": f"family-{index}",
            "queries": [{"message_id": f"q-{index * 3 + query}"} for query in range(3)],
        }
        for index in range(6)
    ]
    receipts = [{"conversation_id": item["conversation_id"]} for item in documents]
    manifest = {
        "documents": [
            {
                "conversation_id": item["conversation_id"],
                "family_id": item["family_id"],
            }
            for item in documents
        ]
    }
    rows = _validated_rows()
    calls = []

    def validate(row, **kwargs):
        calls.append((row["preview_row_index"], kwargs["document"]["conversation_id"]))
        return row["causal"]

    validated = fit.validate_all_rows(
        rows,
        documents,
        receipts,
        manifest,
        root=Path("/unused"),
        validate_row=validate,
    )
    assert len(validated) == len(calls) == 18
    assert calls[14] == (14, "conversation-4")

    wrong = copy.deepcopy(rows)
    wrong[14]["conversation_id"] = "future-conversation"
    with pytest.raises(ValueError, match="row order|source identity"):
        fit.validate_all_rows(
            wrong,
            documents,
            receipts,
            manifest,
            root=Path("/unused"),
            validate_row=validate,
        )


class FakeTensor:
    def __init__(self, values):
        self.values = copy.deepcopy(values)

    def tolist(self):
        return copy.deepcopy(self.values)

    def __getitem__(self, index):
        return FakeTensor(self.values[index])


class FakeCuda:
    def is_available(self):
        return False

    def synchronize(self):
        return None


class FakeTorch:
    long = "long"
    cuda = FakeCuda()

    @staticmethod
    def tensor(values, **_kwargs):
        return FakeTensor(values)

    @staticmethod
    def ones_like(tensor):
        return FakeTensor([[1 for _ in tensor.values[0]]])

    @staticmethod
    def inference_mode():
        return contextlib.nullcontext()


class FakeLayer:
    def __init__(self):
        self.disable_adapters = False
        self.active_adapters = ["roundtrip"]


class FakeOutput:
    def __init__(self, ids):
        self.sequences = FakeTensor([ids])


class FakeTokenizer:
    def decode(self, ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        assert skip_special_tokens is False
        assert clean_up_tokenization_spaces is False
        return bytes(ids).decode("utf-8")


class FakeModel:
    def __init__(self, suffixes):
        from transformers import GenerationConfig

        self.layer = FakeLayer()
        self.suffixes = list(suffixes)
        self.calls = []
        self.generation_config = GenerationConfig(
            do_sample=True,
            eos_token_id=[151645, 151643],
            pad_token_id=151643,
            temperature=0.6,
            top_k=20,
            top_p=0.95,
        )
        self.config = type(
            "Config",
            (),
            {
                "use_cache": False,
                "_get_generation_parameters": lambda _self: {},
            },
        )()
        self.checkpointing_disabled = False
        self.native_resolution_calls = []

    def modules(self):
        return [self, self.layer]

    def eval(self):
        return self

    def gradient_checkpointing_disable(self):
        self.checkpointing_disabled = True

    def set_adapter(self, name, *, inference_mode):
        assert inference_mode is True
        self.layer.active_adapters = [name]
        self.layer.disable_adapters = False

    @contextlib.contextmanager
    def disable_adapter(self):
        self.layer.disable_adapters = True
        try:
            yield
        finally:
            self.layer.disable_adapters = False

    def generate(self, **kwargs):
        self.calls.append(
            {
                "kwargs": kwargs,
                "disabled": self.layer.disable_adapters,
                "active": list(self.layer.active_adapters),
            }
        )
        suffix = self.suffixes.pop(0)
        if isinstance(suffix, BaseException):
            raise suffix
        for criterion in kwargs["stopping_criteria"]:
            criterion(None, None)
        return FakeOutput(kwargs["input_ids"].values[0] + suffix)

    def _prepare_generation_config(self, generation_config, **kwargs):
        from transformers.generation.utils import GenerationMixin

        self.native_resolution_calls.append("config")
        return GenerationMixin._prepare_generation_config(
            self, generation_config, **kwargs
        )

    def _prepare_generated_length(self, **kwargs):
        from transformers.generation.utils import GenerationMixin

        self.native_resolution_calls.append("length")
        return GenerationMixin._prepare_generated_length(self, **kwargs)


def _generation_row():
    return {
        "preview_row_index": 14,
        "conversation_id": "conversation-4",
        "query_index": 2,
        "query_message_id": "q14",
        "prefix_ids": [10, 11, 12] + [13] * 2963,
        "target_ids": [99],
        "target_with_eos_ids": [99, fit.EOS_TOKEN_ID],
        "labels": [-100, -100, -100, 99, fit.EOS_TOKEN_ID],
        "source_prefix": [
            {"message_id": "m1", "role": "user", "text": "rule"},
            {
                "message_id": "q14",
                "role": "user",
                "text": "work",
                "task_handle": "task",
            },
        ],
    }


def _json_suffix(*, trailing=False, eos=True):
    body = b'{"obligations":[]}' + (b" trailing" if trailing else b"")
    return list(body) + ([fit.EOS_TOKEN_ID] if eos else [])


def test_pair_uses_prefix_only_and_exact_modes_kwargs_while_retaining_invalid(tmp_path):
    model = FakeModel([_json_suffix(trailing=True), _json_suffix()])
    row = _generation_row()
    pair = fit.run_generation_pair(
        tmp_path,
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        row=row,
        adapter_name="roundtrip",
        stopping_list=lambda values: values,
        deadline_seconds=300,
    )
    assert pair["status"] == "COMPLETE"
    assert len(model.calls) == 2
    assert model.calls[0]["disabled"] is True
    assert model.calls[1]["disabled"] is False
    assert model.calls[1]["active"] == ["roundtrip"]
    assert model.checkpointing_disabled is True
    for call in model.calls:
        kwargs = call["kwargs"]
        assert kwargs["input_ids"].values == [row["prefix_ids"]]
        assert kwargs["attention_mask"].values == [[1] * 2966]
        assert "labels" not in kwargs and "target_ids" not in kwargs
        assert "past_key_values" not in kwargs
        assert kwargs["do_sample"] is False
        assert kwargs["max_new_tokens"] == 2048
        assert kwargs["eos_token_id"] == fit.EOS_TOKEN_ID
        assert kwargs["pad_token_id"] == fit.PAD_TOKEN_ID
        assert kwargs["logits_to_keep"] == 1
    first, second = pair["calls"]
    assert model.native_resolution_calls == ["config", "length", "config", "length"]
    assert first["inherited_generation_config"]["max_length"] is None
    assert first["inherited_generation_config"]["min_length"] is None
    assert first["inherited_generation_config"]["repetition_penalty"] is None
    assert first["resolved_generation_config"]["min_length"] == 0
    assert first["resolved_generation_config"]["repetition_penalty"] == 1.0
    assert first["resolved_generation_config"]["max_length"] == 5014
    assert first["explicit_forward_arguments"] == {"logits_to_keep": 1}
    assert first["explicit_control_arguments"] == {"synced_gpus": False}
    assert "logits_to_keep" not in first["explicit_generation_config_arguments"]
    assert "synced_gpus" not in first["explicit_generation_config_arguments"]
    assert first["strict_output"]["valid"] is False
    assert "trailing" in first["decoded_text"]
    assert first["generated_ids"][-1] == fit.EOS_TOKEN_ID
    assert first["stop_facts"]["eos_present"] is True
    assert second["strict_output"]["valid"] is True


def test_generation_deadline_or_exception_stops_second_call_without_fabrication(
    tmp_path,
):
    class DeadlineClock:
        def __init__(self):
            self.calls = 0

        def __call__(self):
            self.calls += 1
            return 0.0 if self.calls <= 4 else 301.0

    deadline_model = FakeModel([_json_suffix(eos=False), _json_suffix()])
    pair = fit.run_generation_pair(
        tmp_path / "deadline",
        model=deadline_model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        row=_generation_row(),
        adapter_name="roundtrip",
        stopping_list=lambda values: values,
        deadline_seconds=300,
        clock=DeadlineClock(),
    )
    assert pair["status"] == "INCOMPLETE_DEADLINE"
    assert len(deadline_model.calls) == 1
    assert pair["calls"][0]["stop_facts"]["deadline_reached"] is True
    assert pair["calls"][1]["status"] == "NOT_ATTEMPTED"
    assert pair["calls"][1]["generated_ids"] is None

    failed_model = FakeModel([RuntimeError("decode failed"), _json_suffix()])
    pair = fit.run_generation_pair(
        tmp_path / "exception",
        model=failed_model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        row=_generation_row(),
        adapter_name="roundtrip",
        stopping_list=lambda values: values,
        deadline_seconds=300,
    )
    assert pair["status"] == "INCOMPLETE_EXCEPTION"
    assert len(failed_model.calls) == 1
    assert pair["calls"][0]["generated_ids"] is None
    assert pair["calls"][1]["status"] == "NOT_ATTEMPTED"


def test_returned_cap_is_retained_and_does_not_block_fixed_second_call(tmp_path):
    capped = list(b"{" + b"x" * 2047)
    model = FakeModel([capped, _json_suffix()])
    pair = fit.run_generation_pair(
        tmp_path,
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        row=_generation_row(),
        adapter_name="roundtrip",
        stopping_list=lambda values: values,
    )
    assert pair["status"] == "COMPLETE"
    assert len(model.calls) == 2
    first = pair["calls"][0]
    assert first["stop_facts"] == {
        "eos_present": False,
        "terminal_eos": False,
        "cap_reached": True,
        "deadline_reached": False,
    }
    assert len(first["generated_ids"]) == 2048
    assert first["strict_output"]["valid"] is False
    assert pair["calls"][1]["strict_output"]["valid"] is True


def test_late_completion_publication_stops_pair_before_second_call(
    tmp_path, monkeypatch
):
    class MutableClock:
        now = 0.0

        def __call__(self):
            return self.now

    clock = MutableClock()
    original_write = fit._write_json
    delayed = False

    def write(path, value):
        nonlocal delayed
        original_write(path, value)
        if (
            not delayed
            and Path(path).name == "stage-generation_base.json"
            and value.get("status") == "COMPLETE"
        ):
            delayed = True
            clock.now = 301.0

    monkeypatch.setattr(fit, "_write_json", write)
    model = FakeModel([_json_suffix(), _json_suffix()])
    pair = fit.run_generation_pair(
        tmp_path,
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        row=_generation_row(),
        adapter_name="roundtrip",
        stopping_list=lambda values: values,
        deadline_seconds=300,
        clock=clock,
    )
    assert pair["status"] == "INCOMPLETE_DEADLINE"
    assert len(model.calls) == 1
    assert pair["calls"][0]["stop_facts"]["deadline_reached"] is True
    stage = json.loads((tmp_path / "stage-generation_base.json").read_text())
    assert stage["status"] == "DEADLINE"
    assert stage["completion_records_observed_monotonic"] == 301.0
    current = json.loads((tmp_path / "current-stage.json").read_text())
    assert current["stage"] == "generation-base"
    assert current["status"] == "COMPLETION_PENDING"


def _child_script(tmp_path: Path, body: str) -> list[str]:
    path = tmp_path / (hashlib.sha256(body.encode()).hexdigest()[:10] + ".py")
    path.write_text(body, encoding="utf-8")
    return [sys.executable, str(path)]


def test_supervisor_hung_stage_reaps_only_owned_child_and_preserves_unknown(tmp_path):
    run = tmp_path / "run-hung"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned", encoding="utf-8")
    foreign = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    body = (
        "import json,pathlib,sys,time\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "deadline=time.monotonic()+0.2\n"
        "(run/'current-stage.json').write_text(json.dumps({"
        "'stage':'training','status':'INTENT','hard_deadline_monotonic':deadline}))\n"
        "(run/'step-00.json').write_text(json.dumps({"
        "'ordinal':0,'classification':'warm-up','status':'UPDATE_PENDING',"
        "'update_completed':None,'update_completion_known':False,"
        "'validation_completed':False}))\n"
        "time.sleep(30)\n"
    )
    try:
        code, lifecycle = fit.supervise_child(
            run,
            _child_script(tmp_path, body) + [str(run)],
            run_flag=flag,
            pid_registry=tmp_path / "pids",
            reservation_seconds=3,
            termination_reserve_seconds=1,
            poll_seconds=0.03,
        )
        assert code == 2
        assert lifecycle["status"] == "INCOMPLETE_STAGE_TIMEOUT"
        assert lifecycle["timed_out_stage"] == "training"
        assert lifecycle["child_exit_confirmed"] is True
        assert lifecycle["updates"] is None
        assert lifecycle["pending_or_unknown_steps"] == [0]
        assert [call["status"] for call in lifecycle["generation_calls"]] == [
            "NOT_ATTEMPTED",
            "NOT_ATTEMPTED",
        ]
        assert foreign.poll() is None
        assert not flag.exists()
    finally:
        foreign.terminate()
        foreign.wait(timeout=2)


def test_supervisor_base_hard_stop_marks_only_started_call_unavailable(tmp_path):
    run = tmp_path / "run-base-hung"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned", encoding="utf-8")
    body = (
        "import json,pathlib,sys,time\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "deadline=time.monotonic()+0.2\n"
        "stage={'stage':'generation-base','status':'INTENT',"
        "'hard_deadline_monotonic':deadline}\n"
        "(run/'stage-generation_base.json').write_text(json.dumps(stage))\n"
        "(run/'current-stage.json').write_text(json.dumps(stage))\n"
        "time.sleep(30)\n"
    )
    code, lifecycle = fit.supervise_child(
        run,
        _child_script(tmp_path, body) + [str(run)],
        run_flag=flag,
        pid_registry=tmp_path / "pids",
        reservation_seconds=3,
        termination_reserve_seconds=1,
        poll_seconds=0.03,
    )
    assert code == 2
    assert lifecycle["timed_out_stage"] == "generation-base"
    assert [call["status"] for call in lifecycle["generation_calls"]] == [
        "UNAVAILABLE",
        "NOT_ATTEMPTED",
    ]
    assert lifecycle["generation_calls"][0]["generated_ids_available"] is None
    assert not flag.exists()


def test_missing_final_result_cannot_pass_and_publication_tail_is_explicit(tmp_path):
    run = tmp_path / "run-partial"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned", encoding="utf-8")
    body = (
        "import json,pathlib,sys\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "(run/'step-00.json').write_text(json.dumps({"
        "'ordinal':0,'classification':'warm-up','status':'UPDATE_CONFIRMED',"
        "'update_completed':True,'update_completion_known':True,"
        "'validation_completed':False}))\n"
    )
    code, lifecycle = fit.supervise_child(
        run,
        _child_script(tmp_path, body) + [str(run)],
        run_flag=flag,
        pid_registry=tmp_path / "pids",
        reservation_seconds=2,
        termination_reserve_seconds=0.5,
    )
    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_CHILD_RESULT"
    assert lifecycle["confirmed_updates"] == 1
    assert lifecycle["validated_updates"] == 0
    assert lifecycle["receipt_publication_tail"]["included_in_elapsed"] is False
    assert (
        lifecycle["receipt_publication_tail"]["bounded_by_outer_process_observation"]
        is True
    )
    assert lifecycle["ended_monotonic"] >= lifecycle["child_exit_monotonic"]
    assert not flag.exists()


def test_import_dry_and_direct_qualification_do_not_load_ml_or_create_run(tmp_path):
    command = (
        "import sys; import scripts.source_interpreter_fit; "
        "assert 'torch' not in sys.modules; "
        "assert 'transformers' not in sys.modules; "
        "assert 'peft' not in sys.modules"
    )
    imported = subprocess.run(
        [sys.executable, "-c", command], cwd=fit.ROOT, check=False
    )
    assert imported.returncode == 0

    run = fit.RESULTS_DIR / f"run-dry-{os.getpid()}-{time.time_ns()}"
    dry = subprocess.run(
        [sys.executable, str(fit.__file__), "--run-dir", str(run)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry.returncode == 0, dry.stderr
    plan = json.loads(dry.stdout)
    assert plan["execute"] is False
    assert plan["outer_observer_required"] is True
    assert plan["outer_observer_enforces_initial_training_stage"] is True
    assert "before supervisor launch" in plan["outer_observer_contract"]
    assert plan["training_stage_seconds"] == 1220
    assert plan["generation_stage_seconds"] == 300
    assert not run.exists()

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    qualified = subprocess.run(
        [sys.executable, str(fit.__file__), "--_qualify-only"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert qualified.returncode == 0, qualified.stderr
    receipt = json.loads(qualified.stdout)
    assert receipt["status"] == "PASS"
    assert receipt["rows"] == 18
    assert receipt["updates"] == 54
    assert receipt["model_loaded"] is False

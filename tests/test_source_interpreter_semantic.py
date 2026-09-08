import contextlib
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import source_interpreter_semantic as semantic


def _json_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _document(index):
    return {
        "schema_version": 1,
        "conversation_id": f"source-semantic-20260908-{index:02d}",
        "family_id": f"source-semantic-family-20260908-{index:02d}",
        "split": "withheld",
        "messages": [
            {
                "message_id": f"m-{index}-{query}",
                "role": "user",
                "text": f"synthetic request {query}",
                "task_handle": f"task-{index}-{query}",
            }
            for query in range(3)
        ],
        "queries": [
            {
                "message_id": f"m-{index}-{query}",
                "target": {
                    "obligations": [
                        {
                            "text": f"SECRET-TARGET-{index}-{query}",
                            "source_ids": [f"m-{index}-{query}"],
                        }
                    ]
                },
            }
            for query in range(3)
        ],
    }


class FakePreparedRow:
    def __init__(self, document, query_index):
        query = document["queries"][query_index]
        prefix = document["messages"][: query_index + 1]
        target = query["target"]
        target_text = json.dumps(target, sort_keys=True)
        self.value = {
            "conversation_id": document["conversation_id"],
            "family_id": document["family_id"],
            "split": "withheld",
            "query_index": query_index,
            "query_message_id": query["message_id"],
            "task_handle": prefix[-1]["task_handle"],
            "source_prefix": copy.deepcopy(prefix),
            "source_prefix_sha256": hashlib.sha256(_json_bytes(prefix)).hexdigest(),
            "prefix_ids": [1000 + query_index, 2000 + query_index],
            "prefix_length": 2,
            "target_text": target_text,
            "target_text_sha256": hashlib.sha256(target_text.encode()).hexdigest(),
            "target_ids": [3000 + query_index],
            "target_with_eos_ids": [3000 + query_index, semantic.EOS_TOKEN_ID],
            "target_length": 2,
            "full_length": 4,
            "eos_token_id": semantic.EOS_TOKEN_ID,
        }

    def receipt(self):
        return copy.deepcopy(self.value)


class FakeSource:
    @staticmethod
    def load_documents(paths):
        documents = [json.loads(Path(path).read_text()) for path in paths]
        return documents, [
            {
                "path": str(path),
                "bytes": Path(path).stat().st_size,
                "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                "conversation_id": document["conversation_id"],
                "family_id": document["family_id"],
                "split": document["split"],
                "read_error": None,
                "parse_error": None,
            }
            for path, document in zip(paths, documents, strict=True)
        ]

    @staticmethod
    def prepare_rows(documents, tokenizer):
        assert tokenizer == "synthetic-tokenizer"
        return [
            FakePreparedRow(document, query)
            for document in documents
            for query in range(3)
        ]

    @staticmethod
    def _tokenizer_state(tokenizer):
        assert tokenizer == "synthetic-tokenizer"
        return {"kind": "synthetic-tokenizer", "eos_token_id": semantic.EOS_TOKEN_ID}

    @staticmethod
    def _verify_original_tokenizer(tokenizer):
        return FakeSource._tokenizer_state(tokenizer), {"tokenizer.json": "abc"}, []


def _accepted_manifest(tmp_path, monkeypatch):
    semantic_body = b"synthetic accepted semantic spec\n"
    review_body = b"synthetic accepted review\n"
    assets_body = b'{"status":"LOCAL_BASE_BYTES_VERIFIED"}\n'
    (tmp_path / "results/source-interpreter").mkdir(parents=True)
    (tmp_path / "results/coding-auto-reasoning/research-next").mkdir(parents=True)
    (tmp_path / "results/source-interpreter/SEMANTIC.md").write_bytes(semantic_body)
    (tmp_path / "results/source-interpreter/semantic-review-astra.md").write_bytes(
        review_body
    )
    (
        tmp_path / "results/coding-auto-reasoning/research-next/base-assets.json"
    ).write_bytes(assets_body)
    monkeypatch.setattr(
        semantic, "SEMANTIC_SHA256", hashlib.sha256(semantic_body).hexdigest()
    )
    monkeypatch.setattr(
        semantic, "ACCEPTED_REVIEW_SHA256", hashlib.sha256(review_body).hexdigest()
    )
    monkeypatch.setattr(semantic, "_accepted_review_bytes", lambda _root: review_body)
    bindings = {}
    for relative in (
        "results/source-interpreter/SEMANTIC.md",
        "results/source-interpreter/semantic-review-astra.md",
        "results/coding-auto-reasoning/research-next/base-assets.json",
    ):
        body = (tmp_path / relative).read_bytes()
        bindings[relative] = {
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    static_hashes = dict(semantic.STATIC_SHA256)
    static_hashes["results/coding-auto-reasoning/research-next/base-assets.json"] = (
        bindings["results/coding-auto-reasoning/research-next/base-assets.json"][
            "sha256"
        ]
    )
    monkeypatch.setattr(semantic, "STATIC_SHA256", static_hashes)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts/source_interpreter_semantic.py").write_text("synthetic")
    (tmp_path / "tests/test_source_interpreter_semantic.py").write_text("synthetic")
    monkeypatch.setattr(
        semantic,
        "qualify_static",
        lambda **_kwargs: {
            "status": "PASS",
            "bindings": dict(bindings),
            "adapter": {
                "source_sha256": semantic.ADAPTER_SHA256,
                "source_bytes": semantic.ADAPTER_BYTES,
                "tensors": semantic.ADAPTER_TENSORS,
                "parameters": semantic.ADAPTER_PARAMETERS,
                "payloads": list(semantic.ADAPTER_PAYLOADS),
                "payload_bytes_verified": False,
            },
            "git_head": "1" * 40,
        },
    )
    documents = []
    for index in range(6):
        relative = semantic.DOCUMENT_PATHS[index]
        path = tmp_path / relative
        path.parent.mkdir(parents=True)
        body = _json_bytes(_document(index))
        path.write_bytes(body)
        documents.append(
            {
                "index": index,
                "path": relative,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "conversation_id": semantic.CONVERSATION_IDS[index],
                "family_id": semantic.FAMILY_IDS[index],
                "split": "withheld",
            }
        )
    value = {
        "schema_version": 1,
        "kind": "source-interpreter-semantic-accepted-inputs",
        "status": "ACCEPTED",
        "accepted_review_git_commit": semantic.ACCEPTED_SEMANTIC_COMMIT,
        "bindings": bindings,
        "documents": documents,
    }
    path = tmp_path / semantic.ACCEPTED_INPUTS_PATH.relative_to(semantic.ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))
    return path


def _contains_forbidden_target(value):
    if isinstance(value, dict):
        return any(
            key in {"target", "targets", "target_ids", "target_text", "labels"}
            or _contains_forbidden_target(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_target(item) for item in value)
    return isinstance(value, str) and "SECRET-TARGET" in value


def test_prepare_binds_six_withheld_sources_and_separates_targets(
    tmp_path, monkeypatch
):
    accepted = _accepted_manifest(tmp_path, monkeypatch)
    output = tmp_path / semantic.PREPARED_DIR.relative_to(semantic.ROOT)
    receipt = semantic.prepare_packet(
        accepted,
        output,
        root=tmp_path,
        source=FakeSource,
        tokenizer="synthetic-tokenizer",
    )
    generation = json.loads((output / "generation-manifest.json").read_text())
    reference = json.loads((output / "reference-manifest.json").read_text())
    old_review = (
        tmp_path / "results/source-interpreter/semantic-review-astra.md"
    ).read_bytes()
    monkeypatch.setattr(
        semantic,
        "_git_blob",
        lambda _root, commit, relative: (
            old_review
            if commit == generation["preparation_git_head"]
            and relative == "results/source-interpreter/semantic-review-astra.md"
            else (_ for _ in ()).throw(AssertionError("unexpected Git blob"))
        ),
    )
    (tmp_path / "results/source-interpreter/semantic-review-astra.md").write_bytes(
        old_review + b"appended preparation audit\n"
    )
    assert len(semantic.validate_generation_manifest(generation, root=tmp_path)) == 18
    assert receipt["status"] == "PASS"
    assert len(generation["rows"]) == len(reference["rows"]) == 18
    assert not _contains_forbidden_target(generation)
    assert _contains_forbidden_target(reference)
    assert [row["row_index"] for row in generation["rows"]] == list(range(18))
    assert all(row["split"] == "withheld" for row in generation["rows"])
    assert generation["settings"] == semantic.fit.GENERATION_SETTINGS
    assert generation["reference_manifest_read_by_generation"] is False

    tainted = copy.deepcopy(generation)
    tainted["rows"][0]["target_text"] = "SECRET-TARGET"
    with pytest.raises(semantic.SemanticError, match="target"):
        semantic.validate_generation_manifest(tainted, root=tmp_path)

    bad = json.loads(accepted.read_text())
    bad["documents"][3]["sha256"] = "0" * 64
    accepted.write_bytes(_json_bytes(bad))
    with pytest.raises(semantic.SemanticError, match="hash|binding"):
        semantic.validate_accepted_manifest(bad, root=tmp_path)


def _generation_rows(count=18):
    return [
        {
            "row_index": index,
            "conversation_index": index // 3,
            "conversation_id": semantic.CONVERSATION_IDS[index // 3],
            "family_id": semantic.FAMILY_IDS[index // 3],
            "split": "withheld",
            "query_index": index % 3,
            "query_message_id": f"q-{index}",
            "task_handle": f"task-{index}",
            "source_prefix": [
                {
                    "message_id": f"q-{index}",
                    "role": "user",
                    "text": "synthetic",
                    "task_handle": f"task-{index}",
                }
            ],
            "visible_source_ids": [f"q-{index}"],
            "prefix_ids": [10 + index, 20 + index],
            "prefix_sha256": hashlib.sha256(
                _json_bytes([10 + index, 20 + index])
            ).hexdigest(),
            "prefix_length": 2,
            "context_with_output_tokens": 2050,
        }
        for index in range(count)
    ]


def _returned_call(mode, *, cap=False):
    return {
        "mode": mode,
        "status": "RETURNED",
        "generated_ids": [1, 2],
        "complete_output_ids": [10, 20, 1, 2],
        "decoded_bytes": 2,
        "whole_call_seconds": 0.25,
        "strict_output": {"valid": not cap, "error": "cap" if cap else None},
        "stop_facts": {
            "eos_present": not cap,
            "terminal_eos": not cap,
            "cap_reached": cap,
            "deadline_reached": False,
        },
        "resource_before": {},
        "resource_after": {},
    }


def test_current_base_assets_reject_same_size_changed_file(tmp_path):
    model_dir = tmp_path / "models/qwen3-4b-hf"
    model_dir.mkdir(parents=True)
    first = model_dir / "config.json"
    second = model_dir / "model.safetensors"
    first.write_bytes(b"config")
    second.write_bytes(b"weights")
    files = {}
    for path in (first, second):
        relative = str(path.relative_to(tmp_path))
        files[relative] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "matches_historical_original": True,
        }
    receipt_path = tmp_path / "base-assets.json"
    receipt_path.write_bytes(
        _json_bytes(
            {
                "schema_version": 1,
                "status": "LOCAL_BASE_BYTES_VERIFIED",
                "file_count": 2,
                "total_file_bytes": sum(item["bytes"] for item in files.values()),
                "files": files,
            }
        )
    )

    verified = semantic.verify_current_base_assets(receipt_path, root=tmp_path)
    assert verified["status"] == "CURRENT_BASE_BYTES_VERIFIED"
    assert verified["file_count"] == 2
    assert all(item["bytes_verified"] for item in verified["files"].values())

    second.write_bytes(b"WeightS")
    assert second.stat().st_size == files[str(second.relative_to(tmp_path))]["bytes"]
    with pytest.raises(semantic.SemanticError, match="base asset bytes differ"):
        semantic.verify_current_base_assets(receipt_path, root=tmp_path)


def test_loaded_adapter_must_equal_serialized_payload_with_same_shape():
    torch = pytest.importorskip("torch")
    serialized = {"layer.lora_A.weight": torch.tensor([[1.0, 2.0]])}
    loaded = {"layer.lora_A.weight": torch.tensor([[1.0, 3.0]])}

    with pytest.raises(semantic.SemanticError, match="serialized adapter state"):
        semantic.verify_loaded_adapter_state(serialized, loaded)

    receipt = semantic.verify_loaded_adapter_state(serialized, serialized)
    assert receipt["status"] == "LOADED_SERIALIZED_EXACT_MATCH"
    assert receipt["tensors"] == 1
    assert receipt["parameters"] == 2
    assert receipt["state"]["layer.lora_A.weight"]["sha256"]


def test_fixed_order_all_36_no_overwrite_and_cap_continues(tmp_path):
    calls = []

    def single_call(run, *, row, mode, **_kwargs):
        calls.append((row["row_index"], mode, Path(run)))
        value = _returned_call(mode, cap=len(calls) == 1)
        semantic._write_json(Path(run) / f"generation-{mode}.json", value)
        return value

    result = semantic.run_inference_schedule(
        tmp_path,
        rows=_generation_rows(),
        model=object(),
        tokenizer=object(),
        torch=object(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
        single_call=single_call,
        deadline_seconds=300,
    )
    expected = [
        (row, mode)
        for row in range(18)
        for mode in (("base", "adapter") if row % 2 == 0 else ("adapter", "base"))
    ]
    assert [(row, mode) for row, mode, _path in calls] == expected
    assert result["status"] == "COMPLETE"
    assert result["returned_calls"] == 36
    assert result["calls"][0]["cap_reached"] is True
    assert len({path for _row, _mode, path in calls}) == 18
    assert all((tmp_path / f"row-{row:02d}").is_dir() for row in range(18))


def test_technical_stop_makes_every_later_call_not_attempted(tmp_path):
    invoked = 0

    def single_call(run, *, mode, **_kwargs):
        nonlocal invoked
        invoked += 1
        value = (
            _returned_call(mode)
            if invoked == 1
            else {
                **_returned_call(mode),
                "status": "TECHNICAL_ERROR",
                "generated_ids": None,
                "complete_output_ids": None,
                "stop_facts": None,
            }
        )
        semantic._write_json(Path(run) / f"generation-{mode}.json", value)
        return value

    result = semantic.run_inference_schedule(
        tmp_path,
        rows=_generation_rows(),
        model=object(),
        tokenizer=object(),
        torch=object(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
        single_call=single_call,
    )
    assert result["status"] == "INCOMPLETE_TECHNICAL"
    assert invoked == 2
    assert [call["status"] for call in result["calls"][:3]] == [
        "RETURNED",
        "TECHNICAL_ERROR",
        "NOT_ATTEMPTED",
    ]
    assert len(result["calls"]) == 36


class FakeTensor:
    def __init__(self, values):
        self.values = copy.deepcopy(values)

    def tolist(self):
        return copy.deepcopy(self.values)

    def __getitem__(self, index):
        return FakeTensor(self.values[index])


class FakeTorch:
    long = "long"

    class cuda:
        @staticmethod
        def is_available():
            return False

        @staticmethod
        def synchronize():
            return None

    @staticmethod
    def tensor(values, **_kwargs):
        return FakeTensor(values)

    @staticmethod
    def ones_like(tensor):
        return FakeTensor([[1] * len(tensor.values[0])])

    @staticmethod
    def inference_mode():
        return contextlib.nullcontext()


class FakeLayer:
    disable_adapters = False
    active_adapters = ["semantic"]


class FakeModel:
    def __init__(self):
        from transformers import GenerationConfig

        self.layer = FakeLayer()
        self.config = type(
            "Config",
            (),
            {"use_cache": True, "_get_generation_parameters": lambda _self: {}},
        )()
        self.generation_config = GenerationConfig()
        self.calls = []

    def modules(self):
        return [self.layer]

    def get_base_model(self):
        return self

    @contextlib.contextmanager
    def disable_adapter(self):
        self.layer.disable_adapters = True
        try:
            yield
        finally:
            self.layer.disable_adapters = False

    def set_adapter(self, name, *, inference_mode):
        assert inference_mode is True
        self.layer.disable_adapters = False
        self.layer.active_adapters = [name]

    def _prepare_generation_config(self, config, **kwargs):
        from transformers.generation.utils import GenerationMixin

        return GenerationMixin._prepare_generation_config(self, config, **kwargs)

    def _prepare_generated_length(self, **kwargs):
        from transformers.generation.utils import GenerationMixin

        return GenerationMixin._prepare_generated_length(self, **kwargs)

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        suffix = list(b'{"obligations":[]}') + [semantic.EOS_TOKEN_ID]
        return SimpleNamespace(
            sequences=FakeTensor([kwargs["input_ids"].values[0] + suffix])
        )


class FakeTokenizer:
    @staticmethod
    def decode(ids, **_kwargs):
        return bytes(ids).decode()


def test_schedule_consumes_the_real_fit_single_call_for_each_mode(tmp_path):
    model = FakeModel()
    result = semantic.run_inference_schedule(
        tmp_path,
        rows=_generation_rows(),
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
    )
    assert result["status"] == "COMPLETE"
    assert len(model.calls) == 36
    assert all(call["max_new_tokens"] == 2048 for call in model.calls)
    assert all("labels" not in call for call in model.calls)
    assert len(semantic.validate_complete_calls(tmp_path)) == 36


class ManualClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.mark.parametrize("delayed_ordinal", [0, 35])
def test_late_final_call_publication_stops_and_complete_consumer_rejects(
    tmp_path, monkeypatch, delayed_ordinal
):
    clock = ManualClock()
    original_write = semantic._write_json

    def delayed_write(path, value):
        original_write(path, value)
        if (
            Path(path).name == f"call-{delayed_ordinal:02d}.json"
            and value.get("status") in {"RETURNED", "COMPLETION_PENDING"}
            and value.get("requested_status", "RETURNED") == "RETURNED"
        ):
            clock.now = 1.01

    monkeypatch.setattr(semantic, "_write_json", delayed_write)
    model = FakeModel()
    result = semantic.run_inference_schedule(
        tmp_path,
        rows=_generation_rows(),
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
        deadline_seconds=1.0,
        clock=clock,
    )
    assert result["status"] == "INCOMPLETE_DEADLINE"
    assert len(model.calls) == delayed_ordinal + 1
    assert result["returned_calls"] == delayed_ordinal
    delayed = result["calls"][delayed_ordinal]
    assert delayed["status"] == "UNAVAILABLE"
    assert delayed["generated_ids_available"] is True
    assert delayed["within_deadline_confirmed"] is False
    with pytest.raises(semantic.SemanticError, match="36|complete|confirmation"):
        semantic.validate_complete_calls(tmp_path)


def test_late_or_missing_completion_confirmation_cannot_derive_returned(
    tmp_path, monkeypatch
):
    clock = ManualClock()
    original_write = semantic._write_json

    def delayed_confirmation(path, value):
        original_write(path, value)
        if (
            Path(path).name == "call-00-completion.json"
            and value.get("status") == "COMPLETE"
            and "completion_records_observed_monotonic" in value
        ):
            clock.now = 1.01

    monkeypatch.setattr(semantic, "_write_json", delayed_confirmation)
    model = FakeModel()
    result = semantic.run_inference_schedule(
        tmp_path,
        rows=_generation_rows(),
        model=model,
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
        deadline_seconds=1.0,
        clock=clock,
    )
    assert result["status"] == "INCOMPLETE_DEADLINE"
    assert len(result["calls"]) == 36
    assert len(model.calls) == 1
    assert result["calls"][0]["status"] == "UNAVAILABLE"
    assert result["calls"][0]["generated_ids_available"] is True

    clean = tmp_path / "missing"
    clean.mkdir()
    complete = semantic.run_inference_schedule(
        clean,
        rows=_generation_rows(),
        model=FakeModel(),
        tokenizer=FakeTokenizer(),
        torch=FakeTorch(),
        adapter_name="semantic",
        stopping_list=lambda values: values,
    )
    assert complete["status"] == "COMPLETE"
    (clean / "call-35-completion.json").unlink()
    assert semantic.partial_call_records(clean)[35]["status"] == "UNAVAILABLE"
    with pytest.raises(semantic.SemanticError, match="36|complete|confirmation"):
        semantic.validate_complete_calls(clean)


def _child_script(tmp_path, body):
    path = tmp_path / f"child-{hashlib.sha256(body.encode()).hexdigest()[:10]}.py"
    path.write_text(body)
    return [sys.executable, str(path)]


def test_supervisor_observes_nested_publication_deadline_and_unknown_output(tmp_path):
    run = tmp_path / "run-timeout"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned")
    body = (
        "import json,pathlib,sys,time\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "records=[]\n"
        "for i in range(36):\n"
        " mode=('base','adapter')[i%2]\n"
        " value={'ordinal':i,'row_index':i//2,'mode':mode,'status':'NOT_ATTEMPTED'}\n"
        " (run/f'call-{i:02d}.json').write_text(json.dumps(value))\n"
        "stage={'stage':'generation-base','status':'COMPLETION_PENDING',"
        "'hard_deadline_monotonic':time.monotonic()+0.2,'row_index':0}\n"
        "(run/'current-stage.json').write_text(json.dumps(stage))\n"
        "value={'ordinal':0,'row_index':0,'mode':'base','status':'INTENT'}\n"
        "(run/'call-00.json').write_text(json.dumps(value))\n"
        "time.sleep(30)\n"
    )
    code, lifecycle = semantic.supervise_child(
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
    assert lifecycle["timed_out_stage"] == "generation-base"
    assert lifecycle["calls"][0]["status"] == "UNAVAILABLE"
    assert lifecycle["calls"][0]["generated_ids_available"] is None
    assert all(call["status"] == "NOT_ATTEMPTED" for call in lifecycle["calls"][1:])
    assert lifecycle["receipt_publication_tail"]["bounded_by_outer_observer"] is True
    assert lifecycle["owned_child_cleanup_confirmed"] is True
    assert lifecycle["model_cleanup_confirmed"] is False
    assert not flag.exists()


def test_complete_validation_rejects_35_returned_and_one_unknown(tmp_path):
    semantic.initialize_call_records(tmp_path, _generation_rows())
    for ordinal in range(35):
        value = json.loads((tmp_path / f"call-{ordinal:02d}.json").read_text())
        value.update(status="RETURNED", receipt_path=f"row-{ordinal // 2:02d}/x.json")
        semantic._write_json(tmp_path / f"call-{ordinal:02d}.json", value)
    unknown = json.loads((tmp_path / "call-35.json").read_text())
    unknown["status"] = "INTENT"
    semantic._write_json(tmp_path / "call-35.json", unknown)
    with pytest.raises(semantic.SemanticError, match="36|complete"):
        semantic.validate_complete_calls(tmp_path)
    partial = semantic.partial_call_records(tmp_path)
    assert sum(call["status"] == "RETURNED" for call in partial) == 0
    assert all(call["status"] == "UNAVAILABLE" for call in partial)
    assert all(call["completion_publication_confirmed"] is False for call in partial)


def test_partial_accounting_recovers_raw_ids_without_claiming_call_complete(tmp_path):
    rows = _generation_rows()
    semantic.initialize_call_records(tmp_path, rows)
    intent = json.loads((tmp_path / "call-00.json").read_text())
    intent.update(status="INTENT", generated_ids_available=None)
    semantic._write_json(tmp_path / "call-00.json", intent)
    nested = tmp_path / "row-00"
    nested.mkdir()
    semantic._write_json(
        nested / "generation-base.json",
        {
            **_returned_call("base"),
            "generated_ids": [71, 72, 73],
            "decoded_bytes": 3,
        },
    )
    call = semantic.partial_call_records(tmp_path)[0]
    assert call["status"] == "UNAVAILABLE"
    assert call["generated_ids_available"] is True
    assert call["generated_tokens"] == 3
    assert call["decoded_bytes"] == 3
    assert call["raw_receipt_status"] == "RETURNED"
    assert call["within_deadline_confirmed"] is False
    assert call["availability_interpretation"] == (
        "raw output bytes are available; final call-completion and "
        "within-deadline confirmation are unavailable"
    )


def test_import_dry_and_direct_qualification_are_artifact_only(tmp_path):
    imported = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import scripts.source_interpreter_semantic; "
            "assert 'torch' not in sys.modules; assert 'peft' not in sys.modules; "
            "assert 'transformers' not in sys.modules",
        ],
        cwd=semantic.ROOT,
        check=False,
    )
    assert imported.returncode == 0
    run = semantic.RESULTS_DIR / f"run-dry-{os.getpid()}-{time.time_ns()}"
    dry = subprocess.run(
        [sys.executable, str(semantic.__file__), "--run-dir", str(run)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry.returncode == 0, dry.stderr
    plan = json.loads(dry.stdout)
    assert plan["execute"] is False
    assert plan["scheduled_calls"] == 36
    assert plan["outer_observer"]["initial_training_seconds"] == 660
    assert plan["outer_observer"]["initial_bound_semantics"] == (
        "semantic startup through durable first generation intent; no training"
    )
    assert not run.exists()

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    qualified = subprocess.run(
        [sys.executable, str(semantic.__file__), "--_qualify-only"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert qualified.returncode == 0, qualified.stderr
    receipt = json.loads(qualified.stdout)
    assert receipt["status"] == "PASS"
    assert receipt["model_loaded"] is False
    assert receipt["tokenizer_loaded"] is False
    assert receipt["accepted_documents_read"] is False

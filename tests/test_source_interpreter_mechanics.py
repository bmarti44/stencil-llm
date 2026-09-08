import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import torch

from scripts import source_interpreter_mechanics as mechanics


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _row_fixture(tmp_path: Path):
    document = {
        "schema_version": 1,
        "conversation_id": "conversation",
        "family_id": "family",
        "split": "fit",
        "messages": [
            {
                "message_id": f"m{index}",
                "role": "user",
                "task_handle": f"task-{index}",
                "text": f"request {index}",
            }
            for index in range(3)
        ],
        "queries": [
            {
                "message_id": f"m{index}",
                "target": {
                    "obligations": [
                        {"text": f"rule {index}", "source_ids": [f"m{index}"]}
                    ]
                },
            }
            for index in range(3)
        ],
    }
    body = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    source_path = tmp_path / "reviewed.json"
    source_path.write_bytes(body)
    source_prefix = document["messages"][:1]
    target_text = json.dumps(
        document["queries"][0]["target"], sort_keys=True, separators=(",", ":")
    )
    source_text = json.dumps(source_prefix, sort_keys=True, separators=(",", ":"))
    prompt = [
        {"role": "system", "content": mechanics.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": mechanics.USER_PROMPT.format(
                task_handle="task-0", source_events=source_text
            ),
        },
    ]
    row = {
        "conversation_id": "conversation",
        "family_id": "family",
        "split": "fit",
        "query_index": 0,
        "query_message_id": "m0",
        "task_handle": "task-0",
        "message_count": 3,
        "source_prefix": source_prefix,
        "source_prefix_sha256": _sha(source_text.encode()),
        "prompt_messages": prompt,
        "prompt_messages_sha256": _sha(
            json.dumps(prompt, sort_keys=True, separators=(",", ":")).encode()
        ),
        "prefix_text": "rendered-prefix",
        "prefix_text_sha256": _sha(b"rendered-prefix"),
        "target_text": target_text,
        "target_text_sha256": _sha(target_text.encode()),
        "prefix_ids": [10, 11],
        "target_ids": [20, 21],
        "target_with_eos_ids": [20, 21, 99],
        "input_ids": [10, 11, 20, 21, 99],
        "labels": [-100, -100, 20, 21, 99],
        "attention_mask": [1, 1, 1, 1, 1],
        "loss_positions": [2, 3, 4],
        "prefix_length": 2,
        "target_length": 3,
        "full_length": 5,
        "eos_token_id": 99,
        "supervised_tokens": 3,
        "masked_prefix_tokens": 2,
        "target_eos_count": 1,
        "boundary_construction": "separate_prefix_target_ids",
        "joint_tokenization_equal": True,
    }
    input_receipt = {
        "path": str(source_path),
        "bytes": len(body),
        "sha256": _sha(body),
        "conversation_id": "conversation",
        "family_id": "family",
        "split": "fit",
        "read_error": None,
        "parse_error": None,
    }
    manifest_entry = {
        "path": source_path.name,
        "sha256": _sha(body),
        "conversation_id": "conversation",
        "family_id": "family",
        "split": "fit",
    }
    return row, document, input_receipt, manifest_entry


def test_exact_causal_target_positions_and_preload_rejections(tmp_path):
    row, document, receipt, entry = _row_fixture(tmp_path)
    result = mechanics.validate_training_row(
        row,
        document=document,
        input_receipt=receipt,
        manifest_entry=entry,
        root=tmp_path,
    )
    assert result["label_positions"] == [2, 3, 4]
    assert result["causal_logit_positions"] == [1, 2, 3]
    assert result["supervised_tokens"] == 3

    bad = copy.deepcopy(row)
    bad["labels"] = [-100] * 5
    with pytest.raises(ValueError, match="labels|supervision"):
        mechanics.validate_training_row(
            bad,
            document=document,
            input_receipt=receipt,
            manifest_entry=entry,
            root=tmp_path,
        )

    bad = copy.deepcopy(row)
    bad["target_with_eos_ids"][-1] = 98
    with pytest.raises(ValueError, match="EOS|boundary"):
        mechanics.validate_training_row(
            bad,
            document=document,
            input_receipt=receipt,
            manifest_entry=entry,
            root=tmp_path,
        )

    bad = copy.deepcopy(row)
    bad["input_ids"] = bad["input_ids"][:-1]
    with pytest.raises(ValueError, match="length|truncated"):
        mechanics.validate_training_row(
            bad,
            document=document,
            input_receipt=receipt,
            manifest_entry=entry,
            root=tmp_path,
        )

    wrong = dict(entry, sha256="0" * 64)
    with pytest.raises(ValueError, match="input binding"):
        mechanics.validate_training_row(
            row,
            document=document,
            input_receipt=receipt,
            manifest_entry=wrong,
            root=tmp_path,
        )


class TinyAdapter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.original = torch.nn.Parameter(torch.tensor([2.0]), requires_grad=False)
        self.lora_A = torch.nn.Parameter(torch.tensor([1.0]))
        self.lora_B = torch.nn.Parameter(torch.tensor([1.0]))

    def forward(self, value):
        return self.original * value + self.lora_A * value + self.lora_B * 0


def test_optimizer_frozen_gradients_and_update_evidence():
    model = TinyAdapter()
    optimizer = torch.optim.AdamW([model.lora_A, model.lora_B], lr=0.1, weight_decay=0)
    before = mechanics.capture_parameter_state(model)
    model(torch.tensor([1.0])).square().sum().backward()
    optimizer.step()
    evidence = mechanics.validate_optimizer_step(model, optimizer, before)
    assert evidence["nonzero_gradient_tensors"] == 1
    assert evidence["nonzero_update_tensors"] == 1
    assert evidence["original_parameter_identities_unchanged"] is True
    assert evidence["original_parameter_bytes_unchanged"] is True

    with torch.no_grad():
        model.original.add_(1)
    with pytest.raises(RuntimeError, match="original parameter bytes changed"):
        mechanics.validate_frozen_originals(model, before["originals"])

    detached = TinyAdapter()
    detached_optimizer = torch.optim.AdamW(
        [detached.lora_A, detached.lora_B], lr=0.1, weight_decay=0
    )
    detached_before = mechanics.capture_parameter_state(detached)
    detached(torch.tensor([1.0])).square().sum().backward()
    detached.lora_B.grad = None
    detached_optimizer.step()
    with pytest.raises(RuntimeError, match="absent gradient"):
        mechanics.validate_optimizer_step(detached, detached_optimizer, detached_before)

    unchanged = TinyAdapter()
    unchanged_optimizer = torch.optim.AdamW(
        [unchanged.lora_A, unchanged.lora_B], lr=0.1, weight_decay=0
    )
    unchanged_before = mechanics.capture_parameter_state(unchanged)
    unchanged(torch.tensor([1.0])).square().sum().backward()
    with pytest.raises(RuntimeError, match="no adapter update"):
        mechanics.validate_optimizer_step(
            unchanged, unchanged_optimizer, unchanged_before
        )

    wrong_optimizer = torch.optim.AdamW(
        [model.original, model.lora_A, model.lora_B], lr=0.1
    )
    with pytest.raises(RuntimeError, match="optimizer"):
        mechanics.validate_optimizer_step(model, wrong_optimizer, before)


def test_adapter_state_and_byte_archive_roundtrip(tmp_path):
    expected = {"lora_A.weight": torch.tensor([1.0], dtype=torch.float32)}
    mechanics.compare_adapter_states(expected, copy.deepcopy(expected))
    with pytest.raises(RuntimeError, match="keys"):
        mechanics.compare_adapter_states(expected, {})
    with pytest.raises(RuntimeError, match="dtype"):
        mechanics.compare_adapter_states(
            expected, {"lora_A.weight": expected["lora_A.weight"].double()}
        )
    with pytest.raises(RuntimeError, match="bytes"):
        mechanics.compare_adapter_states(
            expected, {"lora_A.weight": torch.tensor([2.0])}
        )

    source = tmp_path / "adapter_model.safetensors"
    body = bytes(range(251)) * 101
    source.write_bytes(body)
    archive = tmp_path / "archive"
    manifest = mechanics.archive_file(source, archive, max_part_bytes=997)
    assert max(part["bytes"] for part in manifest["parts"]) <= 997
    rebuilt = tmp_path / "rebuilt.safetensors"
    mechanics.reconstruct_archive(manifest, archive, rebuilt)
    assert rebuilt.read_bytes() == body
    (archive / manifest["parts"][1]["name"]).write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="archive part"):
        mechanics.reconstruct_archive(manifest, archive, tmp_path / "bad")


def test_reload_key_receipt_ignores_base_missing_but_rejects_adapter_issues():
    result = type(
        "LoadResult",
        (),
        {"missing_keys": ["base_model.embed.weight"], "unexpected_keys": []},
    )()
    receipt = mechanics._adapter_load_receipt(result)
    assert receipt["reported_missing_keys"] == ["base_model.embed.weight"]
    assert receipt["missing_adapter_keys"] == []

    result = type(
        "LoadResult",
        (),
        {
            "missing_keys": ["base_model.layer.lora_A.roundtrip.weight"],
            "unexpected_keys": [],
        },
    )()
    with pytest.raises(RuntimeError, match="missing or unexpected adapter"):
        mechanics._adapter_load_receipt(result)


def _complete_result():
    return {
        "schema_version": 1,
        "kind": "source-interpreter-mechanics-result",
        "status": "COMPLETE",
        "mechanical_pass": True,
        "bindings": {"input": "bound"},
        "settings": {"updates": 4},
        "stage_receipts": [{"stage": "start"}, {"stage": "reload"}],
        "step_receipts": [
            {
                "ordinal": ordinal,
                "classification": "warm-up" if ordinal == 0 else "timed",
                "update_completed": True,
            }
            for ordinal in range(4)
        ],
        "original_parameters": {"unchanged": True},
        "adapter_roundtrip": {"exact": True},
        "resource_receipts": [{"stage": "exit"}],
        "timings": {"total_seconds": 0.1},
        "post_reload": {"loss": 1.0, "optimizer_update": False},
    }


def _child_script(tmp_path: Path, body: str) -> list[str]:
    script = tmp_path / (
        "child-" + hashlib.sha256(body.encode()).hexdigest()[:8] + ".py"
    )
    script.write_text(body, encoding="utf-8")
    return [sys.executable, str(script)]


def test_supervisor_happy_and_failing_children_preserve_receipts(tmp_path):
    run = tmp_path / "happy"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned", encoding="utf-8")
    result = repr(_complete_result())
    command = _child_script(
        tmp_path,
        "import json, pathlib, sys\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "(run/'partial.json').write_text(json.dumps({'stage':'worked'}))\n"
        f"(run/'result.json').write_text(json.dumps({result}))\n",
    ) + [str(run)]
    code, lifecycle = mechanics.supervise_child(
        run,
        command,
        run_flag=flag,
        pid_registry=tmp_path / "pids",
        reservation_seconds=2,
        termination_reserve_seconds=0.5,
    )
    assert code == 0
    assert lifecycle["status"] == "COMPLETE"
    assert lifecycle["warm_up_updates"] == 1
    assert not flag.exists()
    assert (run / "partial.json").exists()

    failed = tmp_path / "failed"
    failed.mkdir()
    flag.write_text("owned", encoding="utf-8")
    command = _child_script(
        tmp_path,
        "import json, pathlib, sys\n"
        "run=pathlib.Path(sys.argv[1])\n"
        "(run/'partial.json').write_text('partial')\n"
        "(run/'step-00.json').write_text(json.dumps({"
        "'ordinal':0,'classification':'warm-up','update_completed':True}))\n"
        "(run/'step-01.json').write_text(json.dumps({"
        "'ordinal':1,'classification':'timed','update_completed':True}))\n"
        "raise SystemExit(7)\n",
    ) + [str(failed)]
    code, lifecycle = mechanics.supervise_child(
        failed,
        command,
        run_flag=flag,
        pid_registry=tmp_path / "pids",
        reservation_seconds=2,
        termination_reserve_seconds=0.5,
    )
    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_CHILD"
    assert lifecycle["child_exit_code"] == 7
    assert lifecycle["updates"] == 2
    assert lifecycle["warm_up_updates"] == 1
    assert lifecycle["timed_updates"] == 1
    assert (failed / "partial.json").exists()
    assert not flag.exists()


def test_supervisor_timeout_stops_only_owned_child_and_preserves_foreign_flag(tmp_path):
    run = tmp_path / "timeout"
    run.mkdir()
    own_flag = tmp_path / "RUNNING.flag"
    own_flag.write_text("owned", encoding="utf-8")
    foreign_flag = tmp_path / "foreign" / "RUNNING.flag"
    foreign_flag.parent.mkdir()
    foreign_flag.write_text("foreign", encoding="utf-8")
    foreign = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        command = _child_script(
            tmp_path,
            "import pathlib, sys, time\n"
            "(pathlib.Path(sys.argv[1])/'partial.json').write_text('started')\n"
            "time.sleep(30)\n",
        ) + [str(run)]
        code, lifecycle = mechanics.supervise_child(
            run,
            command,
            run_flag=own_flag,
            pid_registry=tmp_path / "pids",
            reservation_seconds=0.6,
            termination_reserve_seconds=0.3,
        )
        assert code == 2
        assert lifecycle["status"] == "INCOMPLETE_TIMEOUT"
        assert lifecycle["child_exit_confirmed"] is True
        assert foreign.poll() is None
        assert foreign_flag.read_text() == "foreign"
        assert not own_flag.exists()
        assert (run / "partial.json").exists()
    finally:
        foreign.terminate()
        foreign.wait(timeout=2)


def test_supervisor_reaps_child_when_registration_fails(tmp_path):
    run = tmp_path / "registration-failure"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned", encoding="utf-8")
    command = _child_script(tmp_path, "import time\ntime.sleep(30)\n")
    processes = []

    def start(*args, **kwargs):
        process = subprocess.Popen(*args, **kwargs)
        processes.append(process)
        return process

    def fail_registration(*_args, **_kwargs):
        raise OSError("registry unavailable")

    code, lifecycle = mechanics.supervise_child(
        run,
        command,
        run_flag=flag,
        pid_registry=tmp_path / "pids",
        reservation_seconds=1,
        termination_reserve_seconds=0.5,
        popen=start,
        register=fail_registration,
    )
    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_LAUNCH"
    assert lifecycle["child_exit_confirmed"] is True
    assert lifecycle["termination_requested"] is True
    assert lifecycle["termination_reason"] == "supervisor-error"
    assert processes[0].poll() is not None
    assert not flag.exists()


def test_incomplete_result_cannot_pass(tmp_path):
    result = _complete_result()
    result["step_receipts"] = result["step_receipts"][1:]
    with pytest.raises(RuntimeError, match="four|warm-up"):
        mechanics.validate_completion(result)
    result = _complete_result()
    result["status"] = "INCOMPLETE"
    with pytest.raises(RuntimeError, match="COMPLETE"):
        mechanics.validate_completion(result)


def test_import_and_dry_run_have_no_heavy_side_effects(tmp_path, capsys, monkeypatch):
    check = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import scripts.source_interpreter_mechanics; "
            "assert 'torch' not in sys.modules; "
            "assert 'transformers' not in sys.modules; "
            "assert 'peft' not in sys.modules",
        ],
        cwd=mechanics.ROOT,
        check=False,
    )
    assert check.returncode == 0
    run = mechanics.RESULTS_DIR / f"run-dry-{os.getpid()}-{time.time_ns()}"
    flag = tmp_path / "RUNNING.flag"
    monkeypatch.setattr(mechanics, "RUN_FLAG", flag)
    assert mechanics.main(["--run-dir", str(run)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["execute"] is False
    assert plan["settings"] == mechanics.SETTINGS
    assert plan["reservation_seconds"] == 600
    assert plan["working_seconds"] == 585
    assert not run.exists()
    assert not flag.exists()

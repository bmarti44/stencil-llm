"""CPU transport and driver consumer checks; no server or GPU needed."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from stencil.focus import slab2 as s


def driver():
    path = Path(__file__).parents[1] / "scripts/composition_pilot5.py"
    spec = importlib.util.spec_from_file_location("composition_pilot5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vllm_truncation_through_real_driver(tmp_path):
    d = driver()
    e = s.generate_episode()
    requests = []

    def factory(episode, arm, turn):
        text = s.reference(episode, turn)
        ids = list(s.qwen_encode(text))
        if turn:
            ids += list(s.qwen_encode("<|im_end|>"))

        def transport(payload):
            requests.append(payload)
            return {
                "choices": [
                    {
                        "text": text,
                        "token_ids": ids,
                        "finish_reason": "length" if turn == 0 else "stop",
                    }
                ],
                "usage": {"completion_tokens": len(ids)},
            }

        return d.VLLMDecoder("http://unused/v1", "stub", transport)

    lane = d.run_lane(tmp_path / "lane", e, "R", factory)
    first = lane["records"][0]
    assert first["truncated"] and first["execution"]["truncated"]
    assert not first["execution"]["executed"]
    assert first["execution"]["category"] == "truncated"
    assert all(
        row["outcome"]["floor_pending"] and row["outcome"]["success"] is None
        for row in lane["records"]
    )
    journal = [
        json.loads(line)
        for line in (tmp_path / "lane/loop.jsonl").read_text().splitlines()
    ]
    assert journal[0]["truncated"] is True
    assert journal[-1]["eos"] == s.qwen_encode("<|im_end|>")[0]
    assert journal[-1]["output_token_ids"][-1] != journal[-1]["eos"]
    assert lane["records"][-1]["output_tokens"] == journal[-1]["output_token_count"] + 1
    assert journal[0]["output_token_count"] == first["output_tokens"]
    assert all(
        request["max_tokens"] == 2048 and isinstance(request["prompt"], list)
        for request in requests
    )
    assert not lane["records"][-1]["execution"]["breakage"]


def test_complete_cpu_driver_floor_and_cost(tmp_path):
    d = driver()
    summary = d.run_pilot(tmp_path / "pilot", d.stub_factory, cpu_stub=True)
    assert len(summary["lanes"]) == 32
    assert summary["projected_gpu_hours"] is None
    assert summary["lane_seconds"] is None
    assert not summary["reading"]["eligible"]
    assert summary["reading"]["r_final_success"] == 8
    floor = json.loads((tmp_path / "pilot/floor.json").read_text())
    assert len(floor["traits"]["delivery"]["opportunity_episodes"]) >= 7
    scored = json.loads((tmp_path / "pilot/scored.json").read_text())
    assert len(scored) == 512 and all(row["outcome"]["success"] for row in scored)
    assert all(row["lane_seconds"] is None for row in summary["lanes"])


def test_driver_cost_rule_and_adapter_validation(tmp_path):
    d = driver()
    with pytest.raises(ValueError, match="fallback"):
        d.run_pilot(tmp_path / "bad", d.stub_factory, n_rounds=12)
    with pytest.raises(ValueError, match="max_workers"):
        d.run_pilot(tmp_path / "bad", d.stub_factory, max_workers=3)
    adapter = d.VLLMDecoder(
        "unused",
        "stub",
        lambda payload: {"choices": [{"text": "", "finish_reason": "stop"}]},
    )
    with pytest.raises(ValueError, match="token_ids"):
        adapter(SimpleNamespace(prompt_ids=(1,)))
    with pytest.raises(ValueError, match="context"):
        adapter(SimpleNamespace(prompt_ids=(1,) * 32768))


def test_fallback_floor_is_complete():
    records = []
    for e in range(8):
        for i in range(12):
            records.append(
                dict(
                    episode_id=f"slab2-dev-{e:02}",
                    arm="T",
                    turn=i,
                    outcome=dict(
                        observed=True,
                        applicable=dict.fromkeys(s.TRAITS, True),
                        satisfied=dict.fromkeys(s.TRAITS, True),
                        trait_denominators=dict.fromkeys(s.TRAITS, 1),
                    ),
                )
            )
    assert s.freeze_t_floor(records, n_rounds=12)["eligible_traits"] == list(s.TRAITS)
    with pytest.raises(ValueError):
        s.freeze_t_floor(records)


def test_measured_lane_allocations_with_cpu_injected_decoder(tmp_path):
    # Simulated clock/decoder tests GPU accounting without touching a GPU/server.
    d = driver()
    ticks = iter(range(100))
    summary = d.run_pilot(
        tmp_path / "simulated",
        d.stub_factory,
        clock=lambda: next(ticks),
        load_seconds=10,
    )
    assert summary["gpu_held_seconds"] == 17
    assert sum(lane["lane_seconds"] for lane in summary["lanes"]) == 17
    assert all(lane["concurrent_lanes"] == 4 for lane in summary["lanes"])
    assert summary["projected_gpu_hours"] == s.measured_projection(
        summary["lane_seconds"], load_seconds=10
    )
    assert all(len(v) == 8 for v in summary["output_tokens_per_arm"].values())

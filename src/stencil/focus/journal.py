"""Same-run JSONL provenance; null means unavailable, never reconstructed."""

import json
from pathlib import Path

FIELDS = frozenset(
    {
        "request_id",
        "raw_messages",
        "rendered_messages",
        "raw_token_ids",
        "rendered_token_ids",
        "source_events",
        "classifier_inputs",
        "classifier_decisions",
        "before_versions",
        "after_versions",
        "before_live_mask",
        "after_live_mask",
        "defaults",
        "applicability",
        "output",
        "output_token_ids",
        "eos",
        "truncated",
        "attempted_tool_calls",
        "executed_tool_calls",
        "tool_results",
        "artifact_hashes",
        "started_at",
        "finished_at",
        "cpu_seconds",
        "wall_seconds",
        "gpu_held_seconds",
        "input_token_count",
        "output_token_count",
        "actuator",
        "bias_hash",
        "whole_body_intervals",
        "keep_mask",
        "absolute_positions",
        "failures",
        "fallback_reasons",
        "oracle_checker_results",
    }
)


class Journal:
    def __init__(self, path):
        self.path = Path(path)

    def append(self, record):
        if set(record) != FIELDS:
            raise ValueError(f"journal field mismatch: {set(record) ^ FIELDS}")
        encoded = (
            json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
            + "\n"
        )
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()

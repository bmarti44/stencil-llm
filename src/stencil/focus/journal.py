"""Same-run JSONL provenance; null means unavailable, never reconstructed."""

import json
from copy import deepcopy
from pathlib import Path

FIELDS = frozenset(
    {
        "request_id",
        "journal_cursor",
        "request_bindings",
        "register_events",
        "event_generations",
        "experimental_flag_state",
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
    def __init__(self, path, *, checker=None):
        """checker(record) returns hidden harness results for this round.

        Invoked after generation/restoration, before this record is serialized.
        The callback receives an isolated copy; results never enter model inputs.
        No checker means an empty result list, not a reconstructed placeholder.
        """
        self.path = Path(path)
        self._checker = checker

    def append(self, record):
        if set(record) != FIELDS:
            raise ValueError(f"journal field mismatch: {set(record) ^ FIELDS}")
        record = deepcopy(record)
        if self._checker is not None:
            record["oracle_checker_results"] = self._checker(deepcopy(record))
        encoded = (
            json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
            + "\n"
        )
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()

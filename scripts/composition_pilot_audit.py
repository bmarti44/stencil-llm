"""Re-score saved DEV outputs and validate provenance on CPU; no trunk load."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

from stencil.focus.journal import FIELDS
from stencil.focus.slab import TOKENIZER_PATH, Executor, bank, check, materialize


def audit(root):
    rows = [json.loads(x) for x in (root / "records.jsonl").read_text().splitlines()]
    episodes = {e.episode_id: e for e in bank()}
    tokenizer = Tokenizer.from_file(str(TOKENIZER_PATH))
    seen, executors, next_round = set(), {}, {}
    hidden_count = 0
    with tempfile.TemporaryDirectory() as temp:
        for r in rows:
            assert set(r) == FIELDS
            d = r["oracle_checker_results"][0]
            key = (d["mode"], d["episode"], d["arm"])
            rowkey = key + (d["round"],)
            assert rowkey not in seen
            seen.add(rowkey)
            assert d["round"] == next_round.get(key, 0)
            next_round[key] = d["round"] + 1
            assert (
                tokenizer.decode(r["output_token_ids"], skip_special_tokens=False)
                == r["output"]
            )
            assert r["output_token_count"] == len(r["output_token_ids"])
            assert r["input_token_count"] == len(r["rendered_token_ids"])
            assert len(r["output_token_ids"]) + (r["eos"] is not None) <= 512
            m = d["measurements"]
            assert 0 <= m["generated_forward_tokens"] <= r["output_token_count"]
            assert m["hidden_complete"] == (
                m["generated_forward_tokens"] == r["output_token_count"]
            )
            e = episodes[d["episode"]]
            if key not in executors:
                p = Path(temp).joinpath(*key)
                materialize(e, p)
                executors[key] = Executor(
                    p, json.loads((p / "public_tests.json").read_text())
                )
            ex = executors[key]
            feedback = ex.run(r["output"])
            outcome = check(e, d["round"], r["output"], ex, truncated=r["truncated"])
            assert outcome == d["outcome"], rowkey
            assert feedback["executed"] == d["execution"]["executed"]
            assert feedback["results"] == d["execution"]["results"]
            assert ex.hashes() == d["artifact_hashes"]
            assert r["actuator"] == "off" and not r["failures"]
            live = {
                v["entry"]["key"]: v["entry"]["value"]
                for v in r["applicability"]
                if "shadowed_by" not in v
            }
            assert live == dict(e.turns[d["round"]].live)
            assert (
                d["paired_gate"]["allowed"]
                and r["input_token_count"] <= d["paired_gate"]["bounds"][d["arm"]]
            )
            for h in d["hidden"]:
                path = root / h["path"]
                arr = np.load(path, allow_pickle=False)
                assert list(arr.shape) == h["shape"] == [5, 2048]
                assert str(arr.dtype) == h["dtype"] == "float16"
                assert hashlib.sha256(path.read_bytes()).hexdigest() == h["sha256"]
                if (
                    d["measurements"]["generated_forward_tokens"]
                    or "prompt_hidden" in h["path"]
                ):
                    assert np.isfinite(arr).all() and np.any(arr)
                hidden_count += 1
    result = dict(
        verified_rows=len(rows),
        hidden_files=hidden_count,
        unique_lanes=len(executors),
        duplicate_rows=0,
        same_run_scores_reproduce=True,
        live_views_match_gold=True,
        literal_outputs_match_ids=True,
        hidden_hashes_shapes_match=True,
        record_sha256=hashlib.sha256((root / "records.jsonl").read_bytes()).hexdigest(),
    )
    (root / "audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "results/quick-checks/composition-pilot",
    )
    audit(parser.parse_args().out)


if __name__ == "__main__":
    main()

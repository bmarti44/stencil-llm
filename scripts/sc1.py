"""SC1 CPU validation and prospectively gated setup/final execution.

Examples:
  uv run python scripts/sc1.py validate data/sc1/smoke
  uv run python scripts/sc1.py smoke
  uv run python scripts/sc1.py analyze BANK --manifest MANIFEST
      --setup-certificate CERT --out RUN

No model is loaded by validate/smoke/analyze. Setup and final require a frozen
production manifest, complete review evidence and a separately budgeted smoke
model-determinism certificate. CPU smoke cannot substitute for that certificate.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from stencil import sc1
from stencil import sc1_episodes as episodes

ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "src/stencil/sc1.py",
    "src/stencil/sc1_episodes.py",
    "scripts/sc1.py",
    "tests/test_sc1.py",
    "src/stencil/selector_v2.py",
    "src/stencil/bfcl.py",
    "src/stencil/qwen3.py",
    "src/stencil/stats.py",
    "pyproject.toml",
    "uv.lock",
)
CLASSIFIER_RECORD = "results/quick-checks/ft_final2_s0_sha256.txt"
CONTRACT = "data/sc1/AUTHOR-CONTRACT.md"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def load_tokenizer(trunk):
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(ROOT / f"models/qwen3-{trunk}-hf/tokenizer.json"))


def classifier_hashes():
    expected = {}
    for line in (ROOT / CLASSIFIER_RECORD).read_text().splitlines():
        h, path = line.split(maxsplit=1)
        expected[path.strip()] = h
    required = {
        "head.pt",
        "encoder/config.json",
        "encoder/model.safetensors",
        "encoder/tokenizer_config.json",
        "encoder/tokenizer.json",
    }
    if {
        str(Path(p).relative_to("data/classifier/model/ft")) for p in expected
    } != required:
        raise ValueError("LEG B classifier record incomplete")
    for path, h in expected.items():
        if sc1.file_hash(ROOT / path) != h:
            raise ValueError("LEG B classifier hash mismatch: " + path)
    return expected


def dependencies():
    return {
        name: importlib.metadata.version(name)
        for name in ("torch", "tokenizers", "transformers", "numpy", "pytest", "ruff")
    }


def build_manifest(bank, trunk, episode_rows, *, stage1=None, executable=None):
    files = {
        p: sc1.file_hash(ROOT / p)
        for p in (*CODE_FILES, CONTRACT, "LEDGER-PLAN.md", CLASSIFIER_RECORD)
    }
    classifier = classifier_hashes()
    files.update(classifier)
    for path in sorted((ROOT / "data/classifier/model/ft").rglob("*")):
        if path.is_file() and ".cache" not in path.parts:
            files[str(path.relative_to(ROOT))] = sc1.file_hash(path)
    paths = [ROOT / f"models/qwen3-{trunk}.pt"]
    paths += [
        ROOT / f"models/qwen3-{trunk}-hf/{name}"
        for name in (
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "generation_config.json",
        )
    ]
    paths.append(ROOT / "models/qwen3-1.7b-hf/config.json")
    for path in paths:
        files[str(path.relative_to(ROOT))] = sc1.file_hash(path)
    for path in sorted(Path(bank).glob("*.json")):
        if path.name.endswith((".source.json", ".episode.json")):
            files[str(path.resolve())] = sc1.file_hash(path)
    payload = {
        "schema": "sc1-manifest-v2",
        "trunk": trunk,
        "harness_commit": git("rev-parse", "HEAD"),
        "files": files,
        "classifier": classifier,
        "dependencies": dependencies(),
        "python": sys.version,
        "grammar": episodes.SCHEMA,
        "filler_hash": sc1.digest(episodes.FILLER),
        "deployment": {
            "dtype": "bfloat16",
            "numerics": "hf_compatible",
            "temperature": 0,
            "greedy": True,
            "max_new_tokens": 256,
            "deadline": 300,
            "eos_ids": [151645, 151643],
            "nonthinking_opener": sc1.OPENER,
            "initialization": "one resident model per invocation; no warmup",
            "max_prefix": sc1.MAX_PREFIX,
            "max_query": sc1.MAX_QUERY,
            "position_guard": 40960,
        },
        "episodes": [
            {
                "id": ep["id"],
                "pool": ep["pool"],
                "index": ep["index"],
                "hash": sc1.digest(ep),
                "order": episodes.commission_slot(ep["pool"], ep["index"])["order"],
                "setup_order": episodes.commission_slot(ep["pool"], ep["index"])[
                    "setup_order"
                ],
            }
            for ep in episode_rows
        ],
        "power": [
            sc1.exact_power(256, q, d)
            for q, d in ((0.1, 0.05), (0.2, 0.05), (0.3, 0.05), (0.2, 0.1))
        ],
        "stage1": stage1,
        "executable_freeze": executable,
        "production": all(ep["pool"] != "smoke" for ep in episode_rows),
    }
    for name in ("stage1", "executable_freeze"):
        if payload[name]:
            path = Path(payload[name]).resolve()
            files[str(path)] = sc1.file_hash(path)
            payload[name] = str(path)
    payload["manifest_id"] = sc1.digest(payload)
    return payload


def verify_manifest(path, *, production=False):
    manifest = json.loads(Path(path).read_text())
    if (
        sc1.digest({k: v for k, v in manifest.items() if k != "manifest_id"})
        != manifest["manifest_id"]
    ):
        raise ValueError("manifest hash mismatch")
    for filename, h in manifest["files"].items():
        if sc1.file_hash(ROOT / filename) != h:
            raise ValueError("frozen artifact hash mismatch: " + filename)
    if manifest["dependencies"] != dependencies() or manifest["python"] != sys.version:
        raise ValueError("frozen dependency/runtime mismatch")
    if manifest["classifier"] != classifier_hashes():
        raise ValueError("classifier identity mismatch")
    if production:
        if (
            not manifest["production"]
            or not manifest["stage1"]
            or not manifest["executable_freeze"]
        ):
            raise ValueError("production requires scientific and executable freezes")
        stage1 = json.loads(Path(manifest["stage1"]).read_text())
        if stage1.get("status") != "REGISTERED" or set(
            stage1.get("authors", {})
        ) != set(episodes.AUTHORS):
            raise ValueError("Stage 1 author/version manifest is not registered")
        for family, author in stage1["authors"].items():
            if any(
                not author.get(k)
                for k in (
                    "provider",
                    "immutable_version",
                    "settings",
                    "neutral_template",
                    "contract_hash",
                    "grammar_hash",
                )
            ):
                raise ValueError("unfrozen author configuration: " + family)
            if author["contract_hash"] != manifest["files"][CONTRACT] or author[
                "grammar_hash"
            ] != sc1.digest(episodes.SCHEMA):
                raise ValueError("author contract/grammar mismatch")
        frozen = verify_manifest(manifest["executable_freeze"])
        for key in (*CODE_FILES, CONTRACT):
            if frozen["files"][key] != manifest["files"][key]:
                raise ValueError("production executable differs from Stage 2")
        if (
            frozen["deployment"] != manifest["deployment"]
            or frozen["trunk"] != manifest["trunk"]
        ):
            raise ValueError("deployment differs from Stage 2")
        # Full transcript bytes, not just caller-supplied claims, are frozen.
        for ep in load_manifest_bank(manifest):
            provenance = ep["provenance"]
            author = stage1["authors"][ep["assignments"]["author"]]
            if (
                provenance["author_version"] != author["immutable_version"]
                or provenance["settings"] != author["settings"]
            ):
                raise ValueError("episode author version/settings mismatch")
            transcript = str(Path(provenance["transcript_path"]).resolve())
            if manifest["files"].get(transcript) != provenance["transcript_hash"]:
                raise ValueError("author transcript absent from frozen manifest")
    return manifest


def load_manifest_bank(manifest):
    paths = [ROOT / p for p in manifest["files"] if p.endswith(".episode.json")]
    rows = [json.loads(path.read_text()) for path in paths]
    expected = {e["id"]: e["hash"] for e in manifest["episodes"]}
    if len(rows) != len(expected) or {r["id"]: sc1.digest(r) for r in rows} != expected:
        raise ValueError("episode manifest/cohort mismatch")
    return rows


def require_setup(path, manifest_id=None, *, committed=True):
    if path is None or not Path(path).is_file():
        raise ValueError("final requires an existing setup certificate")
    path = Path(path).resolve()
    cert = json.loads(path.read_text())
    if sc1.digest(
        {k: v for k, v in cert.items() if k != "certificate_hash"}
    ) != cert.get("certificate_hash"):
        raise ValueError("setup certificate hash mismatch")
    if (
        cert.get("full_passes", 0) < 24
        or cert.get("full_passes", 0) - cert.get("evicted_passes", 32) < 8
        or not cert.get("passed")
    ):
        raise ValueError("setup competence/headroom gate failed: NOT RUN")
    if manifest_id is not None and cert["manifest_id"] != manifest_id:
        raise ValueError("setup manifest mismatch")
    if cert["projection_seconds"] > sc1.COST_CAP or not cert["cost"]["samples"]:
        raise ValueError("setup cost gate failed")
    if committed:
        try:
            rel = path.relative_to(ROOT)
            committed_bytes = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"HEAD:{rel}"]
            )
        except (ValueError, subprocess.CalledProcessError) as exc:
            raise ValueError(
                "setup certificate must be committed before final"
            ) from exc
        if committed_bytes != path.read_bytes():
            raise ValueError("setup certificate changed since commit")
    for filename, h in cert["output_hashes"].items():
        if sc1.file_hash(filename) != h:
            raise ValueError("setup output hash mismatch")
    return cert


def verify_determinism(path, manifest):
    if path is None:
        raise ValueError("separately authorized model determinism certificate required")
    cert = json.loads(Path(path).read_text())
    if (
        cert.get("executable_manifest_id")
        != verify_manifest(manifest["executable_freeze"])["manifest_id"]
    ):
        raise ValueError("determinism artifact identity mismatch")
    rows = cert["outputs"]
    if (
        len(rows) != 8
        or len({r["process_id"] for r in rows}) != 2
        or len({r["episode_id"] for r in rows}) != 2
    ):
        raise ValueError(
            "determinism requires two fresh processes x two sources x two arms"
        )
    for episode in {r["episode_id"] for r in rows}:
        for arm in ("clf", "rule"):
            match = [r for r in rows if r["episode_id"] == episode and r["arm"] == arm]
            if len(match) != 2 or match[0]["token_ids"] != match[1]["token_ids"]:
                raise ValueError("model determinism failed")
    if cert["allocated_seconds"] <= 0:
        raise ValueError("determinism allocation not metered")
    return cert


def _check_cohort(rows):
    for pool, n in (("setup", 32), ("final", 256)):
        selected = [r for r in rows if r["pool"] == pool]
        if len(selected) != n or sorted(r["index"] for r in selected) != list(range(n)):
            raise ValueError(
                "production requires 32 setup and 256 final slots, none dropped"
            )
    if len(rows) != 288:
        raise ValueError("production pool contains extra sources")
    episodes.independence_audit(rows)


def _timing(row):
    latency = row["latency"]
    return {
        "prefill": latency["prefill"],
        "token": latency["worst_token"],
        "cpu": sum(
            latency[k] for k in ("render", "candidate", "scoring", "admission", "echo")
        ),
        "check": latency["check"],
    }


def run_study(
    args,
    manifest,
    rows,
    tokenizer,
    *,
    backend_factory=sc1.QwenBackend,
    scorer_factory=None,
):
    """Execute a frozen cohort. Injectable factories exist for CPU consumer tests."""
    from stencil.selector_v2 import ClassifierScorer

    stage = args.mode
    root = args.out / stage
    store = sc1.RunStore(root, manifest["manifest_id"])
    cert = (
        require_setup(args.setup_certificate, manifest["manifest_id"])
        if stage == "final"
        else None
    )
    determinism = (
        verify_determinism(args.determinism_certificate, manifest)
        if stage == "setup"
        else None
    )
    baseline_cost = (
        cert["cost"] if cert else {"spent": determinism["allocated_seconds"]}
    )
    cost_path = args.out / "cost.json"
    meter = (
        sc1.CostMeter(**json.loads(cost_path.read_text())["meter"])
        if cost_path.exists()
        else sc1.CostMeter(**baseline_cost)
    )
    if (
        cost_path.exists()
        and json.loads(cost_path.read_text())["manifest_id"] != manifest["manifest_id"]
    ):
        raise ValueError("allocation ledger manifest mismatch")
    if not meter.can_start(512 if stage == "final" else 64):
        return {
            "status": "NOT RUN" if stage == "setup" else "INCOMPLETE",
            "reason": "cost cap",
            "cost": asdict(meter),
        }
    if any(e["event"] == "start" for e in store.events()[-1:]):
        raise ValueError(
            "external interruption evidence required before resuming missing output"
        )
    init_id = f"init-{time.time_ns()}"
    init_start = time.monotonic()
    store.append(
        {
            "event": "initialization_start",
            "initialization_id": init_id,
            "wall_start": time.time(),
        }
    )
    backend = backend_factory(ROOT, args.trunk)
    scorer = (scorer_factory or ClassifierScorer)(ROOT / "data/classifier/model/ft")
    init_seconds = time.monotonic() - init_start
    meter.spent += init_seconds
    store.append(
        {
            "event": "initialization_completed",
            "initialization_id": init_id,
            "allocated_seconds": init_seconds,
        }
    )
    sc1.atomic_json(
        cost_path, {"manifest_id": manifest["manifest_id"], "meter": asdict(meter)}
    )
    selected = sorted((r for r in rows if r["pool"] == stage), key=lambda r: r["index"])
    completed_rows = []
    for episode in selected:
        order = episodes.commission_slot(stage, episode["index"])[
            "order" if stage == "final" else "setup_order"
        ]
        pending = store.pending(episode["id"], order)
        for arm in pending:
            remaining = sum(
                len(
                    store.pending(
                        e["id"],
                        ["clf", "rule"] if stage == "final" else ["full", "evicted"],
                    )
                )
                for e in selected
            )
            if not meter.can_start(remaining):
                return {
                    "status": "INCOMPLETE",
                    "completed_arms": 2 * len(selected) - remaining,
                    "cost": asdict(meter),
                }
            attempt = f"{episode['index']}-{arm}-{time.time_ns()}"
            store.start(episode["id"], arm, attempt)
            # Unknown harness exceptions deliberately leave the attempt unresolved.
            # Completed bad outputs/timeouts are persisted and never retried.
            row = sc1.run_arm(
                episode,
                arm,
                tokenizer,
                backend,
                scorer,
                manifest_id=manifest["manifest_id"],
                order=order,
                attempt_id=attempt,
                initialization_id=init_id,
                prior_elapsed=store.prior_elapsed(episode["id"], arm),
            )
            store.complete(row)
            meter.spent += row["allocated_seconds"]
            meter.observe(_timing(row), row["input_tokens"])
            sc1.atomic_json(
                cost_path,
                {"manifest_id": manifest["manifest_id"], "meter": asdict(meter)},
            )
        pair = store.write_pair(episode["id"], order, episode["assignments"])
        completed_rows.append(pair)
        if stage == "setup":
            diagnostic = root / f"{episode['id']}.cpu.json"
            if not diagnostic.exists():
                started = time.monotonic()
                cpu = {
                    arm: sc1.select_policy(
                        sc1.render_episode(episode, tokenizer), tokenizer, arm, scorer
                    )
                    for arm in ("clf", "rule")
                }
                elapsed = time.monotonic() - started
                meter.spent += elapsed
                meter.estimates["cpu"] = max(
                    meter.estimates["cpu"],
                    *(sum(c["latency"].values()) for c in cpu.values()),
                )
                sc1.atomic_json(
                    diagnostic,
                    {"cpu_selection_only": True, "arms": cpu, "elapsed": elapsed},
                    exclusive=True,
                )
                sc1.atomic_json(
                    cost_path,
                    {"manifest_id": manifest["manifest_id"], "meter": asdict(meter)},
                )
    if stage == "setup":
        full = sum(r["arms"]["full"]["success"] for r in completed_rows)
        evicted = sum(r["arms"]["evicted"]["success"] for r in completed_rows)
        projection = meter.project(512)
        summary = {
            "manifest_id": manifest["manifest_id"],
            "full_passes": full,
            "evicted_passes": evicted,
            "passed": full >= 24 and full - evicted >= 8 and projection <= sc1.COST_CAP,
            "projection_seconds": projection,
            "cost": asdict(meter),
            "episode_hashes": {r["id"]: sc1.digest(r) for r in selected},
            "output_hashes": {
                str(p.resolve()): sc1.file_hash(p) for p in root.glob("*.json")
            },
        }
        summary["certificate_hash"] = sc1.digest(summary)
        sc1.atomic_json(args.out / "setup-certificate.json", summary, exclusive=True)
        return {
            "status": "SETUP PASSED" if summary["passed"] else "NOT RUN",
            "full": full,
            "evicted": evicted,
            "projection_seconds": projection,
            "certificate": str(args.out / "setup-certificate.json"),
            "requires_commit": True,
        }
    seal = {
        "manifest_id": manifest["manifest_id"],
        "setup_certificate_hash": cert["certificate_hash"],
        "cost": asdict(meter),
        "pairs": {str(p.resolve()): sc1.file_hash(p) for p in root.glob("*.pair.json")},
    }
    if len(seal["pairs"]) != 256:
        raise ValueError("complete cohort seal requires all 256 pairs")
    sc1.atomic_json(args.out / "complete.json", seal, exclusive=True)
    return {
        "status": "COMPLETE; outcomes sealed until analyze",
        "pairs": 256,
        "allocated_seconds": meter.spent,
    }


def analyze(args, manifest):
    cert = require_setup(args.setup_certificate, manifest["manifest_id"])
    seal_path = args.out / "complete.json"
    if not seal_path.exists():
        raise ValueError("INCOMPLETE: final outcomes remain sealed")
    seal = json.loads(seal_path.read_text())
    if (
        seal["manifest_id"] != manifest["manifest_id"]
        or seal["setup_certificate_hash"] != cert["certificate_hash"]
    ):
        raise ValueError("completion seal identity mismatch")
    if seal["cost"]["spent"] > sc1.COST_CAP or len(seal["pairs"]) != 256:
        raise ValueError("invalid complete-study cost/cohort")
    # Check ALL bytes and identities before opening any outcome for inference.
    for path, h in seal["pairs"].items():
        if sc1.file_hash(path) != h:
            raise ValueError("sealed paired output hash mismatch")
    rows = [json.loads(Path(p).read_text()) for p in seal["pairs"]]
    expected = {e["id"]: e for e in manifest["episodes"] if e["pool"] == "final"}
    if len(rows) != len(expected) or {r["id"] for r in rows} != set(expected):
        raise ValueError("final cohort ID mismatch")
    store = sc1.RunStore(args.out / "final", manifest["manifest_id"])
    for row in rows:
        for arm in ("clf", "rule"):
            a = row["arms"][arm]
            if (
                set(a) != sc1.ARM_FIELDS
                or a["manifest_id"] != manifest["manifest_id"]
                or a["episode_hash"] != expected[row["id"]]["hash"]
                or a["order"] != expected[row["id"]]["order"]
                or any(a["interventions"].values())
            ):
                raise ValueError("invalid final arm record")
        if store.write_pair(row["id"], ["clf", "rule"], row["assignments"]) != row:
            raise ValueError("pair differs from immutable arm outputs")
    summary = sc1.analyze_pairs(rows)
    summary["cost"] = seal["cost"]
    summary["setup"] = {"full": cert["full_passes"], "evicted": cert["evicted_passes"]}
    sc1.atomic_json(args.out / "analysis.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("validate", "smoke", "setup", "final", "analyze", "commission")
    )
    parser.add_argument("bank", nargs="?", type=Path, default=ROOT / "data/sc1/smoke")
    parser.add_argument("--trunk", choices=("4b", "1.7b"), default="4b")
    parser.add_argument("--out", type=Path, default=ROOT / "data/sc1/smoke")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--setup-certificate", type=Path)
    parser.add_argument("--determinism-certificate", type=Path)
    parser.add_argument("--stage1", type=Path)
    parser.add_argument("--executable-freeze", type=Path)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="validate, write episodes and freeze a manifest; no model",
    )
    parser.add_argument("--pool", choices=("setup", "final"))
    parser.add_argument("--index", type=int)
    args = parser.parse_args(argv)
    if args.mode in {"final", "analyze"}:
        require_setup(args.setup_certificate)  # Before tokenizer/backend or outcome IO.
    if args.mode == "commission":
        if not args.stage1 or args.pool is None or args.index is None:
            raise ValueError("commission requires frozen --stage1, --pool and --index")
        versions = json.loads(args.stage1.read_text())["authors"]
        result = episodes.commissioning_request(
            (ROOT / CONTRACT).read_text(),
            episodes.SCHEMA,
            versions,
            args.pool,
            args.index,
        )
        sc1.atomic_json(
            args.out / f"{args.pool}-{args.index}.request.json", result, exclusive=True
        )
        return result
    tokenizer = load_tokenizer(args.trunk)
    if args.mode in {"validate", "smoke"}:
        rows, report = episodes.validate_bank(args.bank, tokenizer)
        if args.mode == "smoke" and (
            len(rows) != 8 or {r["pool"] for r in rows} != {"smoke"}
        ):
            raise ValueError("smoke requires exactly eight disposable sources")
        if args.mode == "smoke" or args.freeze:
            for row in rows:
                sc1.atomic_json(args.bank / f"{row['id']}.episode.json", row)
            sc1.atomic_json(args.out / "validation.json", report)
            manifest = build_manifest(
                args.bank,
                args.trunk,
                rows,
                stage1=args.stage1,
                executable=args.executable_freeze,
            )
            if manifest["production"]:
                _check_cohort(rows)
                for ep in rows:
                    p = str(Path(ep["provenance"]["transcript_path"]).resolve())
                    manifest["files"][p] = sc1.file_hash(p)
                manifest["manifest_id"] = sc1.digest(
                    {k: v for k, v in manifest.items() if k != "manifest_id"}
                )
            sc1.atomic_json(args.out / "manifest.json", manifest)
            report["manifest_id"] = manifest["manifest_id"]
        result = {
            k: report[k]
            for k in ("episodes", "references_pass", "mutations_fail", "bank_hash")
        }
        result.update(
            status="PASS",
            manifest_id=report.get("manifest_id"),
            age_counts={pool: count["age"] for pool, count in report["counts"].items()},
        )
    else:
        if not args.manifest:
            raise ValueError("a frozen production --manifest is required")
        manifest = verify_manifest(args.manifest, production=True)
        if manifest["trunk"] != args.trunk:
            raise ValueError("trunk differs from frozen manifest")
        rows = load_manifest_bank(manifest)
        _check_cohort(rows)
        if args.mode == "analyze":
            result = analyze(args, manifest)
        else:
            result = run_study(args, manifest, rows, tokenizer)
    print(sc1.canonical(result))
    return result


if __name__ == "__main__":
    main()

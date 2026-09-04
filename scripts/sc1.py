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
import hashlib
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


STUDY_REGISTRY = ROOT / ".git/sc1-studies"


def bind_study(manifest, out, *, stage="production"):
    """A registered identity has one durable directory across every invocation."""
    if any(
        not manifest.get(k) for k in ("study_id", "registration_hash", "execution_root")
    ):
        raise ValueError("registered study identity/execution root required")
    out = Path(out).resolve()
    if out != Path(manifest["execution_root"]).resolve():
        raise ValueError(
            "output differs from registered study execution root; "
            "relocation is not supported"
        )
    identity = {
        k: manifest[k] for k in ("study_id", "registration_hash", "execution_root")
    }
    identity["execution_root"] = str(out)
    registry = STUDY_REGISTRY / (sc1.digest(manifest["study_id"]) + ".json")
    if registry.exists():
        saved = json.loads(registry.read_text())
        if any(saved[k] != v for k, v in identity.items()):
            raise ValueError(
                "study identity already registered to different sources or output"
            )
        if (
            stage in saved["manifests"]
            and saved["manifests"][stage] != manifest["manifest_id"]
        ):
            raise ValueError("study cannot change frozen manifest or retry new sources")
    else:
        saved = {**identity, "manifests": {}}
    owners = []
    if stage == "production" and manifest.get("production"):
        fingerprints = {
            e.get("source_fingerprint") for e in manifest.get("episodes", [])
        }
        if not fingerprints or None in fingerprints:
            raise ValueError("registered study requires frozen source fingerprints")
        for fingerprint in fingerprints:
            owner_path = (
                STUDY_REGISTRY / "sources" / (sc1.digest(fingerprint) + ".json")
            )
            owner = {
                "source_fingerprint": fingerprint,
                "study_id": manifest["study_id"],
                "registration_hash": manifest["registration_hash"],
            }
            if owner_path.exists() and json.loads(owner_path.read_text()) != owner:
                raise ValueError(
                    "new study requires new sources; "
                    "source already bound to another study"
                )
            owners.append((owner_path, owner))
    for owner_path, owner in owners:
        if not owner_path.exists():
            sc1.atomic_json(owner_path, owner, exclusive=True)
    saved["manifests"][stage] = manifest["manifest_id"]
    sc1.atomic_json(registry, saved, exclusive=not registry.exists())
    out.mkdir(parents=True, exist_ok=True)
    local = out / "study.json"
    if local.exists() and json.loads(local.read_text()) != identity:
        raise ValueError("study directory identity mismatch")
    if not local.exists():
        sc1.atomic_json(local, identity, exclusive=True)
    for marker in ("invalid.json", "halt.json"):
        if (out / marker).exists():
            raise ValueError("study execution is terminal: " + marker)
    return identity


def infrastructure_exception(exc):
    import torch

    if isinstance(exc, (OSError, torch.cuda.OutOfMemoryError)):
        return True
    if isinstance(exc, RuntimeError):
        return any(
            word in str(exc).casefold()
            for word in ("cuda", "nccl", "device", "out of memory")
        )
    return False


def stop_for_cost(args, manifest, allocation, **details):
    allocation.checkpoint(close=True)
    result = {
        "status": "INCOMPLETE",
        "reason": "cost cap",
        "study_id": manifest["study_id"],
        "cost": asdict(allocation.meter),
        **details,
    }
    sc1.atomic_json(args.out / "halt.json", result, exclusive=True)
    return result


def record_exception(args, manifest, allocation, store, exc, **identity):
    allocation.checkpoint(close=True)
    if infrastructure_exception(exc):
        store.append(
            {
                "event": "attempt_open"
                if "attempt_id" in identity
                else "initialization_open",
                "cause": repr(exc),
                **identity,
            }
        )
    else:
        sc1.atomic_json(
            args.out / "invalid.json",
            {
                "manifest_id": manifest["manifest_id"],
                "study_id": manifest["study_id"],
                "cause": repr(exc),
                **identity,
            },
            exclusive=True,
        )


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
        if path.name.endswith((".source.json", ".episode.json")) or path.name in {
            "validation.json",
            "power.json",
            "grammar.json",
        }:
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
                "source_fingerprint": ep["source_fingerprint"],
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
    if stage1:
        registration = episodes.parse_json(Path(stage1).read_text())
        payload.update(
            study_id=registration["study_id"],
            execution_root=registration["execution_root"],
            registration_hash=sc1.file_hash(stage1),
        )
    payload["manifest_id"] = sc1.digest(payload)
    for path in CODE_FILES:
        committed = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{payload['harness_commit']}:{path}"]
        )
        if hashlib.sha256(committed).hexdigest() != files[path]:
            raise ValueError("commit executable artifacts before freezing: " + path)
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
        stage1, _ = verify_stage_freezes(
            manifest["stage1"], manifest["executable_freeze"]
        )
        if (
            manifest.get("study_id") != stage1["study_id"]
            or manifest.get("execution_root") != stage1["execution_root"]
            or manifest.get("registration_hash") != sc1.file_hash(manifest["stage1"])
        ):
            raise ValueError("registered study identity mismatch")
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
            settings_fields = {
                "temperature",
                "top_p",
                "reasoning_effort",
                "max_output_tokens",
                "seed_support",
            }
            if not settings_fields <= author["settings"].keys():
                raise ValueError("incomplete author generation settings: " + family)
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
            episodes.validate_schema(ep)
            verify_author_chain(ep, stage1)
            provenance = ep["provenance"]
            author = stage1["authors"][ep["assignments"]["author"]]
            if (
                provenance["author_version"] != author["immutable_version"]
                or provenance["settings"] != author["settings"]
                or provenance["provider"] != author["provider"]
                or provenance["contract_hash"] != manifest["files"][CONTRACT]
            ):
                raise ValueError("episode author version/settings mismatch")
            transcript = str(Path(provenance["transcript_path"]).resolve())
            if manifest["files"].get(transcript) != provenance["transcript_hash"]:
                raise ValueError("author transcript absent from frozen manifest")
    return manifest


def verify_stage_freezes(stage1_path, executable_path):
    if not stage1_path or not executable_path:
        raise ValueError("Stage 1 registration and Stage 2 executable freeze required")
    stage1 = episodes.parse_json(Path(stage1_path).read_text())
    if stage1.get("status") != "REGISTERED":
        raise ValueError("Stage 1 must be REGISTERED")
    if (
        stage1.get("trunk") != "4b"
        or not stage1.get("study_id")
        or not Path(stage1.get("execution_root", "")).is_absolute()
        or stage1.get("science_hash") != sc1.file_hash(ROOT / "LEDGER-PLAN.md")
    ):
        raise ValueError(
            "Stage 1 registered study/deployment/science identity mismatch"
        )
    frozen = verify_manifest(executable_path)
    if frozen["trunk"] != "4b" or stage1.get("deployment") != frozen["deployment"]:
        raise ValueError("registered Qwen3-4B deployment constants mismatch")
    if set(stage1.get("authors", {})) != set(episodes.AUTHORS):
        raise ValueError("Stage 1 author manifest incomplete")
    for author in stage1["authors"].values():
        if any(
            not author.get(k)
            for k in ("provider", "immutable_version", "settings", "neutral_template")
        ):
            raise ValueError("Stage 1 author configuration incomplete")
        if (
            not {
                "temperature",
                "top_p",
                "reasoning_effort",
                "max_output_tokens",
                "seed_support",
            }
            <= author["settings"].keys()
        ):
            raise ValueError("author settings incomplete")
        if author.get("contract_hash") != sc1.file_hash(ROOT / CONTRACT) or author.get(
            "grammar_hash"
        ) != sc1.digest(episodes.SCHEMA):
            raise ValueError("Stage 1 contract/grammar mismatch")
    return stage1, frozen


def verify_author_chain(ep, stage1, *, final_decision="accepted"):
    provenance = ep["provenance"]
    author = stage1["authors"][ep["assignments"]["author"]]
    chain = provenance.get("attempt_history")
    if not isinstance(chain, list) or len(chain) != ep["attempt"] + 1:
        raise ValueError("complete three-attempt request/rejection chain required")
    session = provenance["session_id"]
    previous = None
    messages = []
    for attempt, entry in enumerate(chain):
        if entry.get("attempt") != attempt or entry.get("previous") != previous:
            raise ValueError("attempt chain order/hash mismatch")
        feedback = entry.get("feedback")
        if feedback != (chain[attempt - 1]["reason"] if attempt else None):
            raise ValueError("repair feedback must match the retained rejection")
        request = episodes.commissioning_request(
            (ROOT / CONTRACT).read_text(),
            episodes.SCHEMA,
            stage1["authors"],
            ep["pool"],
            ep["index"],
            attempt,
            feedback,
        )
        if entry.get("request_hash") != sc1.digest(request):
            raise ValueError("stale author request/input hash")
        transcript_path = Path(entry["transcript_path"])
        if sc1.file_hash(transcript_path) != entry["transcript_hash"]:
            raise ValueError("author transcript hash mismatch")
        transcript = episodes.parse_json(transcript_path.read_text())
        messages.extend(
            [
                {"role": "user", "content": request["input"]},
                {"role": "assistant", "content": transcript.get("response")},
            ]
        )
        if (
            transcript.get("input") != request["input"]
            or transcript.get("session_id") != session
            or transcript.get("provider") != author["provider"]
            or transcript.get("version") != author["immutable_version"]
            or transcript.get("settings") != author["settings"]
            or transcript.get("messages") != messages
            or not isinstance(transcript.get("response"), dict)
        ):
            raise ValueError(
                "transcript exact sanitized input/session/response mismatch"
            )
        response = transcript["response"]
        if episodes.source_spec_hash(response) != entry.get("source_hash"):
            raise ValueError("retained attempted source hash mismatch")
        if attempt < ep["attempt"] or final_decision == "rejected":
            if (
                entry.get("decision") != "rejected"
                or not entry.get("reason")
                or not entry.get("reviewer")
            ):
                raise ValueError("prior rejected attempt/transcript missing")
        elif (
            entry.get("decision") != final_decision
            or entry["source_hash"] != ep["validation"]["source_hash"]
        ):
            raise ValueError("accepted attempt source mismatch")
        previous = sc1.digest(entry)
    last_request = request
    if (
        provenance["prompt_hash"] != sc1.digest(author["neutral_template"])
        or provenance["input_hashes"] != [last_request["input_hash"]]
        or provenance["transcript_hash"] != chain[-1]["transcript_hash"]
    ):
        raise ValueError("stale prompt/input/transcript provenance")


def load_manifest_bank(manifest):
    paths = [ROOT / p for p in manifest["files"] if p.endswith(".episode.json")]
    rows = [episodes.parse_json(path.read_text()) for path in paths]
    expected = {e["id"]: e["hash"] for e in manifest["episodes"]}
    if len(rows) != len(expected) or {r["id"]: sc1.digest(r) for r in rows} != expected:
        raise ValueError("episode manifest/cohort mismatch")
    by_id = {e["id"]: e for e in manifest["episodes"]}
    if any(
        by_id[r["id"]].get("source_fingerprint") != r["source_fingerprint"]
        for r in rows
    ):
        raise ValueError("manifest source fingerprint mismatch")
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
    if len(cert.get("episode_hashes", {})) != 32:
        raise ValueError("setup certificate requires exactly 32 episode hashes")
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
    pairs = [
        episodes.parse_json(Path(p).read_text())
        for p in cert["output_hashes"]
        if p.endswith(".pair.json")
    ]
    if len(pairs) != 32 or {r["id"] for r in pairs} != set(cert["episode_hashes"]):
        raise ValueError("setup paired cohort mismatch")
    for row in pairs:
        if set(row["arms"]) != {"full", "evicted"}:
            raise ValueError("setup arms must be full/evicted only")
        for arm in row["arms"].values():
            if (
                arm["manifest_id"] != cert["manifest_id"]
                or arm["episode_hash"] != cert["episode_hashes"][row["id"]]
            ):
                raise ValueError("setup arm identity mismatch")
    if (
        sum(r["arms"]["full"]["success"] for r in pairs) != cert["full_passes"]
        or sum(r["arms"]["evicted"]["success"] for r in pairs) != cert["evicted_passes"]
    ):
        raise ValueError("setup pass counts differ from committed outputs")
    return cert


def verify_determinism(path, manifest):
    if path is None:
        raise ValueError("separately authorized model determinism certificate required")
    cert = episodes.parse_json(Path(path).read_text())
    required = {
        "executable_manifest_id",
        "outputs",
        "allocated_seconds",
        "study_id",
        "initializations",
        "allocation_path",
        "allocation_hash",
    }
    if not required <= cert.keys():
        raise ValueError("incomplete determinism certificate")
    frozen = verify_manifest(
        manifest.get("executable_freeze") or manifest["manifest_path"]
    )
    if cert.get("executable_manifest_id") != frozen["manifest_id"]:
        raise ValueError("determinism artifact identity mismatch")
    expected_episodes = sorted(
        (e for e in frozen["episodes"] if e["pool"] == "smoke"), key=lambda e: e["id"]
    )[:2]
    expected = {e["id"]: e["hash"] for e in expected_episodes}
    allocation_path = Path(cert["allocation_path"])
    if sc1.file_hash(allocation_path) != cert["allocation_hash"]:
        raise ValueError("determinism allocation artifact hash mismatch")
    charged = episodes.parse_json(allocation_path.read_text())
    if (
        sc1.digest({k: v for k, v in charged.items() if k != "hash"}) != charged["hash"]
        or charged["meter"]["spent"] != cert["allocated_seconds"]
        or charged["manifest_id"] != cert["study_id"]
        or any(not interval["closed"] for interval in charged["intervals"])
    ):
        raise ValueError("determinism allocation ledger mismatch")
    inputs = {ep["id"]: ep for ep in load_manifest_bank(frozen)}
    tokenizer = load_tokenizer(frozen["trunk"])
    rows = cert["outputs"]
    processes = set(cert.get("initializations", {}))
    if (
        len(charged["intervals"]) != 2
        or {i["id"] for i in charged["intervals"]} != processes
        or any(
            i["elapsed"] < cert["initializations"][i["id"]]["allocated_seconds"]
            for i in charged["intervals"]
        )
    ):
        raise ValueError("determinism initialization intervals not charged")
    if len(expected) != 2 or len(rows) != 8 or len(processes) != 2:
        raise ValueError(
            "determinism requires two processes x two frozen smoke sources x two arms"
        )
    cells, artifacts = {}, set()
    for row in rows:
        key = (row["process_id"], row["episode_id"], row["arm"])
        if (
            key in cells
            or key[0] not in processes
            or key[1] not in expected
            or key[2] not in {"clf", "rule"}
            or row.get("episode_hash") != expected[key[1]]
            or row.get("deployment_hash") != sc1.digest(frozen["deployment"])
            or row.get("initialization_id")
            != cert["initializations"][key[0]].get("initialization_id", key[0])
            or not row.get("input_hash")
        ):
            raise ValueError("determinism process/cell/input identity mismatch")
        artifact = Path(row["output_path"]).resolve()
        if artifact in artifacts or sc1.file_hash(artifact) != row["output_hash"]:
            raise ValueError("determinism retained output hash/identity mismatch")
        output = episodes.parse_json(artifact.read_text())
        if output != {
            k: v for k, v in row.items() if k not in {"output_path", "output_hash"}
        }:
            raise ValueError("determinism output does not match retained artifact")
        arm_path = Path(row["arm_path"])
        if sc1.file_hash(arm_path) != row["arm_hash"]:
            raise ValueError("determinism retained arm hash mismatch")
        arm_row = episodes.parse_json(arm_path.read_text())
        if (
            arm_row["token_ids"] != row["token_ids"]
            or arm_row["episode_hash"] != row["episode_hash"]
            or arm_row["arm"] != row["arm"]
            or arm_row["initialization_id"] != row["initialization_id"]
            or arm_row["manifest_id"] != frozen["manifest_id"]
            or arm_row["allocated_seconds"] != row["allocated_seconds"]
        ):
            raise ValueError("determinism retained arm/input identity mismatch")
        prompt = sc1.render_episode(
            inputs[row["episode_id"]],
            tokenizer,
            arm_row["selection"]["echo"]["insertion"],
        )
        if row["input_hash"] != sc1.digest(prompt["ids"]):
            raise ValueError("determinism frozen input hash mismatch")
        artifacts.add(artifact)
        cells[key] = row
    for episode in expected:
        for arm in ("clf", "rule"):
            pair = [cells.get((p, episode, arm)) for p in processes]
            if any(r is None for r in pair) or any(
                pair[0][k] != pair[1][k]
                for k in ("token_ids", "input_hash", "deployment_hash", "episode_hash")
            ):
                raise ValueError("model determinism cross-process replication failed")
    allocated = sum(v["allocated_seconds"] for v in cert["initializations"].values())
    if (
        cert["allocated_seconds"] <= 0
        or cert["allocated_seconds"] < allocated
        or allocated < sum(r["allocated_seconds"] for r in rows)
        or cert["allocated_seconds"] > sc1.COST_CAP
    ):
        raise ValueError("determinism allocation not fully metered")
    if manifest.get("study_id") and cert.get("study_id") != manifest["study_id"]:
        raise ValueError("determinism certificate belongs to another study")
    return cert


def run_determinism(
    args,
    manifest,
    rows,
    tokenizer,
    *,
    backend_factory=sc1.QwenBackend,
    scorer_factory=None,
):
    """One fresh initialization produces four outputs; two invocations certify eight."""
    import os

    from stencil.selector_v2 import ClassifierScorer

    bind_study(manifest, args.out, stage="executable")
    allocation = sc1.AllocationLedger(args.out / "cost.json", manifest["study_id"])
    root = args.out / "determinism"
    receipts = sorted(root.glob("*.process.json"))
    if len(receipts) >= 2:
        raise ValueError("determinism study already has two process executions")
    # PID plus kernel process start ticks distinguishes reuse without allowing a new
    # invocation in the same interpreter to masquerade as a fresh process.
    identity = f"{os.getpid()}-{Path('/proc/self/stat').read_text().split()[21]}"
    if any(
        episodes.parse_json(p.read_text())["process_id"] == identity for p in receipts
    ):
        raise ValueError("determinism requires a fresh process")
    store = sc1.RunStore(root / identity, manifest["manifest_id"])
    if any(root.glob("*/attempts.jsonl")) and len(
        list(root.glob("*/attempts.jsonl"))
    ) > len(receipts):
        raise ValueError(
            "determinism has an interrupted process; "
            "retained outputs cannot be replaced"
        )
    selected_ids = [
        e["id"]
        for e in sorted(manifest["episodes"], key=lambda e: e["id"])
        if e["pool"] == "smoke"
    ][:2]
    selected = [next(r for r in rows if r["id"] == i) for i in selected_ids]
    if len(selected) != 2 or any(
        sc1.digest(r)
        != next(e["hash"] for e in manifest["episodes"] if e["id"] == r["id"])
        for r in selected
    ):
        raise ValueError("determinism frozen smoke input mismatch")
    if not allocation.meter.can_start(4):
        return stop_for_cost(args, manifest, allocation)
    init_id = identity
    allocation.begin(init_id)
    started = time.monotonic()
    try:
        backend = backend_factory(ROOT, args.trunk)
        scorer = (scorer_factory or ClassifierScorer)(ROOT / "data/classifier/model/ft")
    except Exception as exc:
        record_exception(
            args, manifest, allocation, store, exc, initialization_id=init_id
        )
        raise
    allocation.meter.initialization_estimate = max(
        allocation.meter.initialization_estimate, time.monotonic() - started
    )
    outputs = []
    for ep in selected:
        order = episodes.commission_slot("smoke", ep["index"])["order"]
        for arm in order:
            allocation.checkpoint()
            if not allocation.meter.can_start(4 - len(outputs)):
                return stop_for_cost(args, manifest, allocation)
            attempt = f"{identity}-{ep['id']}-{arm}"
            store.start(ep["id"], arm, attempt)
            try:
                row = sc1.run_arm(
                    ep,
                    arm,
                    tokenizer,
                    backend,
                    scorer,
                    manifest_id=manifest["manifest_id"],
                    order=order,
                    attempt_id=attempt,
                    initialization_id=init_id,
                )
                store.complete(row)
            except Exception as exc:
                record_exception(
                    args,
                    manifest,
                    allocation,
                    store,
                    exc,
                    episode_id=ep["id"],
                    arm=arm,
                    attempt_id=attempt,
                )
                raise
            prompt = sc1.render_episode(
                ep, tokenizer, row["selection"]["echo"]["insertion"]
            )
            output = {
                "process_id": identity,
                "initialization_id": init_id,
                "episode_id": ep["id"],
                "episode_hash": sc1.digest(ep),
                "arm": arm,
                "executable_manifest_id": manifest["manifest_id"],
                "deployment_hash": sc1.digest(manifest["deployment"]),
                "input_hash": sc1.digest(prompt["ids"]),
                "token_ids": row["token_ids"],
                "allocated_seconds": row["allocated_seconds"],
                "arm_path": str(store.arm_path(ep["id"], arm).resolve()),
                "arm_hash": sc1.file_hash(store.arm_path(ep["id"], arm)),
            }
            path = root / identity / f"{ep['id']}.{arm}.output.json"
            sc1.atomic_json(path, output, exclusive=True)
            outputs.append(
                {
                    **output,
                    "output_path": str(path.resolve()),
                    "output_hash": sc1.file_hash(path),
                }
            )
            allocation.meter.observe(_timing(row), row["input_tokens"])
    allocation.checkpoint()
    elapsed = allocation.intervals[-1]["elapsed"]
    receipt = {
        "process_id": identity,
        "initialization_id": init_id,
        "allocated_seconds": elapsed,
        "outputs": outputs,
    }
    sc1.atomic_json(root / f"{identity}.process.json", receipt, exclusive=True)
    allocation.checkpoint(close=True)
    all_receipts = [
        episodes.parse_json(p.read_text()) for p in sorted(root.glob("*.process.json"))
    ]
    cert = {
        "study_id": manifest["study_id"],
        "executable_manifest_id": manifest["manifest_id"],
        "allocated_seconds": allocation.meter.spent,
        "initializations": {
            r["process_id"]: {
                "initialization_id": r["initialization_id"],
                "allocated_seconds": r["allocated_seconds"],
            }
            for r in all_receipts
        },
        "outputs": [o for r in all_receipts for o in r["outputs"]],
    }
    if len(all_receipts) == 2:
        snapshot = root / "allocation.json"
        sc1.atomic_json(
            snapshot, json.loads((args.out / "cost.json").read_text()), exclusive=True
        )
        cert.update(
            allocation_path=str(snapshot.resolve()),
            allocation_hash=sc1.file_hash(snapshot),
        )
    path = args.out / "determinism-certificate.json"
    sc1.atomic_json(path, cert)
    return {
        "status": "DETERMINISM RECORDED"
        if len(all_receipts) == 2
        else "SECOND FRESH PROCESS REQUIRED",
        "certificate": str(path),
        "outputs": len(cert["outputs"]),
    }


def _check_cohort(rows):
    smoke_sources = episodes.load_sources(ROOT / "data/sc1/smoke")
    forbidden_ids = {s["source_id"] for s in smoke_sources}
    forbidden_fingerprints = {episodes.sibling_fingerprint(s) for s in smoke_sources}
    forbidden_literals = set()
    for source in smoke_sources:
        material, literals = episodes._literal_expand(
            source, episodes.commission_slot("smoke", source["index"])
        )
        forbidden_literals.update(
            str(v)
            for k, v in literals.items()
            if source["literal_specs"][k]["type"] in {"name", "identifier"}
        )
        forbidden_literals.update(
            str(e[k]) for e in material["entities"] for k in ("name", "id")
        )
    for row in rows:
        names = {str(e[k]) for e in row["entities"] for k in ("name", "id")}
        fm = row["filler_manifest"]
        names.update(
            str(v)
            for k, v in fm["literal_values"].items()
            if fm["literal_types"][k] in {"name", "identifier"}
        )
        if (
            row["source_id"] in forbidden_ids
            or row["source_fingerprint"] in forbidden_fingerprints
            or names & forbidden_literals
        ):
            raise ValueError(
                "smoke source/fingerprint/entity may never be reused in production"
            )
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
    bind_study(manifest, args.out)
    root = args.out / stage
    try:
        store = sc1.RunStore(root, manifest["manifest_id"])
    except RuntimeError as exc:
        sc1.atomic_json(
            args.out / "invalid.json",
            {
                "study_id": manifest["study_id"],
                "manifest_id": manifest["manifest_id"],
                "cause": repr(exc),
            },
            exclusive=True,
        )
        raise
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
    allocation = sc1.AllocationLedger(
        cost_path, manifest["study_id"], sc1.CostMeter(**baseline_cost)
    )
    if getattr(args, "interruption_evidence", None):
        evidence = json.loads(args.interruption_evidence.read_text())
        if allocation.intervals and not allocation.intervals[-1]["closed"]:
            allocation.recover(evidence)
        else:
            allocation.recover(evidence, allow_closed=True)
        for attempt in evidence.get("attempts", []):
            if store.is_completed(attempt["episode_id"], attempt["arm"]):
                continue  # Recovered durable outputs are never classified as retries.
            store.interrupt(
                attempt["episode_id"],
                attempt["arm"],
                attempt["attempt_id"],
                evidence["reason"],
                attempt["elapsed"],
                evidence["evidence"],
            )
    meter = allocation.meter
    if (args.out / "invalid.json").exists():
        raise ValueError(
            "INVALID: unresolved harness defect; this bank cannot be rerun"
        )
    final_marker = args.out / (
        "complete.json" if stage == "final" else "setup-certificate.json"
    )
    if final_marker.exists():
        return {"status": "ALREADY COMPLETE", "artifact": str(final_marker)}
    # Reconcile maxima from durable outputs if loss preceded the cost checkpoint.
    for path in root.glob("*.json"):
        if path.name.endswith((".pair.json", ".cpu.json")):
            continue
        row = json.loads(path.read_text())
        if set(row) == sc1.ARM_FIELDS:
            meter.observe(_timing(row), row["input_tokens"])
    for path in root.glob("*.cpu.json"):
        for cpu in json.loads(path.read_text())["arms"].values():
            meter.estimates["cpu"] = max(
                meter.estimates["cpu"], sum(cpu["latency"].values())
            )
    selected = sorted((r for r in rows if r["pool"] == stage), key=lambda r: r["index"])
    pending_by_id = {}
    for episode in selected:
        order = episodes.commission_slot(stage, episode["index"])[
            "order" if stage == "final" else "setup_order"
        ]
        pending_by_id[episode["id"]] = store.pending(episode["id"], order)
    remaining = sum(map(len, pending_by_id.values()))
    meter.remaining_initialization = (
        max(meter.remaining_initialization, meter.initialization_estimate)
        if remaining or stage == "setup"
        else 0.0
    )
    if not meter.can_start(remaining):
        return stop_for_cost(
            args, manifest, allocation, completed_arms=2 * len(selected) - remaining
        )
    if (
        any(e["event"] == "initialization_open" for e in store.events()[-1:])
        and not args.interruption_evidence
    ):
        raise ValueError("initialization requires external interruption evidence")
    init_id = f"init-{time.time_ns()}"
    allocation.begin(init_id)
    init_start = time.monotonic()
    store.append(
        {
            "event": "initialization_start",
            "initialization_id": init_id,
            "wall_start": time.time(),
        }
    )
    try:
        backend = backend_factory(ROOT, args.trunk) if remaining else None
        scorer = (
            (scorer_factory or ClassifierScorer)(ROOT / "data/classifier/model/ft")
            if remaining or stage == "setup"
            else None
        )
    except Exception as exc:
        record_exception(
            args, manifest, allocation, store, exc, initialization_id=init_id
        )
        raise
    init_seconds = time.monotonic() - init_start
    meter.initialization_estimate = max(meter.initialization_estimate, init_seconds)
    meter.remaining_initialization = 0.0
    allocation.checkpoint()
    store.append(
        {
            "event": "initialization_completed",
            "initialization_id": init_id,
            "allocated_seconds": init_seconds,
        }
    )
    allocation.checkpoint()
    completed_rows = []
    for episode in selected:
        order = episodes.commission_slot(stage, episode["index"])[
            "order" if stage == "final" else "setup_order"
        ]
        pending = pending_by_id[episode["id"]]
        for arm in pending:
            allocation.checkpoint()
            if not meter.can_start(remaining):
                return stop_for_cost(
                    args,
                    manifest,
                    allocation,
                    completed_arms=2 * len(selected) - remaining,
                )
            attempt = f"{episode['index']}-{arm}-{time.time_ns()}"
            store.start(episode["id"], arm, attempt)
            # Unknown harness exceptions deliberately leave the attempt unresolved.
            # Completed bad outputs/timeouts are persisted and never retried.
            try:
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
                persist_start = time.monotonic()
                store.complete(row)
            except Exception as exc:
                record_exception(
                    args,
                    manifest,
                    allocation,
                    store,
                    exc,
                    episode_id=episode["id"],
                    arm=arm,
                    attempt_id=attempt,
                )
                raise
            meter.persistence_estimate = max(
                meter.persistence_estimate, time.monotonic() - persist_start
            )
            remaining -= 1
            meter.observe(_timing(row), row["input_tokens"])
            allocation.checkpoint()
        pair = store.write_pair(episode["id"], order, episode["assignments"])
        completed_rows.append(pair)
        if stage == "setup":
            diagnostic = root / f"{episode['id']}.cpu.json"
            if not diagnostic.exists():
                started = time.monotonic()
                cpu = {}
                for policy in ("clf", "rule"):
                    render_start = time.monotonic()
                    layout = sc1.render_episode(episode, tokenizer)
                    render_seconds = time.monotonic() - render_start
                    plan = sc1.select_policy(layout, tokenizer, policy, scorer)
                    render_start = time.monotonic()
                    sc1.render_episode(episode, tokenizer, plan["echo"]["insertion"])
                    plan["latency"]["render"] = (
                        render_seconds + time.monotonic() - render_start
                    )
                    cpu[policy] = plan
                elapsed = time.monotonic() - started
                meter.estimates["cpu"] = max(
                    meter.estimates["cpu"],
                    *(sum(c["latency"].values()) for c in cpu.values()),
                )
                sc1.atomic_json(
                    diagnostic,
                    {"cpu_selection_only": True, "arms": cpu, "elapsed": elapsed},
                    exclusive=True,
                )
                allocation.checkpoint()
    allocation.checkpoint(close=True)
    if meter.spent > sc1.COST_CAP:
        return stop_for_cost(args, manifest, allocation)
    if stage == "setup":
        full = sum(r["arms"]["full"]["success"] for r in completed_rows)
        evicted = sum(r["arms"]["evicted"]["success"] for r in completed_rows)
        meter.remaining_initialization = meter.initialization_estimate
        allocation.checkpoint()
        projection = meter.project(512)
        summary = {
            "manifest_id": manifest["manifest_id"],
            "study_id": manifest["study_id"],
            "full_passes": full,
            "evicted_passes": evicted,
            "passed": full >= 24 and full - evicted >= 8 and projection <= sc1.COST_CAP,
            "projection_seconds": projection,
            "cost": asdict(meter),
            "episode_hashes": {r["id"]: sc1.digest(r) for r in selected},
            "output_hashes": {
                str(p.resolve()): sc1.file_hash(p)
                for p in root.iterdir()
                if p.suffix in {".json", ".jsonl"}
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
        "study_id": manifest["study_id"],
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
    bind_study(manifest, args.out)
    allocation = sc1.AllocationLedger(args.out / "cost.json", manifest["study_id"])
    if allocation.meter.spent > sc1.COST_CAP or (
        allocation.intervals and not allocation.intervals[-1]["closed"]
    ):
        raise ValueError("study allocation is incomplete or over cap")
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
    rows = [episodes.parse_json(Path(p).read_text()) for p in seal["pairs"]]
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
        "mode",
        choices=(
            "validate",
            "smoke",
            "determinism",
            "setup",
            "final",
            "analyze",
            "commission",
        ),
    )
    parser.add_argument("bank", nargs="?", type=Path, default=ROOT / "data/sc1/smoke")
    parser.add_argument("--trunk", choices=("4b", "1.7b"), default="4b")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--setup-certificate", type=Path)
    parser.add_argument("--determinism-certificate", type=Path)
    parser.add_argument("--interruption-evidence", type=Path)
    parser.add_argument("--stage1", type=Path)
    parser.add_argument("--executable-freeze", type=Path)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="validate, write episodes and freeze a manifest; no model",
    )
    parser.add_argument("--pool", choices=("setup", "final"))
    parser.add_argument("--index", type=int)
    parser.add_argument("--attempt", type=int, default=0)
    parser.add_argument("--history", type=Path)
    args = parser.parse_args(argv)
    if (
        args.mode in {"setup", "final", "analyze", "determinism", "commission"}
        and args.out is None
    ):
        raise ValueError("--out is required for execution, analysis and commissioning")
    if (
        args.mode in {"setup", "final", "analyze", "determinism", "commission"}
        and args.trunk != "4b"
    ):
        raise ValueError("SC1-v2 registered deployment requires Qwen3-4B")
    if args.out is None:
        args.out = args.bank
    if args.mode in {"final", "analyze"}:
        require_setup(args.setup_certificate)  # Before tokenizer/backend or outcome IO.
    if args.mode == "commission":
        if not args.stage1 or args.pool is None or args.index is None:
            raise ValueError("commission requires frozen --stage1, --pool and --index")
        stage1, _ = verify_stage_freezes(args.stage1, args.executable_freeze)
        versions = stage1["authors"]
        history = episodes.parse_json(args.history.read_text()) if args.history else []
        if len(history) != args.attempt or not 0 <= args.attempt < 3:
            raise ValueError("commission repair requires all prior rejected attempts")
        for i, entry in enumerate(history):
            if (
                entry.get("attempt") != i
                or entry.get("decision") != "rejected"
                or not entry.get("reason")
                or not entry.get("reviewer")
                or not entry.get("transcript_path")
                or not entry.get("transcript_hash")
                or sc1.file_hash(entry["transcript_path"]) != entry["transcript_hash"]
            ):
                raise ValueError("commission rejected-attempt evidence incomplete")
        feedback = history[-1]["reason"] if history else None
        if history:
            last = history[-1]
            transcript = episodes.parse_json(Path(last["transcript_path"]).read_text())
            slot = episodes.commission_slot(args.pool, args.index, args.attempt - 1)
            author = versions[slot["assignments"]["author"]]
            previous_request = episodes.commissioning_request(
                (ROOT / CONTRACT).read_text(),
                episodes.SCHEMA,
                versions,
                args.pool,
                args.index,
                args.attempt - 1,
                last.get("feedback"),
            )
            previous_ep = {
                "attempt": args.attempt - 1,
                "pool": args.pool,
                "index": args.index,
                "assignments": slot["assignments"],
                "validation": {"source_hash": last["source_hash"]},
                "provenance": {
                    "session_id": transcript["session_id"],
                    "attempt_history": history,
                    "prompt_hash": sc1.digest(author["neutral_template"]),
                    "input_hashes": [previous_request["input_hash"]],
                    "transcript_hash": last["transcript_hash"],
                },
            }
            verify_author_chain(previous_ep, stage1, final_decision="rejected")
        result = episodes.commissioning_request(
            (ROOT / CONTRACT).read_text(),
            episodes.SCHEMA,
            versions,
            args.pool,
            args.index,
            args.attempt,
            feedback,
        )
        result["prior_attempts"] = history
        sc1.atomic_json(
            args.out / f"{args.pool}-{args.index}-{args.attempt}.request.json",
            result,
            exclusive=True,
        )
        return result
    if args.mode == "determinism":
        stage1, frozen = verify_stage_freezes(args.stage1, args.manifest)
        execution = {
            **frozen,
            "study_id": stage1["study_id"],
            "execution_root": stage1["execution_root"],
            "registration_hash": sc1.file_hash(args.stage1),
        }
        bind_study(execution, args.out, stage="executable")
        result = run_determinism(
            args, execution, load_manifest_bank(frozen), load_tokenizer(args.trunk)
        )
        if result["outputs"] == 8:
            verify_determinism(
                result["certificate"], {**execution, "executable_freeze": args.manifest}
            )
        print(sc1.canonical(result))
        return result
    tokenizer = load_tokenizer(args.trunk)
    if args.mode in {"validate", "smoke"}:
        rows, report = episodes.validate_bank(
            args.bank, tokenizer, check_frozen=not (args.mode == "smoke" or args.freeze)
        )
        if args.mode == "smoke" and (
            len(rows) != 8 or {r["pool"] for r in rows} != {"smoke"}
        ):
            raise ValueError("smoke requires exactly eight disposable sources")
        if args.mode == "smoke" or args.freeze:
            for row in rows:
                sc1.atomic_json(args.bank / f"{row['id']}.episode.json", row)
            sc1.atomic_json(args.out / "validation.json", report)
            sc1.atomic_json(args.bank / "grammar.json", episodes.SCHEMA)
            sc1.atomic_json(
                args.bank / "power.json",
                [
                    sc1.exact_power(256, q, d)
                    for q, d in ((0.1, 0.05), (0.2, 0.05), (0.3, 0.05), (0.2, 0.1))
                ],
            )
            manifest = build_manifest(
                args.bank,
                args.trunk,
                rows,
                stage1=args.stage1,
                executable=args.executable_freeze,
            )
            if manifest["production"]:
                stage1, _ = verify_stage_freezes(args.stage1, args.executable_freeze)
                _check_cohort(rows)
                for ep in rows:
                    verify_author_chain(ep, stage1)
                    for attempt in ep["provenance"]["attempt_history"]:
                        p = str(Path(attempt["transcript_path"]).resolve())
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

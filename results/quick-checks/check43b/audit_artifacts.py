"""CPU-only reconstruction of check43b saved tensors and applied directions."""

import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path("/home/bmarti44/stencil-llm")
OUT = ROOT / "results/quick-checks/check43b"
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    import focus_check43b as run

    torch.set_num_threads(2)
    rows = [json.loads(x) for x in (OUT / "records.jsonl").read_text().splitlines()]
    data = torch.load(OUT / "profiles.pt", map_location="cpu", weights_only=True)
    donors = [
        torch.load(p, map_location="cpu", weights_only=True)
        for p in sorted((OUT / "profiles").glob("*.pt"))
    ]
    assert len(donors) == 32
    recomputed = {}
    for name in ("window", "identity", "all-generated"):
        means = []
        for operation in ("SUM", "PRODUCT"):
            examples = []
            for d in donors:
                if d["operation"] != operation:
                    continue
                raw = d["raw_generated_logits"].double()
                assert raw.shape == (48, len(d["generated_token_ids"]), 128)
                indices = (
                    d["primary_indices"]
                    if name == "window"
                    else [d["identity_index"]]
                    if name == "identity"
                    else list(range(raw.shape[1]))
                )
                examples.append(raw[:, indices].mean(1))
            means.append(torch.stack(examples).mean(0))
        means = torch.stack(means)
        # File order differs from donor order; permit float64 sum roundoff.
        torch.testing.assert_close(
            means, data["derived"][name]["means"], atol=1e-12, rtol=0
        )
        b = run.direction(means, torch)
        torch.testing.assert_close(b, data["derived"][name]["bias"], atol=1e-7, rtol=0)
        recomputed[name] = float(b.norm())
    b = data["derived"]["window"]["bias"]
    generator = torch.Generator().manual_seed(96062)
    perm = torch.stack([torch.randperm(128, generator=generator) for _ in range(48)])
    assert torch.equal(perm, data["permutations"])
    assert torch.equal(b.gather(1, perm), data["shuffle"])
    norms = json.loads((OUT / "recipe-freeze.json").read_text())["target_norms"]
    js = (
        torch.load(
            ROOT / "results/quick-checks/check40b/frozen-biases.pt",
            map_location="cpu",
            weights_only=True,
        )["correct"].float()
        * 0.75
    )
    tensors = {}
    magnitude = []
    for dose, norm in zip((2, 3), norms, strict=True):
        bias = b * (norm / b.norm())
        shuffle = data["shuffle"] * (norm / b.norm())
        tensors[dose] = dict(
            zip(
                run.ARMS,
                (bias, -bias, shuffle, -shuffle, None, None, None),
                strict=True,
            )
        )
        magnitude.append(
            dict(
                dose=dose,
                float32_band_norm=float(bias.norm()),
                applied_bf16_band_norm=float(bias.bfloat16().float().norm()),
                max_abs_shift=float(bias.abs().max()),
                per_layer_norm=bias.norm(dim=1).tolist(),
                per_layer_max_abs=bias.abs().amax(dim=1).tolist(),
            )
        )
        assert abs(float(bias.norm()) - norm) < 2e-6
        assert torch.allclose(bias.norm(dim=1), shuffle.norm(dim=1))
    dispatch = {}
    for r in rows:
        tensor = (
            js
            if r["phase"] == "sanity"
            else tensors[r["dose"]][r["arm"]]
            if r["dose"]
            else None
        )
        wanted_hash = (
            hashlib.sha256(tensor.float().numpy().tobytes()).hexdigest()
            if tensor is not None
            else None
        )
        assert r["bias_sha256"] == wanted_hash
        assert len(r["dispatch"]) >= 48
        for key, v in r["dispatch"].items():
            layer, stage = key.split("-")
            if not 7 <= int(layer) <= 34:
                continue
            group = f"{r['phase']}/{r['dose']}/{r['arm']}/{stage}"
            group = dispatch.setdefault(
                group,
                dict(tokens=0, changed_routes=0, mixture_l1_sum=0, changed_weights=0),
            )
            group["tokens"] += v["tokens"]
            group["changed_routes"] += v["changed_route_tokens"]
            group["mixture_l1_sum"] += v["mixture_l1_sum"]
            group["changed_weights"] += v["changed_weight_tokens"]
    for v in dispatch.values():
        v["changed_route_fraction"] = v["changed_routes"] / v["tokens"]
        v["mean_mixture_l1"] = v["mixture_l1_sum"] / v["tokens"]
    identities = {}
    for dose in (2, 3):
        paired = {
            (r["task_id"], r["arm"]): r
            for r in rows
            if r["phase"] == "setup" and r["dose"] == dose
        }
        if paired:
            tasks = {t for t, a in paired}
            assert len(paired) == 32 and len(tasks) == 8
            off = {r["task_id"]: r for r in rows if r["phase"] == "OFF-baseline"}
            for task in tasks:
                assert (
                    len(
                        {paired[task, a]["input_sha256"] for a in run.ARMS[:4]}
                        | {off[task]["input_sha256"]}
                    )
                    == 1
                )
            identities[str(dose)] = dict(
                sign_token_identity=sum(
                    paired[t, "plus"]["generated_token_ids"]
                    == paired[t, "minus"]["generated_token_ids"]
                    for t in tasks
                ),
                minus_OFF_token_identity=sum(
                    paired[t, "minus"]["generated_token_ids"]
                    == off[t]["generated_token_ids"]
                    for t in tasks
                ),
            )
    report = dict(
        profile_count=len(donors),
        raw_logits_and_directions_recomputed=True,
        unit_norms=recomputed,
        stable_shuffle_recomputed=True,
        bias_hashes_verified=len(rows),
        magnitudes=magnitude,
        dispatch=dispatch,
        token_identity=identities,
        malformed_records=[
            dict(
                id=r["id"],
                task=r["task_id"],
                phase=r["phase"],
                dose=r["dose"],
                arm=r["arm"],
                text=r["text"],
                error=r["score"].get("error"),
            )
            for r in rows
            if r["score"].get("malformed")
        ],
    )
    (OUT / "audit-details.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("dispatch", "magnitudes", "malformed_records")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

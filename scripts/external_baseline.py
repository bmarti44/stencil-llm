"""SLAB-2 external X baseline, R/N only. Default is offline projection.

API contract: https://platform.claude.com/docs/en/api/messages/create
Rates below are unverified planning assumptions, configurable before a run.
Real API execution requires Brian's separate spend approval; use --mock now.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

from stencil.focus import slab2 as s
from stencil.focus.loop import DecodeResult
from stencil.focus.renderer import compact

PRICES = {"claude-sonnet-5": {"input": 3.0, "output": 15.0}}


def estimate(input_tokens, output_tokens, model="claude-sonnet-5", prices=None):
    rates = (PRICES if prices is None else prices)[model]
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("nonnegative integer token usage required")
    if any(
        not isinstance(rates[k], (int, float)) or not 0 <= rates[k] < float("inf")
        for k in ("input", "output")
    ):
        raise ValueError("finite nonnegative rates required")
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1e6


def projection(episodes, model="claude-sonnet-5", prices=None, n_rounds=16):
    s.validate_rounds(n_rounds)
    if episodes not in (8, 64):
        raise ValueError("registered bank size required")
    calls = episodes * n_rounds * 2
    inp, out = calls * (32768 - s.REPLY_CAP), calls * s.REPLY_CAP
    return dict(
        episodes=episodes,
        arms=["R", "N"],
        calls=calls,
        input_tokens=inp,
        output_tokens=out,
        total_tokens=inp + out,
        usd_estimate=estimate(inp, out, model, prices),
        assumption=(
            "budget envelope; input budget is a planning assumption "
            "in API tokens; no cache discounts"
        ),
    )


class AnthropicClient:
    def __init__(self, *, spend_approved=False):
        if not spend_approved:
            raise ValueError(
                "Brian must approve API spend before a real client is constructed"
            )
        self._key = os.environ["ANTHROPIC_API_KEY"]

    def create(self, **payload):
        request = HTTPRequest(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=1200) as response:
                return json.load(response)
        except Exception:
            # Never let credential-bearing transport diagnostics reach journals.
            raise RuntimeError(
                "Anthropic transport failed; no retry performed"
            ) from None


class MockClient:
    def __init__(self, text):
        self.text = text

    def create(self, **payload):
        return dict(
            id="mock-result",
            content=[dict(type="text", text=self.text)],
            stop_reason="end_turn",
            usage=dict(
                input_tokens=len(s.qwen_encode(compact(payload))),
                output_tokens=len(s.qwen_encode(self.text)),
            ),
        )


class AnthropicDecoder:
    def __init__(
        self,
        client,
        journal,
        *,
        model="claude-sonnet-5",
        prices=None,
        episode_id=None,
        arm=None,
        turn=None,
    ):
        self.client, self.journal, self.model = client, Path(journal), model
        self.prices = PRICES if prices is None else prices
        self.binding = dict(episode_id=episode_id, arm=arm, turn=turn)
        estimate(0, 0, model, self.prices)

    def __call__(self, rendered):
        messages = [
            dict(role=m["role"], content=m["text"]) for m in rendered.history_messages
        ]
        messages.append(dict(role="user", content=rendered.text))
        payload = dict(
            model=self.model,
            system=s.SYSTEM_PROMPT,
            messages=messages,
            max_tokens=s.REPLY_CAP,
            temperature=0,
        )
        response = self.client.create(**payload)
        usage, stop = response["usage"], response["stop_reason"]
        inp, out = usage["input_tokens"], usage["output_tokens"]
        # Write usage even for an unsupported stop; spent tokens remain charged.
        record = dict(
            **self.binding,
            model=self.model,
            result_id=response["id"],
            stop_reason=stop,
            input_tokens=inp,
            output_tokens=out,
            usd_estimate=estimate(inp, out, self.model, self.prices),
            request_sha256=s.digest(payload),
            max_tokens=s.REPLY_CAP,
        )
        with self.journal.open("a") as stream:
            stream.write(compact(record) + "\n")
        if stop not in {"end_turn", "max_tokens"}:
            raise ValueError("unsupported Anthropic stop reason")
        if out > s.REPLY_CAP or any(b["type"] != "text" for b in response["content"]):
            raise ValueError("unexpected Anthropic output/cap")
        text = "".join(b["text"] for b in response["content"])
        # Qwen IDs are renderer accounting; API usage above is billing authority.
        return DecodeResult(
            text,
            tuple(s.qwen_encode(text)),
            eos=s.qwen_encode("<|im_end|>")[0] if stop == "end_turn" else None,
            truncated=stop == "max_tokens",
        )


def driver():
    spec = importlib.util.spec_from_file_location(
        "slab2_driver", Path(__file__).with_name("composition_pilot5.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(
    out,
    *,
    family="dev",
    model="claude-sonnet-5",
    mock=False,
    client=None,
    prices=None,
    spend_approved=False,
    n_rounds=16,
    manifest_path=None,
):
    if family not in {"dev", "eval"}:
        raise ValueError("unknown bank")
    if client is None and not mock:
        client = AnthropicClient(spend_approved=spend_approved)
    root = Path(out)
    root.mkdir(parents=True, exist_ok=False)
    d = driver()
    receipt = json.loads(
        Path(
            manifest_path
            or Path(__file__).parents[1] / "tests/fixtures/slab2_manifest.json"
        ).read_text()
    )
    manifests = receipt["banks" if n_rounds == 16 else "fallback_banks"][family]
    episodes = s.bank(family, n_rounds=n_rounds)
    if [e.manifest() for e in episodes] != manifests:
        raise ValueError("bank differs from frozen manifest")
    rates = PRICES if prices is None else prices
    d.write(
        root / "registration.json",
        dict(
            arm="X",
            subarms=["R", "N"],
            model=model,
            mock=mock,
            prices=rates,
            source_sha256=s.hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            driver_sha256=s.hashlib.sha256(Path(d.__file__).read_bytes()).hexdigest(),
            manifests=manifests,
            projection=projection(len(episodes), model, rates, n_rounds),
        ),
    )

    def factory(e, a, i):
        return AnthropicDecoder(
            MockClient(s.reference(e, i)) if mock else client,
            root / "api.jsonl",
            model=model,
            prices=rates,
            episode_id=e.episode_id,
            arm=a,
            turn=i,
        )

    lanes = [
        d.run_lane(
            root / e.episode_id / a,
            e,
            a,
            factory,
            n_rounds=n_rounds,
            freeze_receipt=e.manifest()["episode_sha256"],
        )
        for e in episodes
        for a in "RN"
    ]
    usage = [json.loads(line) for line in (root / "api.jsonl").read_text().splitlines()]
    summary = dict(
        arm="X",
        mock=mock,
        model=model,
        calls=len(usage),
        input_tokens=sum(r["input_tokens"] for r in usage),
        output_tokens=sum(r["output_tokens"] for r in usage),
        usd_estimate=sum(r["usd_estimate"] for r in usage),
        scoring=(
            "raw pending-floor outcomes; use frozen local T floor via driver.rescore"
        ),
        lanes=[{k: v for k, v in lane.items() if k != "records"} for lane in lanes],
    )
    d.write(root / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--spend-approved-by-brian", action="store_true")
    parser.add_argument("--family", choices=("dev", "eval"), default="dev")
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--prices", type=Path)
    parser.add_argument("--n-rounds", type=int, choices=(12, 16), default=16)
    args = parser.parse_args()
    prices = json.loads(args.prices.read_text()) if args.prices else None
    if args.out is None:
        print(
            compact([projection(n, args.model, prices, args.n_rounds) for n in (8, 64)])
        )
    else:
        print(
            compact(
                run(
                    args.out,
                    family=args.family,
                    model=args.model,
                    mock=args.mock,
                    prices=prices,
                    spend_approved=args.spend_approved_by_brian,
                    n_rounds=args.n_rounds,
                )
            )
        )


if __name__ == "__main__":
    main()

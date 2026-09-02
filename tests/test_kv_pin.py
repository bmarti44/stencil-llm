# ruff: noqa: E501
"""LEDGER-KV prerequisite: pinned KV slots that survive eviction (TDD).

KVCache.evict(drop_start, drop_end, keep=[(s,e),...]) removes a token
range from every layer's K/V EXCEPT the kept sub-ranges (the ledger
entries), returning old->new column index maps so the wave can still
address the pinned slots. Positions of NEW tokens continue from the
original count (no re-indexing) — the feasibility probe measures whether
the trunk tolerates the resulting RoPE distances."""
import pytest
import torch

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


@pytest.fixture(scope="module")
def setup():
    from pathlib import Path

    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    root = Path(__file__).resolve().parent.parent
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    return m.to(torch.bfloat16).cuda().eval(), tok


TEXT = ("<|im_start|>user\nRemember this rule: always mention a lantern. "
        "Now here is a long unrelated story about the harbor, the market, the rain, "
        "the ferry, the bakery, the clocktower and the orchard, repeated for length. "
        "The story goes on and on with many details about the town and its people. "
        "Finally, write two sentences about a garden.<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n")


def test_evict_keeps_pinned_columns_and_maps_indices(setup):
    from stencil.qwen3 import KVCache
    m, tok = setup
    ids = tok.encode(TEXT).ids
    cache = KVCache()
    with torch.no_grad():
        m(torch.tensor([ids], device="cuda"), cache=cache)
    T = len(ids)
    rule = (5, 14)                      # the "always mention a lantern" span
    drop = (rule[1] + 2, T - 20)        # evict the story, keep the rule + the tail
    index_map = cache.evict(drop[0], drop[1], keep=[rule])
    new_T = cache.k[0].shape[2]
    assert new_T == T - (drop[1] - drop[0])
    assert all(cache.k[L].shape[2] == new_T and cache.v[L].shape[2] == new_T for L in range(28))
    # pinned columns survive and are addressable
    for old in range(*rule):
        assert old in index_map and 0 <= index_map[old] < new_T
    # evicted columns are gone
    assert all(old not in index_map for old in range(rule[1] + 2, drop[1]))
    # positions of NEW tokens continue from the ORIGINAL length (no re-indexing)
    assert cache.length == T


def test_pinned_slot_is_reachable_by_bias_after_eviction(setup):
    """the point of pinning: attention can still be steered to the rule
    after its surrounding text is gone — a bias on the pinned columns must
    change the next-token logits, and generation must stay non-degenerate."""
    from stencil.bench import EOS, WAVE_LAYERS
    from stencil.qwen3 import KVCache
    m, tok = setup
    ids = tok.encode(TEXT).ids
    T = len(ids)
    rule = (5, 14)

    def run(bias_amt):
        cache = KVCache()
        with torch.no_grad():
            m(torch.tensor([ids], device="cuda"), cache=cache)
            imap = cache.evict(rule[1] + 2, T - 20, keep=[rule])
            cols = [imap[o] for o in range(*rule)]
            out, nxt = [], int(m(torch.tensor([[ids[-1]]], device="cuda"), cache=cache)[0, -1].argmax())
            # note: the last prompt token was re-fed above only to obtain a first logit;
            # continue greedily with/without bias on the pinned columns
            for _ in range(24):
                if nxt in EOS:
                    break
                out.append(nxt)
                ab = None
                if bias_amt:
                    row = torch.zeros(1, cache.k[0].shape[2] + 1, device="cuda")
                    row[0, cols] = bias_amt
                    ab = {L: row for L in WAVE_LAYERS}
                nxt = int(m(torch.tensor([[nxt]], device="cuda"), cache=cache, attn_bias=ab)[0, -1].argmax())
        return tok.decode(out)
    plain, biased = run(0.0), run(3.0)
    assert plain != biased                     # the pinned slot is reachable
    assert len(plain.split()) >= 4 and len(biased.split()) >= 4   # not degenerate
    assert run(3.0) == biased                   # deterministic

# ruff: noqa
# Independent replication of the Exp C paraphrase probe (novel clue phrasings).
import os, sys
os.environ["DERIVED"] = "1"
sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
sys.path.insert(0, "/home/bmarti44/stencil-llm/scripts")
import torch
import run_gpt2_arms as R
import stencil.nl_task as NT
from stencil.nl_task import BPE, batch

DEV = R.DEV
model = R.build("cache", 0)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/cache-v8derived-s0-ckpt.pt", map_location="cpu")
print("ckpt step", ck["step"])
model.load_state_dict(ck["pathway"], strict=False)
model.logit_bias = torch.nn.Parameter(ck["logit_bias"].to(DEV))
model = model.to(DEV).eval()
bpe = BPE()

NOVEL = {
    "dog": "the loyal creature famous for barking at strangers",
    "moon": "the bright object lighting up the dark evening heavens",
    "blue": "the shade of a cloudless daytime sky",
    "queen": "the woman who rules beside a crowned man",
    "green": "the shade of a freshly mowed summer lawn",
    "gold": "the shiny costly metal pirates hoard in chests",
    "snow": "the white flakes drifting down in freezing weather",
    "wolf": "the fierce forest beast known for its howl",
}
orig = dict(NT.DERIVED_CLUES)
# leak guard
for a, c in NOVEL.items():
    assert a not in c.split(), (a, c)

auto_commit = auto_correct = forced_correct = tried = 0
with torch.no_grad():
    for i, ans in enumerate(NOVEL):
        NT.DERIVED_CLUES.clear(); NT.DERIVED_CLUES.update(orig)
        NT.DERIVED_CLUES[ans] = NOVEL[ans]
        # search seeds for a derived sequence querying this answer beyond-window
        found = None
        for sd in range(R.FINAL_SPACE + 900_000 + i * 300, R.FINAL_SPACE + 900_000 + i * 300 + 300):
            s = NT.generate(sd, family="derived", bpe=bpe)
            for p, slot, a2 in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                if a2 == ans and p - s.rule_statement_pos[slot] > 756:
                    found = (sd, s, p, slot); break
            if found: break
        if not found:
            print(ans, "no beyond-window seq found"); continue
        sd, s, qp, slot = found
        tried += 1
        toks = torch.tensor([s.tokens], device=DEV)
        want = bpe.encode(" " + ans)[0]
        # (a) autonomous: learned gates end-to-end
        lg = model(toks) + model.logit_bias
        committed = False
        if model.cache_internals is not None:
            evp = {pos for pos, sl, a2 in s.rule_events if a2 == ans}
            committed = any(p in evp for _bi, p, _v, _k, _s in model.cache_internals["commits"])
        auto_commit += int(committed)
        auto_correct += int(int(lg[0, qp].argmax()) == want)
        # (b) forced write: teacher masks -> cache code -> code_override
        sal_m, com_m, labels, slot_ov = R.cache_masks([s], toks.shape[1], DEV)
        pos_emb = torch.arange(toks.shape[1], device=DEV)
        x = model.wte(toks) + model.wpe(pos_emb)
        mask = model._mask(toks.shape[1], DEV)
        for idx in range(model.INJ_LAYERS[0]):
            x = model.blocks[idx](x, mask, None, model.lora[idx], None)
        code, _, _ = model.cache(x, sal_override=sal_m, commit_override=com_m, slot_override=slot_ov)
        lg2 = model(toks, code_override=code) + model.logit_bias
        ok = int(int(lg2[0, qp].argmax()) == want)
        forced_correct += ok
        print(f"{ans:>6}: autonomous commit={int(committed)} auto_ans={int(int(lg[0, qp].argmax())==want)} forced_ans={ok}")

print(f"\nNOVEL-PHRASING PROBE (n={tried}): autonomous commits {auto_commit}/{tried}, "
      f"autonomous correct {auto_correct}/{tried}, forced-write correct {forced_correct}/{tried} (chance 1/16)")

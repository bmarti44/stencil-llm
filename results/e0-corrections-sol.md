OpenAI Codex v0.147.0
--------
workdir: /home/bmarti44/stencil-llm
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a04889-69ae-7751-b3f2-de2e74e382e4
--------
user
E0 POST-MORTEM + POSSIBLE CORRECTIONS (Brian's direct request; xhigh; web search available). You ruled KILL on E0 (registered criterion binds; fable verified every number bitwise — zero findings; your AUC readout confirmed independently: margin_delta5 0.706 flipped-direction, attn_mass 0.706, entropy_delta5 0.683, kl_focus 0.667; family-fold selection returns exactly the unfiltered +3). Brian asks: what CORRECTIONS are possible — as NEW registrations, not amendments to the killed E0? Standards: distinguish sharply between (a) corrections that address a real design flaw in E0 that the registration failed to anticipate, (b) new experiments that would test the WHEN hypothesis with more power or better labels (e.g., manufacturing a 10x larger discordant anatomy by running MORE paired calibration-style generations on fresh non-frozen synthetic rows — is 270 discordants enough for 11 features? compute it; token-level counterfactual labels from short rollouts as your original spec preferred over divergence-point-only labels; the 3-feature trajectory-dynamics probe you found post-hoc, pre-registered on FRESH anatomy so it stops being fishing), and (c) sunk-cost traps dressed as corrections (name them). Also weigh: the direction-flip finding (LOWER margin_delta5 predicts repair — margin collapse precedes a useful intervention) is mechanistically interesting and consistent with your ACC/conflict framing — does it deserve its own registered test? And the timing question: does Multi-IF (now running: base / deficit-wave / static25 over 2727 turns) change what correction is worth doing — should any correction WAIT for Multi-IF's read on whether multi-turn drift gives the wave natural headroom? End with a ranked recommendation for Brian: correction(s) worth registering NOW vs after Multi-IF vs never.
context compacted
codex
I’ll separate genuine E0 design corrections from fresh hypothesis tests and from rescue-shaped sunk costs. I’ll first anchor the answer in the governing protocol, E0 registration/artifact, and the running Multi-IF design, then use primary literature only for the sample-size and conflict-monitoring claims.
exec
/bin/bash -lc "sed -n '1,240p' plan/PROTOCOL.md && rg -n '"'^STATE|E0|Multi-IF|multi-if|EVF|divergence|discord'"' plan/LEDGER.md PLAN.md BENCH-WAVE-PLAN.md WORKLOG.md results -g '*.md' -g '*.json' | tail -n 260" in /home/bmarti44/stencil-llm
 exited 2 in 0ms:
sed: can't read plan/PROTOCOL.md: No such file or directory

exec
/bin/bash -lc "pwd && rg --files -g 'PROTOCOL.md' -g 'LEDGER.md' -g 'PLAN.md' -g '*e0*' -g '*multi*' -g 'BENCH-WAVE-PLAN.md' -g 'WORKLOG.md' | sort" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
/home/bmarti44/stencil-llm
BENCH-WAVE-PLAN.md
WORKLOG.md
archive/PLAN.md
archive/codex-agents/phase0-fixes.allow
archive/codex-agents/phase0-fixes.md
archive/codex-agents/phase0-scaffold.allow
archive/codex-agents/phase0-scaffold.md
archive/plan/LEDGER.md
archive/plan/PROTOCOL.md
archive/plan/retros/phase0.md
archive/plan/reviews/phase0/phase0-kimi.md
archive/plan/reviews/phase0/phase0.md
data/bench/multiif_en.jsonl
results/.matrix-190750be0503.json
results/.matrix-e2e0121ddf6e.json
scripts/b4_multiif.py
scripts/e0_pilot.py

codex
The current repo does not contain the instructed live `plan/PROTOCOL.md` or `plan/LEDGER.md` (only archived copies), so there is no active STATE line to follow. I’m proceeding read-only from the live plan, worklog, E0 code/artifact, and Multi-IF runner.
exec
/bin/bash -lc "rg -n -C 8 'E0|EVF|discord|Multi-IF|multi-if|deficit|kill criterion|leave-one' BENCH-WAVE-PLAN.md WORKLOG.md scripts/e0_pilot.py scripts/b4_multiif.py results/qwen/e0-pilot.json | tail -n 900" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
scripts/e0_pilot.py-1-# ruff: noqa
scripts/e0_pilot.py:2:"""EVF Phase E0 — the registered kill-fast pilot (EVF-PLAN.md).
scripts/e0_pilot.py:3:Extracts the registered feature set at each discordant divergence point
scripts/e0_pilot.py-4-(15 repairs / 12 regressions from the t30-b3 calibration anatomy),
scripts/e0_pilot.py-5-fits the deterministic logistic probe, and evaluates the REGISTERED
scripts/e0_pilot.py:6:GATE under BOTH fold schemes: leave-one-TOPIC-out and leave-one-
scripts/e0_pilot.py-7-FAMILY-out (family = first-listed constraint's family; disclosed).
scripts/e0_pilot.py-8-GATE: r+ >= 0.60 AND r- <= 0.25 in BOTH schemes. Per-item features
scripts/e0_pilot.py-9-saved (playbook)."""
scripts/e0_pilot.py-10-import json, sys
scripts/e0_pilot.py-11-from pathlib import Path
scripts/e0_pilot.py-12-ROOT = Path(__file__).resolve().parent.parent
scripts/e0_pilot.py-13-sys.path.insert(0, str(ROOT / "src"))
scripts/e0_pilot.py-14-from stencil import determinism  # noqa: F401
--
scripts/b4_multiif.py-1-# ruff: noqa
scripts/b4_multiif.py:2:"""Multi-IF English runner (EXPLORATORY, registered v3.1/v3.2): all 909
scripts/b4_multiif.py-3-conversations x 3 turns = 2727 turns; each arm consumes ITS OWN prior
scripts/b4_multiif.py-4-responses; history serialization = prior turns as user/assistant blocks
scripts/b4_multiif.py-5-WITHOUT think tags, final turn opens with the pinned assistant opener;
scripts/b4_multiif.py-6-turn t scored with turn t's instruction list/kwargs (the dataset's
scripts/b4_multiif.py-7-lists are already cumulative); per-turn-index (n=909) + pooled
scripts/b4_multiif.py-8-(n=2727) four metrics. Scoring seed pin: random.seed(stable hash of
scripts/b4_multiif.py-9-"key:turn") per scored turn (mirror of the IFEval per-row pin).
scripts/b4_multiif.py-10-Atomic per-conversation records; hash-verified resume.
--
scripts/b4_multiif.py-41-TIMEOUT_S = 300
scripts/b4_multiif.py-42-
scripts/b4_multiif.py-43-
scripts/b4_multiif.py-44-def _registered_sha(record):
scripts/b4_multiif.py-45-    return json.loads((ROOT / "results" / "qwen" / record).read_text())["selected_sha256"]
scripts/b4_multiif.py-46-
scripts/b4_multiif.py-47-
scripts/b4_multiif.py-48-def arms_table():
scripts/b4_multiif.py:49:    """v4.5 Multi-IF arms: base + DEFICIT-wave (v4.4 seed-0 Wq/Wk,
scripts/b4_multiif.py-50-    calibration-selected tau/b_max) + static-x0.25 comparator (same
scripts/b4_multiif.py-51-    controller; descriptive). Controller hash bound to the committed
scripts/b4_multiif.py-52-    training record (equivalent to a literal: the record is tracked)."""
scripts/b4_multiif.py-53-    sha = _registered_sha("b3-ce-s0.json")
scripts/b4_multiif.py-54-    return [("base", None, None),
scripts/b4_multiif.py:55:            ("deficit-wave-s0", "results/qwen/b3-ce-s0.pt", sha),
scripts/b4_multiif.py-56-            ("static25-wave-s0", "results/qwen/b3-ce-s0.pt", sha)]
scripts/b4_multiif.py-57-
scripts/b4_multiif.py-58-
scripts/b4_multiif.py-59-def seed_of(key, turn):
scripts/b4_multiif.py-60-    return int(hashlib.sha256(f"{key}:{turn}".encode()).hexdigest()[:8], 16)
scripts/b4_multiif.py-61-
scripts/b4_multiif.py-62-
scripts/b4_multiif.py-63-def turn_doc(row, t):
--
scripts/b4_multiif.py-72-    import random
scripts/b4_multiif.py-73-    p, ids, kws = turn_doc(row, t)
scripts/b4_multiif.py-74-    random.seed(seed_of(row["key"], t))
scripts/b4_multiif.py-75-    doc = {"key": 0, "prompt": p, "instruction_id_list": ids, "kwargs": kws}
scripts/b4_multiif.py-76-    return ifeval_utils.process_results(doc, [response])
scripts/b4_multiif.py-77-
scripts/b4_multiif.py-78-
scripts/b4_multiif.py-79-def user_turn_spans(history_text, enc):
scripts/b4_multiif.py:80:    """candidate spans for the deficit gate on Multi-IF: each USER
scripts/b4_multiif.py-81-    message's token span (instructions live in user turns and drift out
scripts/b4_multiif.py-82-    of focus across the conversation — the registered long-horizon
scripts/b4_multiif.py-83-    setting). The learned q/k selects among them per step."""
scripts/b4_multiif.py-84-    spans, start = [], 0
scripts/b4_multiif.py-85-    while True:
scripts/b4_multiif.py-86-        i = history_text.find("<|im_start|>user\n", start)
scripts/b4_multiif.py-87-        if i < 0:
scripts/b4_multiif.py-88-            break
--
scripts/b4_multiif.py-93-        if toks:
scripts/b4_multiif.py-94-            spans.append((toks[0], toks[-1] + 1))
scripts/b4_multiif.py-95-        start = j + 1
scripts/b4_multiif.py-96-    return spans
scripts/b4_multiif.py-97-
scripts/b4_multiif.py-98-
scripts/b4_multiif.py-99-def gen(m, tok, ctrl, history_text, mode, tau=None, b_max=None):
scripts/b4_multiif.py-100-    """cached greedy over an explicit conversation string; mode:
scripts/b4_multiif.py:101:    'base' | 'deficit' (registered adapter, user-turn spans) |
scripts/b4_multiif.py-102-    'static25' (v4.4 bias x0.25, descriptive comparator)."""
scripts/b4_multiif.py-103-    import time as _t
scripts/b4_multiif.py-104-
scripts/b4_multiif.py:105:    from stencil.bench import WAVE_LAYERS, make_deficit_hook, make_wave_bias_fn
scripts/b4_multiif.py-106-    ids = tok.encode(history_text).ids
scripts/b4_multiif.py-107-    enc = tok.encode(history_text)
scripts/b4_multiif.py-108-    cache = KVCache()
scripts/b4_multiif.py-109-    out = []
scripts/b4_multiif.py-110-    state = {}
scripts/b4_multiif.py-111-    P = len(ids)
scripts/b4_multiif.py-112-    hook = None
scripts/b4_multiif.py:113:    if mode == "deficit":
scripts/b4_multiif.py-114-        spans = user_turn_spans(history_text, enc)
scripts/b4_multiif.py-115-        state["cache_len"] = 0
scripts/b4_multiif.py:116:        hook = make_deficit_hook(ctrl, state, spans, tau, b_max)
scripts/b4_multiif.py-117-    elif mode == "static25":
scripts/b4_multiif.py-118-        inner = make_wave_bias_fn(ctrl, state)
scripts/b4_multiif.py-119-        def bias_fn(h20, Pp, past):
scripts/b4_multiif.py-120-            row = inner(h20, Pp, past)
scripts/b4_multiif.py-121-            return None if row is None else row * 0.25
scripts/b4_multiif.py-122-
scripts/b4_multiif.py-123-    t0 = _t.monotonic()
scripts/b4_multiif.py-124-    timed_out = False
scripts/b4_multiif.py-125-    with torch.no_grad():
scripts/b4_multiif.py:126:        if mode == "deficit":
scripts/b4_multiif.py:127:            logits = m(torch.tensor([ids], device="cuda"), cache=cache, deficit_hook=hook)
scripts/b4_multiif.py-128-        elif mode == "static25":
scripts/b4_multiif.py-129-            def bh(past):
scripts/b4_multiif.py-130-                def h(h20):
scripts/b4_multiif.py-131-                    row = bias_fn(h20, P, past)
scripts/b4_multiif.py-132-                    return None if row is None else {L: row for L in WAVE_LAYERS}
scripts/b4_multiif.py-133-                return (20, h)
scripts/b4_multiif.py-134-            logits = m(torch.tensor([ids], device="cuda"), cache=cache, bias_hook=bh(0))
scripts/b4_multiif.py-135-        else:
scripts/b4_multiif.py-136-            logits = m(torch.tensor([ids], device="cuda"), cache=cache)
scripts/b4_multiif.py-137-        nxt = int(logits[0, -1].argmax())
scripts/b4_multiif.py-138-        while nxt not in EOS and len(out) < MAX_NEW:
scripts/b4_multiif.py-139-            if _t.monotonic() - t0 > TIMEOUT_S:
scripts/b4_multiif.py-140-                timed_out = True
scripts/b4_multiif.py-141-                break
scripts/b4_multiif.py-142-            out.append(nxt)
scripts/b4_multiif.py:143:            if mode == "deficit":
scripts/b4_multiif.py-144-                state["cache_len"] = cache.length
scripts/b4_multiif.py:145:                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, deficit_hook=hook)
scripts/b4_multiif.py-146-            elif mode == "static25":
scripts/b4_multiif.py-147-                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, bias_hook=bh(cache.length))
scripts/b4_multiif.py-148-            else:
scripts/b4_multiif.py-149-                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache)
scripts/b4_multiif.py-150-            nxt = int(logits[0, -1].argmax())
scripts/b4_multiif.py-151-    return tok.decode(out), len(out), len(out) >= MAX_NEW, timed_out
scripts/b4_multiif.py-152-
scripts/b4_multiif.py-153-
--
scripts/b4_multiif.py-193-    summary["pooled"] = aggregate(per_turn[1] + per_turn[2] + per_turn[3])
scripts/b4_multiif.py-194-    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
scripts/b4_multiif.py-195-    print(f"[{arm_name}] " + json.dumps({k: v for k, v in summary.items() if k.startswith(("turn", "pooled"))}))
scripts/b4_multiif.py-196-
scripts/b4_multiif.py-197-
scripts/b4_multiif.py-198-def main():
scripts/b4_multiif.py-199-    global ARMS, TAU, BMAX
scripts/b4_multiif.py-200-    ARMS = arms_table()
scripts/b4_multiif.py:201:    cal = json.loads((ROOT / "results" / "qwen" / "b3-deficit-cal.json").read_text())
scripts/b4_multiif.py-202-    sel = cal["results"][cal["selected"]]
scripts/b4_multiif.py-203-    TAU, BMAX = sel["tau"], sel["b_max"]
scripts/b4_multiif.py-204-    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
scripts/b4_multiif.py-205-    data_p = ROOT / "data" / "bench" / "multiif_en.jsonl"
scripts/b4_multiif.py-206-    data_sha = hashlib.sha256(data_p.read_bytes()).hexdigest()
scripts/b4_multiif.py-207-    assert data_sha == man["converted_sha256"]["multiif_en.jsonl"]
scripts/b4_multiif.py-208-    pins = provenance_pins(ROOT, extra_files=[p for _, p, _ in ARMS if p]
scripts/b4_multiif.py-209-                           + ["data/bench/multiif_en.jsonl", "scripts/b4_multiif.py"])
--
scripts/b4_multiif.py-220-    if SMOKE:
scripts/b4_multiif.py-221-        rows = rows[:SMOKE]
scripts/b4_multiif.py-222-    for name, path, want in ARMS:
scripts/b4_multiif.py-223-        ctrl = None
scripts/b4_multiif.py-224-        if path is not None:
scripts/b4_multiif.py-225-            ctrl = WaveController(beta_max=1.0).cuda()
scripts/b4_multiif.py-226-            ctrl.load_state_dict(torch.load(ROOT / path, map_location="cpu"))
scripts/b4_multiif.py-227-            ctrl = ctrl.eval()
scripts/b4_multiif.py:228:        mode = "base" if path is None else ("deficit" if name.startswith("deficit") else "static25")
scripts/b4_multiif.py-229-        meta = {"arm": name, "ctrl": path or "none", "ctrl_sha256": (want or "none"),
scripts/b4_multiif.py-230-                "mode": mode, "tau": TAU, "b_max": BMAX,
scripts/b4_multiif.py-231-                "pins": pins, "timeout_s": TIMEOUT_S}
scripts/b4_multiif.py-232-        run_arm(m, tok, rows, name, ctrl, meta, mode)
scripts/b4_multiif.py-233-
scripts/b4_multiif.py-234-
scripts/b4_multiif.py-235-if __name__ == "__main__":
scripts/b4_multiif.py-236-    main()
--
WORKLOG.md-1320-  a WEAK moment discriminator — consistent with the wave usefully
WORKLOG.md-1321-  pressing at non-moment rows (how it beat the moment-only oracle);
WORKLOG.md-1322-  recorded before the record run per registration. The WHEN/NULL
WORKLOG.md-1323-  confusion matrix will be reported at this frozen theta.
WORKLOG.md-1324-a0f8491297a9ebfd08e92139 scripts/w3a.py
WORKLOG.md-1325-26b3340dbbdef1707b46b9ce scripts/w3b.py
WORKLOG.md-1326-- 2026-08-30, W3b RECORD RUN (results/qwen/w3b.json + w3b-trace.json):
WORKLOG.md-1327-  OVERRIDE — adoption 18/90 -> 56/90 (+42.2 pts, 2x the bar; McNemar
WORKLOG.md:1328:  one-sided p ~ 3e-12, discordant 38/0; parse cost 0) but non-target
WORKLOG.md-1329-  adherence dropped 7 > 2 -> gate FAIL on non-inferiority. Honest
WORKLOG.md-1330-  content: focus steering through the wave's actuator is powerfully
WORKLOG.md-1331-  causal and parse-safe but NOT side-effect-free. READOUT — where_acc
WORKLOG.md-1332-  0.2526 vs the 0.80 bar at frozen theta 1.9 (confusion tp73/fn216/
WORKLOG.md-1333-  fp41/tn3079) -> FAIL: the wave's field is not decodable as "the
WORKLOG.md-1334-  governing rule now" by the registered simple rule; it points where
WORKLOG.md-1335-  pressing helps, which is not a rule label. Both gates recorded as
WORKLOG.md-1336-  honest negatives on these specific formulations; trace artifact
--
WORKLOG.md-1376-  the single registered unseen prefix rendering with zero trained-
WORKLOG.md-1377-  template occurrences; this does NOT establish meaning-level
WORKLOG.md-1378-  invariance or generalization to arbitrary paraphrases.
WORKLOG.md-1379-- 2026-08-30, NEW GOAL (Brian): prove the wave on REAL benchmarks —
WORKLOG.md-1380-  IFEval first, then the most relevant others, improvement + cross-
WORKLOG.md-1381-  benchmark generalization, same reviewer loop. BENCH-WAVE-PLAN v1
WORKLOG.md-1382-  drafted (B0 identity/harness/own-baseline -> B1 zero-shot probe ->
WORKLOG.md-1383-  B2 do-no-harm -> B3 benchmark wave + proxy twin on synthetic
WORKLOG.md:1384:  constraints -> B4 sealed IFEval/Multi-IF/do-no-harm with paired
WORKLOG.md-1385-  gates). Checkpoint-i review launched. Internal-wave W3a reproduction
WORKLOG.md-1386-  audit still running; its close-out folds in when it lands.
WORKLOG.md-1387-- 2026-08-30, BENCH-WAVE checkpoint-i: fable CLEARED w/ 6 edits
WORKLOG.md-1388-  (identity settled: bitwise instruct checkpoint; vendoring landmine;
WORKLOG.md-1389-  compatibility matrix; power analysis); sol NOT CLEARED 1 CRITICAL +
WORKLOG.md-1390-  6 HIGH -> v2: sealed ordering fixed (541 touched exactly once, by
WORKLOG.md-1391-  B4; zero-shot probe moved post-seal), single-runner decision +
WORKLOG.md-1392-  per-class goldens + upstream parity + KV/timing admission,
--
WORKLOG.md-1425-  smoke prompts, mean gen ~99 tokens: base 241s / two-forward 318s;
WORKLOG.md-1426-  five-arm 541 projection 11.35h AT SHORT LENGTHS (real IFEval
WORKLOG.md-1427-  responses are 3-5x longer) -> FAILS any fast-iteration bound. The
WORKLOG.md-1428-  registered fallback triggers: KV-cache implementation in the
WORKLOG.md-1429-  hand-rolled trunk with token-by-token parity vs full forward
WORKLOG.md-1430-  INCLUDING the wave bias. CHECKPOINT-ii PACKET now holds: (1) parity
WORKLOG.md-1431-  magnitude-bound ruling (0.6955 vs 0.5, top-1 identity everywhere);
WORKLOG.md-1432-  (2) KV-cache build + parity tests; (3) the freeze list (max_new,
WORKLOG.md:1433:  MMLU-Redux revision/manifests, GSM8K shots/extractor, Multi-IF size,
WORKLOG.md-1434-  non-inferiority machinery). Goldens 25/25 green; vendoring done;
WORKLOG.md-1435-  provenance recorded.
WORKLOG.md-1436-
WORKLOG.md-1437-## 2026-08-30 — KV cache landed; registered parity criterion found unpassable, amended acceptance flagged for checkpoint ii
WORKLOG.md-1438-
WORKLOG.md-1439-- Implemented KVCache in src/stencil/qwen3.py (post-RoPE k/v cached pre-GQA-repeat;
WORKLOG.md-1440-  _rope offset; mask diagonal 1+past; capture_hidden returns layer-i input single-pass).
WORKLOG.md-1441-- The registered B0 fallback criterion "token-by-token parity vs full forward" is
--
WORKLOG.md-1449-  (<=1.0 / <=2.0 logits; top-1 must agree at every step with margin above the bound);
WORKLOG.md-1450-  (3) capture_hidden vs return_hidden within 5% of activation scale, cosine >=0.999.
WORKLOG.md-1451-  tests/test_qwen3_kv.py: 5/5 green under these criteria.
WORKLOG.md-1452-- Timing re-admission with cache (scripts/b0_timing_kv.py): five-arm 541 projection
WORKLOG.md-1453-  7.95h (was 11.35h full-forward). Caveat noted: mean gen len 100 on smoke prompts;
WORKLOG.md-1454-  long-generation IFEval prompts scale linearly (cached), not quadratically.
WORKLOG.md-1455-- Pending checkpoint-ii items now: (a) HF parity magnitude bound 0.6955 vs 0.5;
WORKLOG.md-1456-  (b) this KV parity amendment; (c) freeze list (max_new, MMLU-Redux revision,
WORKLOG.md:1457:  GSM8K demos/extractor, Multi-IF size, Tango details).
WORKLOG.md-1458-
WORKLOG.md-1459-## 2026-08-30 — B0.3 runner core + four-metric aggregate parity PASS (with two real catches)
WORKLOG.md-1460-
WORKLOG.md-1461-- src/stencil/bench.py: load/score/aggregate over the vendored verifiers +
WORKLOG.md-1462-  generate_cached (THE single generator for every arm: pinned template, KV-cached
WORKLOG.md-1463-  greedy, EOS/max_new registered). Wave bias enters via a mid-forward bias_hook at
WORKLOG.md-1464-  layer 20 — SAME-position h20 semantics (train-time teacher forcing = test-time),
WORKLOG.md-1465-  no second forward. tests/test_bench_runner.py 6/6 (hook==direct-bias bitwise;
--
WORKLOG.md-1501-    KV docstring rescoped (argmax stability guaranteed only at margin > 2D;
WORKLOG.md-1502-    agreement = empirical, fixture-local).
WORKLOG.md-1503-  * Consumer-path test: cached generation through the ACTUAL sealed trained
WORKLOG.md-1504-    WaveController (w0-ce.pt) deterministic (to re-run at pre-B4 with the
WORKLOG.md-1505-    benchmark wave). return_hidden+cache now raises (latent cache corruption).
WORKLOG.md-1506-  * pins-manifest: gsm8k train hash + demos sha256 added.
WORKLOG.md-1507-  * b0_timing_long.py running (long-output admission, FINDING-6).
WORKLOG.md-1508-- Still open for round 2: protocol freezes (MMLU loglik wave semantics +
WORKLOG.md:1509:  single-token assert; GSM8K literal serialization; Multi-IF 2727-turn
WORKLOG.md-1510-  semantics), B3 generator/matrix materialization (sol FINDING-2), runtime
WORKLOG.md-1511-  ceiling + resume-by-skip registration.
WORKLOG.md-1512-- W3a reproduction audit COMPLETE: 96/96 full-hash exact, 0 mismatches,
WORKLOG.md-1513-  broken counts match sealed (results/qwen/w3a-audit.json). The clean-format
WORKLOG.md-1514-  win is reproduction-verified; no report changes needed.
WORKLOG.md-1515-
WORKLOG.md-1516-## 2026-08-30 — round-2 packet: protocol freezes (v3.1), B3 materialized, long-output admission
WORKLOG.md-1517-
WORKLOG.md-1518-- BENCH-WAVE-PLAN.md v3.1: restored Tango rule registered; identity/KV claims
WORKLOG.md-1519-  rescoped; MMLU loglik protocol (single-token letters asserted: 362/425/356/422;
WORKLOG.md-1520-  wave bias on the scored final row only, same-position h20); GSM8K literal
WORKLOG.md:1521:  serialization + Decimal extractor; Multi-IF all-2727-turn semantics (own-arm
WORKLOG.md-1522-  history, no think blocks in history); runtime envelope (19.74 tok/s at depth,
WORKLOG.md-1523-  39h absolute ceiling, resume-by-skip atomic persistence, 3x-admission timeout);
WORKLOG.md-1524-  proxy = exact w0-proxy objective transplanted (BCE timing + uniform-span CE,
WORKLOG.md-1525-  1:1), row-matched.
WORKLOG.md-1526-- B3 MATERIALIZED: src/stencil/b3_gen.py (14 constraint types, 6 train families,
WORKLOG.md-1527-  held families zero-exposure), data/b3/compat-matrix.json (committed = code,
WORKLOG.md-1528-  asserted), data/b3/train-2000.jsonl frozen (seed 0, sha 9cb65c70..., combo
WORKLOG.md-1529-  sizes 675/661/664) — ALL 2000 canonicals pass the VENDORED checkers, all
--
WORKLOG.md-1580-  — still matched). Pilot: gain 0.238->2.0 in 100 rows, dev CE 5.636->4.598
WORKLOG.md-1581-  after 300 rows. Collapsed checkpoints deleted. Fleet relaunch after sol
WORKLOG.md-1582-  sign-off of the amendment.
WORKLOG.md-1583-- The orchestrator-is-the-terminator rule applied: fleet killed on evidence at
WORKLOG.md-1584-  epoch 1, ~10h of knowably-collapsed runs saved.
WORKLOG.md-1585-
WORKLOG.md-1586-## 2026-08-31 — B2 MMLU leg (internal wave w0-ce): do-no-harm FAIL, recorded as the real finding it is
WORKLOG.md-1587-
WORKLOG.md:1588:- base 48.05% vs wave-w0ce 45.83% on the 5330 ok-items; discordants 175
WORKLOG.md-1589-  degrade / 57 improve; Tango 95% upper bound on the drop 2.69pt >> 0.5pt
WORKLOG.md-1590-  margin -> NON_INFERIOR false (results/qwen/b2-mmlu-gate.json).
WORKLOG.md-1591-- Interpretation (registered): off-distribution gain firing — the INTERNAL
WORKLOG.md-1592-  wave, trained on session-ledger focus, fires on MMLU prompts and hurts.
WORKLOG.md-1593-  This is the removability probe's answer: w0-ce is NOT harmlessly attachable
WORKLOG.md-1594-  off-distribution. The BINDING external-claim gate is the B4-era do-no-harm
WORKLOG.md-1595-  rerun with the B3 benchmark wave; autopsy item registered for that report:
WORKLOG.md-1596-  response-row gain histograms on MMLU for both waves (w0-ce vs b3).
--
WORKLOG.md-1607-  decorative as preregistered in the v3.3 addendum).
WORKLOG.md-1608-- Reading: the trained wave helps ONLY through WHERE it points attention
WORKLOG.md-1609-  (constraint spans), not through the existence of a bias. The proxy control
WORKLOG.md-1610-  (span-supervised, no CE feedback) sits at base level — the task-CE objective
WORKLOG.md-1611-  package is what finds the useful addressing.
WORKLOG.md-1612-
WORKLOG.md-1613-## 2026-08-31 — B2 GSM8K leg (internal wave w0-ce): do-no-harm FAIL (milder), B2 complete
WORKLOG.md-1614-
WORKLOG.md:1615:- base 75.66% vs wave-w0ce 74.37% (full 1319, 4-shot); discordants 80/63;
WORKLOG.md-1616-  Tango upper 2.80pt > 1.0pt margin -> NON_INFERIOR false. Zero timeouts,
WORKLOG.md-1617-  1 truncation per arm. Both B2 probes (MMLU 2.69pt bound, GSM8K 2.80pt bound)
WORKLOG.md-1618-  agree: w0-ce fires off-distribution and harms. B2 CLOSED as a recorded
WORKLOG.md-1619-  honest finding; the binding external-claim gate remains the B4-era rerun
WORKLOG.md-1620-  with the B3 wave.
WORKLOG.md-1621-
WORKLOG.md-1622-## 2026-08-31 — IFBench verifiers vendored (fable subagent); B3 dev gate running
WORKLOG.md-1623-
--
WORKLOG.md-1710-  (gate needs +2.0). First positive generation-time delta of the program.
WORKLOG.md-1711-- Academic research (results/research-wave-generation.md): the strong scope
WORKLOG.md-1712-  hypothesis is REFUTED — SpotLight (2505.12025) reports positive IFEval
WORKLOG.md-1713-  deltas at 3-8B via DEFICIT-TRIGGERED steering (bias only when per-step
WORKLOG.md-1714-  attention to instruction spans is deficient; zero otherwise); its published
WORKLOG.md-1715-  critique of static bias predicts our x1.0 result. Contrast-pair training
WORKLOG.md-1716-  literature exists for our mutation pairs (MuSC 2502.11541); GRPO-with-
WORKLOG.md-1717-  checker-reward mature at this scale; obligation-state gating unpublished
WORKLOG.md:1718:  (open ground). Ranked: (1) deficit-triggered wave, (2) token-aware contrast
WORKLOG.md-1719-  + GRPO on the 264k controller, (3) scope-graded battery registration.
WORKLOG.md-1720-
WORKLOG.md:1721:## 2026-08-31 — sol results review: sweep legit-but-unauditable; data EXHAUSTED; deficit-trigger registered as the LAST rescue
WORKLOG.md-1722-
WORKLOG.md-1723-- A (accuracy): x1.0 arm fully audited (165/196 base, 156/196 wave, 6 fixes/15
WORKLOG.md-1724-  regressions). x0.5/x0.25 numbers plausible but NOT auditable — I ran the
WORKLOG.md-1725-  sweep without per-row records (the playbook rule violated a third time;
WORKLOG.md-1726-  lesson: EVERY evaluative run writes records, exploratory or not). n=196
WORKLOG.md-1727-  cannot distinguish +1.5 from +2.0 (best-case paired p=0.125); the gate miss
WORKLOG.md-1728-  is exactly one item. Post-hoc scaling = legitimate exploration, NOT a gate
WORKLOG.md-1729-  result (registered operating point was beta 1.0; x0.25 chosen after seeing
WORKLOG.md-1730-  this dev set; seed 0 only).
WORKLOG.md-1731-- B (data): EXHAUSTED — registered ruling: no v4.5 data curation. Residual
WORKLOG.md-1732-  label note (12.8% weighted-token fraction; 1.6% pathological rows) documented
WORKLOG.md-1733-  for any future objective reuse; cannot explain a one-item miss.
WORKLOG.md:1734:- C (path): REGISTER deficit-triggered steering (SpotLight-adapted): frozen
WORKLOG.md-1735-  v4.4 Wq/Wk select the governing constraint span; per step/layer/head compute
WORKLOG.md-1736-  post-softmax mass psi on it; zero bias if psi >= tau; else uniform span bias
WORKLOG.md-1737-  min(b_max, logit(tau) - logit(psi)) (exact odds correction — sol corrected
WORKLOG.md:1738:  the research note's log-ratio). Deterministic battery: zero-deficit ->
WORKLOG.md:1739:  BITWISE base logits; forced deficit -> finite nonzero; uncapped post-bias
WORKLOG.md-1740-  mass == tau; full intervention logging. tau from a frozen grid on a NEW
WORKLOG.md-1741-  calibration stream; ONE confirmation on >= 512 fresh prompt-disjoint rows;
WORKLOG.md-1742-  gate +2.0pts AND one-sided exact McNemar p < 0.05; seed-1 replication before
WORKLOG.md-1743-  sealed IFEval. STOP-LOSS: iteration 3 is the LAST single-turn rescue — no
WORKLOG.md-1744-  recalibration after confirmation; failure CLOSES the line; contrast/GRPO
WORKLOG.md-1745-  would need Brian's separate authorization.
WORKLOG.md-1746-
WORKLOG.md-1747-## 2026-08-31 — fable verification: numbers ACCURATE, +1.5 NOT significant; v4.5 launched
WORKLOG.md-1748-
WORKLOG.md-1749-- Fable reproduced x0.25 BIT-FOR-BIT (168/196 = 0.857143, fresh code path);
WORKLOG.md-1750-  base/wave-s0 rescored 0-mismatch; training record + shas verified; no
WORKLOG.md:1751:  contamination. STATISTICS: 7-vs-4 discordants -> McNemar p=0.549, delta CI
WORKLOG.md-1752-  [-1.8, +4.8]pt; ~1900 paired rows to confirm ANY positive effect. The honest
WORKLOG.md-1753-  statement: quarter-dose is indistinguishable from base AND from the gate at
WORKLOG.md-1754-  n=196. FINDING-1 fixed: v4.4 checkpoint was working-tree-only, now committed.
WORKLOG.md-1755-  FINDING-2 stands: x0.5 sweep number is WORKLOG-prose-only (descriptive).
WORKLOG.md-1756-- Confirmation stream extended 512 -> 1024 PRE-RUN on the power analysis
WORKLOG.md-1757-  (registered in the manifest note). Deficit-gate mechanism committed with
WORKLOG.md:1758:  4/4 battery (bitwise-base at zero deficit; exact odds correction verified
WORKLOG.md-1759-  numerically). Calibration chain launched: v4.4 seed-1 training then the
WORKLOG.md-1760-  one-shot tau x b_max grid on cal-v45.
WORKLOG.md-1761-
WORKLOG.md:1762:## 2026-08-31 — Brian's ruling: Multi-IF is the decisive experiment; "go from there" on its data
WORKLOG.md-1763-
WORKLOG.md-1764-- sol xhigh eval+research (results/b3-eval-research-sol.md): confirmation pass
WORKLOG.md:1765:  odds ~32%; scalar deficit thresholds condemned (15 repairs / 12 regressions,
WORKLOG.md-1766-  amplitude not the missing ingredient; oracle WHEN-chooser ceiling +7.5);
WORKLOG.md-1767-  untried families mapped (retrieval branch, obligation tracker, causal WHEN
WORKLOG.md-1768-  labels); constrained decoding named the honest single-turn ceiling; MMMT-IF
WORKLOG.md-1769-  +22.3pt from re-appending dispersed instructions = published proof the
WORKLOG.md-1770-  multi-turn failure is FOCUS/RETRIEVAL — the wave's arena.
WORKLOG.md-1771-- ORDER: sealed confirmation completes as registered (stop-loss honored either
WORKLOG.md:1772:  way), then Multi-IF three arms (base / deficit-wave user-turn spans /
WORKLOG.md-1773-  static-x0.25) regardless of outcome. Next program decisions wait for
WORKLOG.md:1774:  Multi-IF data (Brian).
WORKLOG.md-1775-
WORKLOG.md:1776:## 2026-08-31 — BRIAN'S RULING: v4.5 confirmation killed mid-run; EVF program authorized
WORKLOG.md-1777-
WORKLOG.md-1778-- Confirmation seed-0 stopped at Brian's direction (~100/1024 base records
WORKLOG.md:1779:  retained untouched; recorded ABANDONED-BY-RULING). EVF-PLAN.md committed:
WORKLOG.md:1780:  Phase E0 = kill-fast pilot probe on the recorded 15/12 calibration anatomy
WORKLOG.md-1781-  (registered gate r+>=0.60 / r-<=0.25 under topic AND family holdout);
WORKLOG.md:1782:  E1 (GRU tracker + two-stage EVF firing) gated on E0 + separate go.
WORKLOG.md-1783-  Red/green TDD + deterministic proofs required throughout.
WORKLOG.md-1784-
WORKLOG.md:1785:## 2026-08-31 — EVF E0 pilot: registered gate FAIL (family-holdout kill criterion triggered)
WORKLOG.md-1786-
WORKLOG.md-1787-- 15/12 anatomy, 11 registered features, deterministic probe. Topic folds:
WORKLOG.md-1788-  r+ 0.733 / r- 0.417 (needs <=0.25). Family folds: r+ 0.733 / r- 0.667 —
WORKLOG.md:1789:  near-indiscriminate under family holdout -> the registered kill criterion
WORKLOG.md-1790-  fires. Per-item features committed (results/qwen/e0-pilot.json).
WORKLOG.md-1791-- Honest caveats for the review: n=27 is tiny for 11 features; the gate was
WORKLOG.md:1792:  registered knowing this. The pre-registered sol+fable review of the E0
WORKLOG.md-1793-  result convenes before ANY next step.
--
BENCH-WAVE-PLAN.md-68-
BENCH-WAVE-PLAN.md-69-ONE sealed run each (fail-closed, pinned hashes, per-prompt records in
BENCH-WAVE-PLAN.md-70-the artifact from the start):
BENCH-WAVE-PLAN.md-71-- IFEval 541 (untouched by anything upstream): arms base / wave /
BENCH-WAVE-PLAN.md-72-  proxy. PRIMARY: prompt-level strict accuracy, paired McNemar
BENCH-WAVE-PLAN.md-73-  one-sided p < 0.05 AND delta >= +2.0 points (>= ~11 prompts; below
BENCH-WAVE-PLAN.md-74-  the +3-7 published steering band but above noise). Causal: wave >
BENCH-WAVE-PLAN.md-75-  proxy.
BENCH-WAVE-PLAN.md:76:- Multi-IF (English subset, registered size): the long-horizon claim;
BENCH-WAVE-PLAN.md-77-  same metrics; EXPLORATORY gate (report, no pass/fail — first
BENCH-WAVE-PLAN.md-78-  multi-turn external exposure).
BENCH-WAVE-PLAN.md-79-- Do-no-harm rerun WITH the B3 wave (same B2 bounds — now a real gate).
BENCH-WAVE-PLAN.md-80-Decision table: IFEval PASS + do-no-harm PASS -> the wave mechanism is
BENCH-WAVE-PLAN.md-81-externally validated on its first real benchmark; either FAIL -> honest
BENCH-WAVE-PLAN.md:82:negative with autopsy; Multi-IF informs the NEXT benchmark's
BENCH-WAVE-PLAN.md-83-registration (cross-benchmark generalization = a fresh checkpoint-iii
BENCH-WAVE-PLAN.md-84-registration naming benchmark #3 by what B4 reveals, e.g. FollowBench/
BENCH-WAVE-PLAN.md-85-ComplexBench/IFBench for taxonomy hold-out, or RULER-style long-context
BENCH-WAVE-PLAN.md:86:if Multi-IF shows length sensitivity).
BENCH-WAVE-PLAN.md-87-
BENCH-WAVE-PLAN.md-88-## Frozen rules
BENCH-WAVE-PLAN.md-89-
BENCH-WAVE-PLAN.md-90-Seeds: synthetic-train generator seed 0; subsets drawn with registered
BENCH-WAVE-PLAN.md-91-seed 1; one sealed attempt per B4 item, no redraws. TDD for verifiers,
BENCH-WAVE-PLAN.md-92-template, generator, canonical builders. Reviews: (i) this plan,
BENCH-WAVE-PLAN.md-93-(ii) B0 results + B3 preregistration details, (iii) pre-B4, (iv) close.
BENCH-WAVE-PLAN.md-94-Playbook governs (pipefail, consumer-path tests, per-work records in
--
BENCH-WAVE-PLAN.md-99-
BENCH-WAVE-PLAN.md-100-- B0.1 SETTLED by fable's file-level audit: the local shards are
BENCH-WAVE-PLAN.md-101-  BITWISE Qwen/Qwen3-1.7B (instruct) — shard sha256 169ad53e... /
BENCH-WAVE-PLAN.md-102-  912becff... match the HF LFS hashes; Base excluded (different repo
BENCH-WAVE-PLAN.md-103-  shape/hash). Remaining B0.1 work: fresh logit-parity spot check of
BENCH-WAVE-PLAN.md-104-  qwen3-1.7b.pt vs shards; record both shard hashes in the artifact.
BENCH-WAVE-PLAN.md-105-- B0.2 additions: ONE-TIME pinned downloads (exact revision + sha256
BENCH-WAVE-PLAN.md-106-  recorded, files committed): IFEval input_data.jsonl (541), MMLU
BENCH-WAVE-PLAN.md:107:  subset source, GSM8K subset, Multi-IF English subset; NO `datasets`
BENCH-WAVE-PLAN.md-108-  dependency. Verifier vendoring: the 4 lm-eval ifeval files +
BENCH-WAVE-PLAN.md-109-  langdetect/immutabledict/nltk pinned in pyproject + punkt_tab
BENCH-WAVE-PLAN.md-110-  COMMITTED to the repo with instructions_util's TOP-LEVEL
BENCH-WAVE-PLAN.md-111-  download_nltk_resources() call patched to a local-path assert (the
BENCH-WAVE-PLAN.md-112-  no-top-level-work rule applies to vendored code); confirm `random`
BENCH-WAVE-PLAN.md-113-  unused on the checking path. Fixtures must include one
BENCH-WAVE-PLAN.md-114-  sentence-count (nltk) and one langdetect constraint. Chat template:
BENCH-WAVE-PLAN.md-115-  pinned deterministic f-string for non-thinking single-turn,
BENCH-WAVE-PLAN.md-116-  verified against HF apply_chat_template in an ISOLATED oracle env
BENCH-WAVE-PLAN.md-117-  (convert-script pattern); stop on token 151645; greedy.
BENCH-WAVE-PLAN.md-118-- Checkpoint-ii registration list (frozen before B0.3): max_new;
BENCH-WAVE-PLAN.md:119:  stop rule; Multi-IF English subset size; MMLU subset source split +
BENCH-WAVE-PLAN.md-120-  shuffling procedure.
BENCH-WAVE-PLAN.md-121-- B3 additions: an explicit CONSTRAINT-COMPATIBILITY MATRIX (JSON
BENCH-WAVE-PLAN.md-122-  cannot co-occur with bullets/paragraphs/start-end; end-with is
BENCH-WAVE-PLAN.md-123-  exact-suffix; word counts use the VERIFIER'S tokenizer); the
BENCH-WAVE-PLAN.md-124-  keyword-forbidden generator excludes stopwords and the entire
BENCH-WAVE-PLAN.md-125-  filler-template lexicon; every canonical response verified by the
BENCH-WAVE-PLAN.md-126-  VENDORED checker before freeze.
BENCH-WAVE-PLAN.md:127:- B4: exact one-sided BINOMIAL McNemar; the full discordant table
BENCH-WAVE-PLAN.md-128-  (b, c) goes in the artifact.
BENCH-WAVE-PLAN.md-129-- FIREWALL: B3 generator parameters/phrasings may not be derived from
BENCH-WAVE-PLAN.md-130-  inspection of per-prompt B1 IFEval failures (taxonomy-level use
BENCH-WAVE-PLAN.md-131-  only) — closes the B1->B4 adaptive-leak path.
BENCH-WAVE-PLAN.md-132-
BENCH-WAVE-PLAN.md-133-## v2 (sol checkpoint-i: 1 CRITICAL + 6 HIGH; all folded — SUPERSEDES
BENCH-WAVE-PLAN.md-134-conflicting v1/v1.1 text)
BENCH-WAVE-PLAN.md-135-
--
BENCH-WAVE-PLAN.md-181-per-constraint relevance mask), span CE over all active constraint
BENCH-WAVE-PLAN.md-182-spans at those same rows; architecture/actuator/init/optimizer/steps
BENCH-WAVE-PLAN.md-183-identical. Otherwise the claim is scoped to "CE beats a start-only
BENCH-WAVE-PLAN.md-184-heuristic".
BENCH-WAVE-PLAN.md-185-
BENCH-WAVE-PLAN.md-186-H6. B4 causal gate: wave-vs-proxy requires its OWN one-sided
BENCH-WAVE-PLAN.md-187-prompt-level exact binomial McNemar p < 0.05 (raw inequality
BENCH-WAVE-PLAN.md-188-insufficient). Benchmark #3 PREREGISTERED NOW: IFBench (58 OOD
BENCH-WAVE-PLAN.md:189:verifier families) as the cross-taxonomy test; Multi-IF described as
BENCH-WAVE-PLAN.md-190-exploratory three-turn transfer, not long-horizon. External-validation
BENCH-WAVE-PLAN.md-191-claims require a SECOND frozen training seed (registered now: init
BENCH-WAVE-PLAN.md-192-seeds 0 and 1, both trained, both evaluated in B4; the claim needs
BENCH-WAVE-PLAN.md-193-both to pass the primary gate).
BENCH-WAVE-PLAN.md-194-
BENCH-WAVE-PLAN.md-195-H7. Seeds/manifests: exact train/dev/calibration streams, dataset
BENCH-WAVE-PLAN.md-196-revisions, and committed item manifests replace the two generic seeds.
BENCH-WAVE-PLAN.md-197-
--
BENCH-WAVE-PLAN.md-205-  post-seal." H1's timing admission rebinds to "before B4".
BENCH-WAVE-PLAN.md-206-- B0.1 PARITY CRITERIA (frozen): chat-template token ids bitwise
BENCH-WAVE-PLAN.md-207-  equal; top-1 equal on every fixture; all logits finite;
BENCH-WAVE-PLAN.md-208-  max_abs_error <= 1e-3 (registered tolerance; identity comes from
BENCH-WAVE-PLAN.md-209-  file hashes, behavior from these criteria).
BENCH-WAVE-PLAN.md-210-- B2 is BLOCKED until checkpoint ii freezes mechanically: MMLU-Redux
BENCH-WAVE-PLAN.md-211-  exact revision + item count + manifests; margins with inherited
BENCH-WAVE-PLAN.md-212-  status stated; null hypotheses; alpha = 0.05 one-sided; test
BENCH-WAVE-PLAN.md:213:  construction (paired exact binomial on discordant items per suite);
BENCH-WAVE-PLAN.md-214-  aggregation rule across MMLU subjects (pooled, registered).
BENCH-WAVE-PLAN.md-215-- B4 ARMS (one sealed job): base, wave-s0, proxy-s0, wave-s1,
BENCH-WAVE-PLAN.md-216-  proxy-s1. Gate mapping: EXTERNAL CLAIM requires BOTH seeds to pass
BENCH-WAVE-PLAN.md-217-  the primary gate AND do-no-harm; CAUSAL ATTRIBUTION requires both
BENCH-WAVE-PLAN.md-218-  seed-specific causal McNemars to pass; a single-seed pass is
BENCH-WAVE-PLAN.md-219-  reported as artifact-specific, not external validation.
BENCH-WAVE-PLAN.md-220-- IFBench FULLY PREREGISTERED at checkpoint iii (pre-B4, before any
BENCH-WAVE-PLAN.md-221-  B4 result exists): revision, split, metric, the same five arms,
--
BENCH-WAVE-PLAN.md-283-  bitwise; wave path demonstrably reaches logits (tests 6/6).
BENCH-WAVE-PLAN.md-284-
BENCH-WAVE-PLAN.md-285-### Freeze list (frozen at this checkpoint, before any 541 exposure)
BENCH-WAVE-PLAN.md-286-
BENCH-WAVE-PLAN.md-287-- Decoding: greedy; max_new 1024; EOS {151645, 151643}; truncation
BENCH-WAVE-PLAN.md-288-  recorded per prompt; pinned non-thinking template f-string (bitwise
BENCH-WAVE-PLAN.md-289-  vs HF apply_chat_template, enable_thinking=False).
BENCH-WAVE-PLAN.md-290-- Data pins (data/bench/pins-manifest.json; converted JSONL committed):
BENCH-WAVE-PLAN.md:291:  GSM8K test 1319 @ 740312ad; MMLU-Redux-2.0 5700 @ 372ea425; Multi-IF
BENCH-WAVE-PLAN.md-292-  4501 @ 0ab97ce0, English subset 909 rows (language=='English',
BENCH-WAVE-PLAN.md-293-  sorted by (key, turn_index)).
BENCH-WAVE-PLAN.md-294-- MMLU-Redux protocol: items with error_type=="ok" ONLY (5330);
BENCH-WAVE-PLAN.md-295-  zero-shot; prompt "Question: {q}\nA. {c0}\nB. {c1}\nC. {c2}\nD. {c3}\n
BENCH-WAVE-PLAN.md-296-  Answer:" through the pinned chat template; score = argmax over the
BENCH-WAVE-PLAN.md-297-  summed logprob of " A"/" B"/" C"/" D" continuations (loglikelihood,
BENCH-WAVE-PLAN.md-298-  no generation); pooled across subjects (registered v2 H3).
BENCH-WAVE-PLAN.md-299-- GSM8K protocol: FULL test 1319; 4-shot with the four demos =
BENCH-WAVE-PLAN.md-300-  train rows 0-3 of the pinned revision (data/bench/gsm8k_demos.jsonl;
BENCH-WAVE-PLAN.md-301-  train raw sha256 ea82612e...); demos joined as Q/A pairs in one user
BENCH-WAVE-PLAN.md-302-  message; answer extractor = LAST number in the response (commas and
BENCH-WAVE-PLAN.md-303-  $ stripped; regex -?[0-9][0-9,]*\.?[0-9]*), exact match vs the #### 
BENCH-WAVE-PLAN.md-304-  gold value.
BENCH-WAVE-PLAN.md-305-- Do-no-harm construction (Tango, fail-closed): margins MMLU-Redux
BENCH-WAVE-PLAN.md-306-  0.5pt / GSM8K 1.0pt, alpha 0.05 one-sided. Registered rule: with
BENCH-WAVE-PLAN.md:307:  discordant counts n10 (base right, wave wrong) and n01 (converse),
BENCH-WAVE-PLAN.md-308-  p_up = BetaInv(0.95, n10+1, n01) (exact Clopper-Pearson upper bound),
BENCH-WAVE-PLAN.md-309-  drop_up = (2*p_up - 1)*(n10+n01)/N; NON-INFERIOR iff drop_up <=
BENCH-WAVE-PLAN.md-310-  margin. Non-convergence or any scoring error = FAIL (fail-closed).
BENCH-WAVE-PLAN.md:311:- Multi-IF: English 909, EXPLORATORY (report only), turn-wise IFEval
BENCH-WAVE-PLAN.md-312-  metrics via the same vendored verifiers, multi-turn template =
BENCH-WAVE-PLAN.md-313-  concatenated pinned single-turn blocks with prior model turns.
BENCH-WAVE-PLAN.md-314-- Single-use invariant restated: no model generation, scoring of model
BENCH-WAVE-PLAN.md-315-  outputs, or per-prompt inspection of the 541 before sealed B4.
BENCH-WAVE-PLAN.md-316-
BENCH-WAVE-PLAN.md-317-### B3 preregistration details
BENCH-WAVE-PLAN.md-318-
BENCH-WAVE-PLAN.md-319-- Families (IFEval taxonomy groups): change_case, keywords, length,
--
BENCH-WAVE-PLAN.md-393-- GSM8K serialization (literal): one user message =
BENCH-WAVE-PLAN.md-394-  "Question: {q_demo1}\nAnswer: {a_demo1}\n\n" x4 demos (answer text
BENCH-WAVE-PLAN.md-395-  verbatim from the pinned train rows INCLUDING their "#### n" line)
BENCH-WAVE-PLAN.md-396-  + "Question: {q_test}\nAnswer:"; through the pinned chat template;
BENCH-WAVE-PLAN.md-397-  greedy, max_new 1024, EOS {151645,151643}, no other stop strings.
BENCH-WAVE-PLAN.md-398-  Extractor: last match of -?[0-9][0-9,]*\.?[0-9]* after removing
BENCH-WAVE-PLAN.md-399-  "$"; commas stripped; trailing "." stripped; compared as
BENCH-WAVE-PLAN.md-400-  python Decimal equality vs the gold "#### " value.
BENCH-WAVE-PLAN.md:401:- Multi-IF: ALL 2727 turns (909 conversations x 3 embedded turns),
BENCH-WAVE-PLAN.md-402-  sequential; each arm consumes ITS OWN prior responses. History
BENCH-WAVE-PLAN.md-403-  serialization: prior turns as
BENCH-WAVE-PLAN.md-404-  "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n{r}<|im_end|>\n"
BENCH-WAVE-PLAN.md-405-  (no think blocks in history), final turn opens with the pinned
BENCH-WAVE-PLAN.md-406-  assistant opener incl. empty think block. Turn t scored with turn
BENCH-WAVE-PLAN.md-407-  t's instruction_id_list/kwargs only (per the dataset columns).
BENCH-WAVE-PLAN.md-408-  Reporting: per-turn-index (n=909 each) + pooled (n=2727) four
BENCH-WAVE-PLAN.md-409-  metrics; EXPLORATORY (unchanged).
--
BENCH-WAVE-PLAN.md-549-  atomic records, hash-verified resume, gain telemetry). Launch order:
BENCH-WAVE-PLAN.md-550-  base, wave-s0, proxy-s0, wave-s1, proxy-s1 (sequential, uncontended
BENCH-WAVE-PLAN.md-551-  GPU). Controllers: results/qwen/b3-{ce,proxy}-s{0,1}.pt (selected
BENCH-WAVE-PLAN.md-552-  checkpoints; sha256s in their .json records).
BENCH-WAVE-PLAN.md-553-- Do-no-harm rerun (the BINDING gate): b2_mmlu.py + b2_gsm8k.py with
BENCH-WAVE-PLAN.md-554-  CTRL=b3-ce-s0 and b3-ce-s1 (wave arms; margins/Tango as frozen).
BENCH-WAVE-PLAN.md-555-  The w0-ce B2 MMLU FAIL (drop upper bound 2.69pt) stands recorded as
BENCH-WAVE-PLAN.md-556-  the internal wave's off-distribution answer.
BENCH-WAVE-PLAN.md:557:- Multi-IF (exploratory): scripts/b4_multiif.py (committed; smoked on
BENCH-WAVE-PLAN.md-558-  1 conversation); PROPOSED arms = base, wave-s0, proxy-s0 (three, not
BENCH-WAVE-PLAN.md-559-  five — 2727 turns x 5 arms exceeds the runtime envelope; reviewers
BENCH-WAVE-PLAN.md-560-  rule).
BENCH-WAVE-PLAN.md-561-- Evidence bundle for this checkpoint: b3-ce/proxy-s0/s1.json (training
BENCH-WAVE-PLAN.md-562-  records), b3-ablations.json (K-perm + uniform controls; gain
BENCH-WAVE-PLAN.md-563-  saturation), b3-consumer-path.json (all four controllers nonzero
BENCH-WAVE-PLAN.md-564-  field + logit movement + deterministic through the cache),
BENCH-WAVE-PLAN.md-565-  b2-mmlu-gate.json (FAIL recorded), b2-gsm8k gate (pending, appended
--
BENCH-WAVE-PLAN.md-581-  enforces the 300s per-prompt deadline in the generation loop; a
BENCH-WAVE-PLAN.md-582-  timed-out PARTIAL response is scored as-is with the timeout flag in
BENCH-WAVE-PLAN.md-583-  the record and all reporting. Registered wording narrowed: the
BENCH-WAVE-PLAN.md-584-  truncation point of a timed-out item is load-dependent (the flag is
BENCH-WAVE-PLAN.md-585-  a runaway backstop ~5.6x the admission's worst case, not an expected
BENCH-WAVE-PLAN.md-586-  path). Gain telemetry includes the prefill's scored row (fable
BENCH-WAVE-PLAN.md-587-  FINDING-3).
BENCH-WAVE-PLAN.md-588-- B2 BINDING ADJUDICATOR (sol FINDING-3): scripts/b2_adjudicate.py —
BENCH-WAVE-PLAN.md:589:  frozen construction; per-item discordances only; registered
BENCH-WAVE-PLAN.md-590-  controller hashes enforced; BOTH seeds must pass BOTH suites
BENCH-WAVE-PLAN.md-591-  (MMLU < 0.5pt, GSM8K < 1.0pt Tango-strict); fail-closed on any
BENCH-WAVE-PLAN.md-592-  missing record/provenance/non-convergence.
BENCH-WAVE-PLAN.md-593-- B3 GATES (sol FINDING-4): (a) gradient battery on the REAL loss —
BENCH-WAVE-PLAN.md-594-  results/qwen/b3-battery.json PASS (all params finite nonzero;
BENCH-WAVE-PLAN.md-595-  dCE/dbias nonzero). (b) REGISTERED BEFORE RUNNING — dev-200
BENCH-WAVE-PLAN.md-596-  GENERATION adherence gate: all five arms generate on the dev-200
BENCH-WAVE-PLAN.md-597-  prompts (same decoding/deadline as B4); metric = strict-prompt
--
BENCH-WAVE-PLAN.md-604-  are disjoint; word-count/format/keyword SEMANTICS overlap B3
BENCH-WAVE-PLAN.md-605-  families). Transfer claims are scoped to unseen verifier classes and
BENCH-WAVE-PLAN.md-606-  compositions, not wholly unseen constraint semantics. Full verifier
BENCH-WAVE-PLAN.md-607-  freeze (vendored ifbench package at a pinned GitHub sha + per-class
BENCH-WAVE-PLAN.md-608-  goldens + per-row seed pin where needed + the same aggregate and
BENCH-WAVE-PLAN.md-609-  paired-McNemar adjudicator as IFEval) is being committed with this
BENCH-WAVE-PLAN.md-610-  amendment; IFBench remains post-B4 in execution and gets its own
BENCH-WAVE-PLAN.md-611-  pre-run goldens review.
BENCH-WAVE-PLAN.md:612:- Multi-IF (sol FINDING-6): runner hardened to the same closed
BENCH-WAVE-PLAN.md-613-  three-arm table (base, wave-s0, proxy-s0), full pin set, real
BENCH-WAVE-PLAN.md-614-  deadline, timeout field; exploratory scope unchanged (no two-seed or
BENCH-WAVE-PLAN.md-615-  external-validation claims from it).
BENCH-WAVE-PLAN.md-616-
BENCH-WAVE-PLAN.md-617-## v4.4 — B3 recipe amendment (PENDING REVIEW; pilot evidence attached
BENCH-WAVE-PLAN.md-618-when ready; 2026-08-31)
BENCH-WAVE-PLAN.md-619-
BENCH-WAVE-PLAN.md-620-Registered dev-gate FAIL for the v3-recipe waves (base 0.865, wave-s0
--
BENCH-WAVE-PLAN.md-630-  seeds 0/1, unrounded dev task CE selection).
BENCH-WAVE-PLAN.md-631-- GATE: same registered dev generation gate on dev-v43 (196):
BENCH-WAVE-PLAN.md-632-  each wave seed >= base + 2.0pts strict adherence; base re-measured
BENCH-WAVE-PLAN.md-633-  on dev-v43.
BENCH-WAVE-PLAN.md-634-- FIREWALL disclosure: postscript_marker 'P.P.S' exempt from kwargs
BENCH-WAVE-PLAN.md-635-  disjointness (upstream regex-escape landmine forces the special-
BENCH-WAVE-PLAN.md-636-  cased marker; the postscript VALUE varies per row from the prompt).
BENCH-WAVE-PLAN.md-637-
BENCH-WAVE-PLAN.md:638:## v4.5 — deficit-triggered wave (THE FINAL single-turn rescue;
BENCH-WAVE-PLAN.md-639-registered per sol's results review, 2026-08-31)
BENCH-WAVE-PLAN.md-640-
BENCH-WAVE-PLAN.md-641-Motivating evidence (exploratory, scoped): dose sweep on v4.4 wave-s0
BENCH-WAVE-PLAN.md-642-(x1.0 0.7959 / x0.5 0.8214 / x0.25 0.8571 vs base 0.8418 on dev-v43;
BENCH-WAVE-PLAN.md-643-x0.25 beats base by +1.5pts but n=196 cannot distinguish +1.5 from
BENCH-WAVE-PLAN.md-644-+2.0 — best-case paired p=0.125; sweep numbers pending fable's
BENCH-WAVE-PLAN.md-645-independent reproduction). Research prior: SpotLight (2505.12025)
BENCH-WAVE-PLAN.md:646:deficit-triggered steering with positive IFEval deltas at 3-8B.
BENCH-WAVE-PLAN.md-647-
BENCH-WAVE-PLAN.md-648-MECHANISM (implemented, battery 4/4 green): frozen v4.4 Wq/Wk select
BENCH-WAVE-PLAN.md-649-the governing Constraint: span per generated row (first-index
BENCH-WAVE-PLAN.md-650-tie-break; no span -> no intervention); per biased layer/head, measure
BENCH-WAVE-PLAN.md-651-natural post-softmax mass psi on the span; psi >= tau -> ZERO bias
BENCH-WAVE-PLAN.md-652-(bitwise base attention); else uniform span bias
BENCH-WAVE-PLAN.md-653-min(b_max, logit(tau) - logit(psi)) (exact odds correction). Every
BENCH-WAVE-PLAN.md-654-intervention logged (span, score, per-item records).
BENCH-WAVE-PLAN.md-655-
BENCH-WAVE-PLAN.md-656-CALIBRATION (one shot): frozen tau grid {0.10, 0.20, 0.30, 0.45} x
BENCH-WAVE-PLAN.md-657-b_max {3.0, 6.0} on cal-v45 (200 rows, seed 5, prompt-disjoint);
BENCH-WAVE-PLAN.md-658-select by adherence, ties -> LOWER intervention rate; base cal run as
BENCH-WAVE-PLAN.md-659-reference. No recalibration after confirmation begins.
BENCH-WAVE-PLAN.md-660-
BENCH-WAVE-PLAN.md-661-CONFIRMATION (one shot): conf-v45 (512 rows, seed 7, dev-topic,
BENCH-WAVE-PLAN.md:662:prompt-disjoint from everything). GATE: deficit-wave(seed-0 Wq/Wk)
BENCH-WAVE-PLAN.md-663->= base + 2.0pts strict adherence AND one-sided exact McNemar p<0.05
BENCH-WAVE-PLAN.md:664:AND no excess timeouts/truncations; per-row records + raw discordants
BENCH-WAVE-PLAN.md-665-saved. If seed 0 passes, REPLICATE with seed-1 Wq/Wk (same tau/b_max,
BENCH-WAVE-PLAN.md-666-no re-selection); BOTH must pass before sealed IFEval.
BENCH-WAVE-PLAN.md-667-
BENCH-WAVE-PLAN.md-668-STOP-LOSS (registered): this is recipe iteration 3 and the LAST
BENCH-WAVE-PLAN.md-669-single-turn rescue. One calibration grid, one confirmation block, no
BENCH-WAVE-PLAN.md-670-recalibration/retraining/fallbacks after seeing confirmation. Failure
BENCH-WAVE-PLAN.md-671-CLOSES the single-turn synthetic/IFEval wave line (honest negative
BENCH-WAVE-PLAN.md-672-with the full autopsy chain already recorded); token-aware contrast or
BENCH-WAVE-PLAN.md-673-GRPO training would be a separately authorized program. The x0.25
BENCH-WAVE-PLAN.md-674-static dose is carried as a descriptive comparator only.
BENCH-WAVE-PLAN.md-675-
BENCH-WAVE-PLAN.md-676-### v4.5 addendum — registered ablation + a disclosure (Brian approved,
BENCH-WAVE-PLAN.md-677-2026-08-31)
BENCH-WAVE-PLAN.md-678-
BENCH-WAVE-PLAN.md-679-- LEARNED-vs-HEURISTIC ADDRESSING ABLATION (registered BEFORE the
BENCH-WAVE-PLAN.md-680-  confirmation runs; executed AFTER confirmation, outside the gate,
BENCH-WAVE-PLAN.md:681:  descriptive): rerun the confirmation block with the SAME deficit
BENCH-WAVE-PLAN.md-682-  trigger and selected (tau, b_max) but span selection replaced by the
BENCH-WAVE-PLAN.md-683-  FIRST Constraint: sentence heuristic (no learned q/k). Claim rules:
BENCH-WAVE-PLAN.md-684-  if learned addressing beats the heuristic (paired), the wave's
BENCH-WAVE-PLAN.md-685-  learned WHERE earns its keep on this task; if not, the single-turn
BENCH-WAVE-PLAN.md-686-  claim is scoped to "SpotLight-class control law", and the wave's
BENCH-WAVE-PLAN.md-687-  distinctive contribution remains the out-of-reach regime (W3) +
BENCH-WAVE-PLAN.md-688-  focus readout/transplant results. Not a gate; no stop-loss impact.
BENCH-WAVE-PLAN.md-689-- DISCLOSURE: the calibration runner's interventions_per_token logs
BENCH-WAVE-PLAN.md-690-  span-SELECTION opportunities (always 1.0 when spans exist), not
BENCH-WAVE-PLAN.md-691-  actual per-head bias firings (those live inside the attention
BENCH-WAVE-PLAN.md-692-  blocks). The registered tie-break (lower intervention rate) is
BENCH-WAVE-PLAN.md-693-  therefore effective only via a post-hoc replay if an exact adherence
BENCH-WAVE-PLAN.md-694-  tie occurs; otherwise selection is by adherence alone. Recorded
BENCH-WAVE-PLAN.md-695-  before seeing full grid results.
BENCH-WAVE-PLAN.md-696-
BENCH-WAVE-PLAN.md:697:### v4.5 Multi-IF execution (Brian-directed, 2026-08-31; EXPLORATORY as
BENCH-WAVE-PLAN.md-698-registered): the long-horizon test runs REGARDLESS of the single-turn
BENCH-WAVE-PLAN.md-699-confirmation outcome — it is the scope-hypothesis test (instructions
BENCH-WAVE-PLAN.md-700-drift out of focus across turns; published models decay 88->71).
BENCH-WAVE-PLAN.md-701-Arms (closed table, controller bound to the committed v4.4 seed-0
BENCH-WAVE-PLAN.md-702-training record's selected_sha256 9d43315b...): base;
BENCH-WAVE-PLAN.md:703:deficit-wave-s0 (calibration-selected tau/b_max; candidate spans =
BENCH-WAVE-PLAN.md-704-each USER message's token span, learned q/k selects per step — the
BENCH-WAVE-PLAN.md-705-natural generalization when instructions are not phrase-marked);
BENCH-WAVE-PLAN.md-706-static25-wave-s0 (v4.4 bias x0.25, descriptive comparator). All 909
BENCH-WAVE-PLAN.md-707-conversations x 3 turns; per-turn-index + pooled metrics; no gate.
BENCH-WAVE-PLAN.md-708-Ordering: after the single-turn confirmation (+ replication if it
BENCH-WAVE-PLAN.md-709-passes) releases the GPU.

exec
/bin/bash -lc "rg --files | rg 'EVF|evf|e0|research-wave|b3-deficit|multiif' && sed -n '1,280p' EVF-PLAN.md 2>/dev/null || true && sed -n '1,260p' results/qwen/e0-pilot.json && sed -n '1,320p' scripts/e0_pilot.py" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
EVF-PLAN.md
archive/plan/retros/phase0.md
src/stencil/evf.py
data/bench/multiif_en.jsonl
archive/plan/reviews/retro-phase0/topics.txt
archive/plan/reviews/retro-phase0/retro-kimi.md
archive/plan/reviews/phase0/phase0.md
archive/plan/reviews/phase0/topics.txt
archive/plan/reviews/phase0/artifacts.txt
archive/plan/reviews/phase0/phase0-kimi.md
results/research-wave-generation.md
scripts/b4_multiif.py
results/research-wave-prior-art.md
tests/test_evf_pilot.py
archive/codex-agents/phase0-fixes.allow
archive/codex-agents/phase0-scaffold.md
archive/codex-agents/phase0-scaffold.allow
archive/codex-agents/phase0-fixes.md
scripts/e0_pilot.py
# EVF — Predictive Reactivation / Expected Value of Focus (the WHEN program)

Authorized by Brian 2026-08-31 ("kill what is currently running and run
this new program instead — red/green TDD, deterministic proof it's
implemented correctly"), superseding the v4.5 confirmation mid-run (its
partial records are retained untouched under results/qwen/
b3-deficit-conf-s0/; the seed-0 sealed attempt is recorded ABANDONED-
BY-RULING, not failed). Design: sol xhigh spec, results/
b3-when-design-sol.md. BENCH-WAVE-PLAN.md machinery (data freezes,
verifier vendoring, stats) is inherited; the single-turn stop-loss is
superseded by this authorization.

## The isolated bottleneck (established)

Amplitude solved (2x force = 0 extra repairs). WHERE solved (K-perm
kills the benefit). WHEN is open: the psi<tau attention trigger makes
12 bad calls per 15 good; oracle WHEN ceiling +7.5pts vs +1.5 harvested.

## Phase E0 — the decisive pilot probe (kill-fast; THIS phase only is
authorized to run before its gate reports)

Data: the recorded calibration discordants (t30-b3 vs base, 15 repairs
+ 12 regressions) + concordant controls, from
results/qwen/b3-deficit-cal/ per-item records. No new generation on any
frozen evaluation stream; teacher-forced feature passes only.

Per discordant row:
1. Find the FIRST divergence token between the base and wave responses
   (shared prefix p; the WHEN decision that mattered happened there).
2. Teacher-force prompt+shared-prefix through the trunk once; cache at
   the divergence point (and at 2 matched control points in concordant
   rows): h20; decoder entropy, top-1 margin and their deltas over the
   last 5 tokens; the frozen wave's rule-readout features (per-span q/k
   scores: max, margin between top-2 spans); natural attention-mass
   summary on the governing span (layers 20-27 mean).
3. One additional weak-focus forward (the selected t30-b3 field scaled
   to b=1.0 on the governing span) at the same prefix; cache
   KL(P1||P0), JS divergence, and the obligation-token probability
   shift (mean delta log-prob of the row's obligation-span tokens).
4. Labels: repair=1, regression=0 (verifier-derived, offline).

Probe: L2-regularized logistic regression (deterministic solver, fixed
seed), leave-one-topic-out AND leave-one-constraint-family-out folds.

GATE E0 (registered): held-out repair recall r+ >= 0.60 with
regression fire-rate r- <= 0.25 on the 15/12 anatomy, in BOTH fold
schemes. KILL immediately if: focused-vs-native divergence features are
indistinguishable between repairs and regressions AND obligation/
readout features add no held-out discrimination; or performance
disappears under family holdout; or the probe works only via constraint
type or response position.

## Phase E1 (only if E0 passes; separate go)

Recurrent obligation tracker (GRU 128/rule) + two-stage firing
(eligibility screen -> one-token counterfactual -> calibrated
lower-confidence-bound EVF > 0), bursts <= 4 tokens + refractory;
labels from offline verifier-scored counterfactual rollouts; safe-dose
interval requirement (a BROAD non-harmful tau/threshold plateau, not
one winning scalar) and behavioral gates per sol's spec sections
(offline discrimination, safe-dose, behavioral) — registered in full
before any E1 training run.

## Process

Red/green TDD throughout: every component gets a failing test first;
deterministic proof = bitwise-identical feature extraction across two
runs, fixed-seed probe fits, and fixture-exact tests for divergence
finding and label derivation. Reviews: sol + fable on the E0 result
before any E1 work. Playbook governs (per-item records from the first
row of anything evaluative; git add -f for results; smoke before
sealing).
{
 "items": [
  {
   "i": 0,
   "label": 1,
   "topic": "patching a canvas sail",
   "family": "keywords",
   "features": {
    "entropy": 1.2485344409942627,
    "margin": 0.36050519347190857,
    "entropy_delta5": 1.2485344384851118,
    "margin_delta5": -0.6394948065280914,
    "readout_top": 0.16809625923633575,
    "readout_margin": 0.0427558571100235,
    "attn_mass_span": 0.007260476821102202,
    "kl_focus": 0.001816573552787304,
    "js_focus": 0.00045197433792054653,
    "obligation_shift": 0.018623456358909607,
    "rel_pos": 0.1794871794871795
   }
  },
  {
   "i": 28,
   "label": 1,
   "topic": "labeling jars of preserves",
   "family": "keywords",
   "features": {
    "entropy": 1.2948119640350342,
    "margin": 0.4854567050933838,
    "entropy_delta5": 1.2948118858686755,
    "margin_delta5": -0.5145432949066162,
    "readout_top": 0.6657071709632874,
    "readout_margin": 0.05605161190032959,
    "attn_mass_span": 0.05239408265333623,
    "kl_focus": 0.014803757891058922,
    "js_focus": 0.003740101237781346,
    "obligation_shift": -0.1819230020046234,
    "rel_pos": 0.4074074074074074
   }
  },
  {
   "i": 34,
   "label": 1,
   "topic": "restoring a wooden rowboat",
   "family": "change_case",
   "features": {
    "entropy": 3.243776321411133,
    "margin": 0.02128380537033081,
    "entropy_delta5": 3.2123059518635273,
    "margin_delta5": -0.9694212079048157,
    "readout_top": 0.5301398038864136,
    "readout_margin": 0.033826619386672974,
    "attn_mass_span": 0.011292336945189163,
    "kl_focus": 0.007412062957882881,
    "js_focus": 0.001854974776506424,
    "obligation_shift": -0.04203889146447182,
    "rel_pos": 0.5151515151515151
   }
  },
  {
   "i": 37,
   "label": 0,
   "topic": "drying herbs in an attic",
   "family": "keywords",
   "features": {
    "entropy": 0.8005515336990356,
    "margin": 0.37918999791145325,
    "entropy_delta5": 0.800551448905928,
    "margin_delta5": -0.6208100020885468,
    "readout_top": 0.5448447465896606,
    "readout_margin": 0.052181899547576904,
    "attn_mass_span": 0.004962845705449581,
    "kl_focus": 3.0196890293154866e-05,
    "js_focus": 7.558479410363361e-06,
    "obligation_shift": -0.12714827060699463,
    "rel_pos": 0.30434782608695654
   }
  },
  {
   "i": 44,
   "label": 1,
   "topic": "rebinding worn atlases",
   "family": "format",
   "features": {
    "entropy": 0.6979253888130188,
    "margin": 0.6484847068786621,
    "entropy_delta5": 0.6978925734547374,
    "margin_delta5": -0.3515111207962036,
    "readout_top": 0.7836577892303467,
    "readout_margin": 0.10296869277954102,
    "attn_mass_span": 0.07065950729884207,
    "kl_focus": 1.2927755117416382,
    "js_focus": 0.1905326172709465,
    "obligation_shift": 1.0506983995437622,
    "rel_pos": 0.058823529411764705
   }
  },
  {
   "i": 46,
   "label": 1,
   "topic": "the rhythm of a night ferry crossing",
   "family": "keywords",
   "features": {
    "entropy": 1.486790418624878,
    "margin": 0.2343515306711197,
    "entropy_delta5": 1.4521914720535278,
    "margin_delta5": -0.7588701099157333,
    "readout_top": 0.5104531645774841,
    "readout_margin": 0.062246501445770264,
    "attn_mass_span": 0.014184350264258683,
    "kl_focus": 0.07678866386413574,
    "js_focus": 0.019054491072893143,
    "obligation_shift": 0.03701985999941826,
    "rel_pos": 0.15789473684210525
   }
  },
  {
   "i": 50,
   "label": 0,
   "topic": "arranging a type case for a letterpress",
   "family": "format",
   "features": {
    "entropy": 0.9677954316139221,
    "margin": 0.2633815407752991,
    "entropy_delta5": -0.42901426553726196,
    "margin_delta5": 0.22597035765647888,
    "readout_top": 0.446548730134964,
    "readout_margin": 0.1069236695766449,
    "attn_mass_span": 0.0074166056292597204,
    "kl_focus": 0.0003904564364347607,
    "js_focus": 9.74904432951007e-05,
    "obligation_shift": 0.04638385772705078,
    "rel_pos": 0.15789473684210525
   }
  },
  {
   "i": 70,
   "label": 1,
   "topic": "cataloguing river pebbles",
   "family": "content",
   "features": {
    "entropy": 2.1749300956726074,
    "margin": 0.24705344438552856,
    "entropy_delta5": 2.1527401246130466,
    "margin_delta5": -0.7487592101097107,
    "readout_top": 0.5843257308006287,
    "readout_margin": 0.5843257308006287,
    "attn_mass_span": 0.03548607253469527,
    "kl_focus": 0.04080497473478317,
    "js_focus": 0.009341433178633451,
    "obligation_shift": 0.5466693639755249,
    "rel_pos": 0.4074074074074074
   }
  },
  {
   "i": 71,
   "label": 0,
   "topic": "pressing apples for cider",
   "family": "keywords",
   "features": {
    "entropy": 1.0307284593582153,
    "margin": 0.2284962236881256,
    "entropy_delta5": 0.7959445416927338,
    "margin_delta5": -0.6459347307682037,
    "readout_top": 0.7177331447601318,
    "readout_margin": 0.056943655014038086,
    "attn_mass_span": 0.0037290647451300174,
    "kl_focus": 0.000846214359626174,
    "js_focus": 0.00021063076565042138,
    "obligation_shift": -0.044465139508247375,
    "rel_pos": 0.3333333333333333
   }
  },
  {
   "i": 74,
   "label": 0,
   "topic": "sorting a municipal seed archive",
   "family": "keywords",
   "features": {
    "entropy": 1.2104192972183228,
    "margin": 0.06223660707473755,
    "entropy_delta5": 1.1187999844551086,
    "margin_delta5": -0.9166919589042664,
    "readout_top": 0.8285130262374878,
    "readout_margin": 0.127205491065979,
    "attn_mass_span": 0.0013366543498705141,
    "kl_focus": 0.0002655338030308485,
    "js_focus": 6.639663479290903e-05,
    "obligation_shift": -0.007652082946151495,
    "rel_pos": 0.6049382716049383
   }
  },
  {
   "i": 89,
   "label": 1,
   "topic": "sorting a municipal seed archive",
   "family": "change_case",
   "features": {
    "entropy": 0.5427402257919312,
    "margin": 0.5400509834289551,
    "entropy_delta5": 0.542575881787343,
    "margin_delta5": -0.4599291682243347,
    "readout_top": 0.5758206844329834,
    "readout_margin": 0.12552574276924133,
    "attn_mass_span": 0.01962585054570809,
    "kl_focus": 0.00331951305270195,
    "js_focus": 0.0008452814072370529,
    "obligation_shift": -0.015664726495742798,
    "rel_pos": 0.38461538461538464
   }
  },
  {
   "i": 90,
   "label": 0,
   "topic": "maintaining a community greenhouse",
   "family": "length",
   "features": {
    "entropy": 2.1645631790161133,
    "margin": 0.08932963013648987,
    "entropy_delta5": 0.7407457828521729,
    "margin_delta5": -0.11343465745449066,
    "readout_top": 0.7537433505058289,
    "readout_margin": 0.180411696434021,
    "attn_mass_span": 0.003814537965808995,
    "kl_focus": 0.0028844373300671577,
    "js_focus": 0.0007198166567832232,
    "obligation_shift": -0.03049209713935852,
    "rel_pos": 0.3191489361702128
   }
  },
  {
   "i": 94,
   "label": 0,
   "topic": "the layout of a village bakery",
   "family": "length",
   "features": {
    "entropy": 2.4158265590667725,
    "margin": 0.00110664963722229,
    "entropy_delta5": 1.8759625554084778,
    "margin_delta5": -0.8281809389591217,
    "readout_top": 0.6207755208015442,
    "readout_margin": 0.007736027240753174,
    "attn_mass_span": 0.014469106681644917,
    "kl_focus": 0.007216235622763634,
    "js_focus": 0.0017971768975257874,
    "obligation_shift": 0.01975833810865879,
    "rel_pos": 0.49206349206349204
   }
  },
  {
   "i": 96,
   "label": 0,
   "topic": "storing winter firewood",
   "family": "keywords",
   "features": {
    "entropy": 0.8695182800292969,
    "margin": 0.6476801633834839,
    "entropy_delta5": 0.5493115186691284,
    "margin_delta5": -0.25455689430236816,
    "readout_top": 0.7571457028388977,
# ruff: noqa
"""EVF Phase E0 — the registered kill-fast pilot (EVF-PLAN.md).
Extracts the registered feature set at each discordant divergence point
(15 repairs / 12 regressions from the t30-b3 calibration anatomy),
fits the deterministic logistic probe, and evaluates the REGISTERED
GATE under BOTH fold schemes: leave-one-TOPIC-out and leave-one-
FAMILY-out (family = first-listed constraint's family; disclosed).
GATE: r+ >= 0.60 AND r- <= 0.25 in BOTH schemes. Per-item features
saved (playbook)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
from stencil.evf import extract_features, gate_eval, load_anatomy, load_model

FAMILY = {"caps": "change_case", "lower": "change_case", "kw_exist": "keywords",
          "kw_freq": "keywords", "kw_forbid": "keywords", "n_words_min": "length",
          "n_words_max": "length", "n_sent": "length", "bullets": "format",
          "title": "format", "json_fmt": "format", "placeholders": "content",
          "postscript": "content", "two_resp": "combination"}

m, tok, ctrl = load_model(ROOT)
anat = load_anatomy(ROOT, arm="t30-b3")
feats, labels, topics, families, items = [], [], [], [], []
for it in anat:
    f = extract_features(m, tok, ctrl, it)
    feats.append(f); labels.append(it["label"])
    topics.append(it["row"]["topic"])
    families.append(FAMILY[it["row"]["combo"][0]])
    items.append({"i": it["i"], "label": it["label"], "topic": it["row"]["topic"],
                  "family": FAMILY[it["row"]["combo"][0]], "features": f})
    print(f"{it['i']}: label {it['label']} kl {f['kl_focus']:.4f} ob {f['obligation_shift']:.4f}", flush=True)

res_topic = gate_eval(feats, labels, topics)
res_family = gate_eval(feats, labels, families)
gate = {"topic_folds": res_topic, "family_folds": res_family,
        "PASS": bool(res_topic["r_plus"] >= 0.60 and res_topic["r_minus"] <= 0.25
                     and res_family["r_plus"] >= 0.60 and res_family["r_minus"] <= 0.25)}
out = {"items": items, "gate": gate}
(ROOT / "results" / "qwen" / "e0-pilot.json").write_text(json.dumps(out, indent=1))
print(json.dumps(gate, indent=1))

exec
/bin/bash -lc "find results/qwen -maxdepth 3 -type f \\( -path '*multiif*' -o -path '*e0*' \\) -printf '%p %s bytes\\n' | sort && find results/logs -maxdepth 2 -type f -iname '*multi*' -printf '%p %s bytes\\n' | sort && git status --short && git log -8 --oneline --decorate" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
results/qwen/b4-multiif-base/conv-000.json 6268 bytes
results/qwen/b4-multiif-base/meta.json 1008 bytes
results/qwen/e0-pilot.json 15508 bytes
results/qwen/t1-trace0-features.pt 17529667 bytes
results/logs/b4-multiif.log 72 bytes
df3eb02 (HEAD -> main, origin/main, origin/HEAD) EVF(E0): pilot gate FAIL — family-holdout kill criterion; dual review convening
f1fb1ab EVF(E0): red/green — divergence finder, anatomy loader, bitwise-deterministic feature extraction (attn_probe added to trunk), deterministic probe+gate (5/5)
ff379e6 EVF program authorized (Brian): confirmation abandoned by ruling; E0 pilot registered with kill-fast gate
017c07a bench: sol xhigh WHEN-design — Predictive Reactivation / Expected-Value-of-Focus gate spec
bd4188d bench(v4.5): calibration complete — selected t30-b3 (0.870 vs base 0.855); v4.4 seed-1 controller committed
c16d62e worklog: Brian's ruling — Multi-IF decisive, decisions follow its data
62171cf bench: sol xhigh evaluation + deep research (actuator alternatives, obligation trackers, constrained-decoding ceiling, ranked resolutions)
bd86560 bench: Multi-IF v4.5 execution registered (Brian) — deficit policy with user-turn spans, static-x0.25 comparator, runs regardless of confirmation outcome

codex
The key quantitative point is already emerging: 270 discordants would be enough for a locked, low-dimensional replication, but not automatically for an 11-feature model-selection exercise. I’m checking that against prediction-model sample-size work and the conflict-monitoring literature, while treating the current one-conversation Multi-IF output as no result—not an interim signal.
web search: 
web search: site:bmj.com sample size prediction model binary outcome Riley events per parameter shrinkage 2019 ...
exec
/bin/bash -lc "sed -n '1,360p' results/b3-when-design-sol.md 2>/dev/null || sed -n '1,360p' results/qwen/b3-when-design-sol.md 2>/dev/null || true; tail -n 180 WORKLOG.md; cat results/logs/b4-multiif.log; if [ -f results/qwen/b4-multiif-base/conv-000.json ]; then sed -n '1,260p' results/qwen/b4-multiif-base/conv-000.json; fi" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
OpenAI Codex v0.147.0
--------
workdir: /home/bmarti44/stencil-llm
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a04889-69ae-7751-b3f2-de2e74e382e4
--------
user
DESIGN QUESTION FROM BRIAN (xhigh, web search enabled — use academic sources deeply): HOW DO WE ACCURATELY DETERMINE WHEN TO APPLY FOCUS — Miller-faithful, and fully AUTOMATIC (no human intervention, no oracle labels at inference, no task-specific wiring)? Context you know: the WHEN problem is now isolated as THE bottleneck (amplitude solved: 2x force = 0 extra repairs; WHERE solved: K-perm kills the benefit; the psi<tau attention trigger makes 12 bad calls per 15 good — a symptom-based trigger, not a diagnosis; oracle WHEN ceiling +7.5 vs +1.5 harvested). Brian's framing: 'the problem is not how much focus, the problem is WHEN to focus.' Your task, three parts: (1) MILLER-FAITHFUL MECHANISMS: go back to the neuroscience — in Miller's framework (beta/gamma interplay, top-down beta carrying task rules gating bottom-up gamma; working-memory reactivation timing), what precisely determines WHEN a rule is re-asserted? Map each candidate neural timing mechanism to an implementable analog on a frozen transformer with a tiny controller: e.g. conflict/error signals (ACC analog: rising next-token entropy or divergence between the model's committed trajectory and the rule's demands), phase-like periodic refresh (is there any defensible analog of oscillatory duty cycles in autoregressive steps?), content-addressable reactivation (the rule reasserts when the current state RESEMBLES contexts where the rule was learned to matter). Which is most faithful AND most implementable? (2) AUTOMATIC WHEN-SIGNALS available at inference with zero human input, ranked by expected precision: decoder entropy/margin trajectories; KL between the model's next-token distribution and a rule-conditioned counterfactual (two-forward probe); the model's own uncertainty about the governing instruction (readout head on h20 — we already proved focus is linearly readable, W2 100% non-NULL accuracy); verifier-free obligation-state estimation (a tiny recurrent state tracking which obligations look satisfied from the generated text so far — learnable from our verified data with per-obligation labels we can compute offline); attention-mass trends (the failed one — why exactly does it underperform, and does its failure predict which alternatives will work?). For each: what would the gate's precision/recall on our 15-repair/12-regression anatomy plausibly be, what does the literature say (cite), and what is the cheapest decisive pilot on our existing recorded data (we have every response, per-item, both arms, plus minimal-violation mutation pairs)? (3) THE SYNTHESIS: propose ONE concrete Miller-faithful automatic WHEN architecture for the wave (controller stays tiny, trunk frozen, deterministic verification culture) with a registered-quality spec sketch: inputs, training labels (computable offline from our data — no human annotation), firing rule, safe-dose interval requirement, and the pilot that would falsify it fastest. Be blunt about what is genuinely automatic vs what smuggles in an oracle.
codex
I’ll separate biological fidelity from engineering usefulness. The key test is whether a signal predicts the *counterfactual value of intervention*—repair versus regression—not merely correlates with low attention or uncertainty. I’m tracing Miller’s actual control loop first, then I’ll map inference-time signals onto the recorded 15/12 discordant anatomy and design one falsifiable gate.
web search: 
web search: Earl Miller beta gamma working memory top down beta task rules gamma bursts reactivation review primary paper ...
web search: 
web search: anterior cingulate cortex conflict monitoring error likelihood cognitive control Botvinick primary paper PMC ...
web search: 
web search: language model uncertainty entropy margin predicts errors selective generation primary paper semantic entropy Nature 2024 ...
web search: 
web search: language model intervention gate counterfactual KL divergence conditioned unconditioned instruction adherence decoding primary paper ...
web search: 
web search: 'readout'
web search: 
web search: working memory retrocue reactivation gamma beta prioritized item primary study Miller lab ...
web search: 
web search: site:aclanthology.org obligation tracking generated text constraints satisfied recurrent state neural decoder ...
web search: 
web search: Miller Cohen 2001 integrative theory prefrontal cortex cognitive control task rules guided activation pdf ...
codex
## Bottom line

The most Miller-faithful automatic answer is not “focus whenever attention is low” and not “refresh every \(N\) tokens.” It is:

> Reactivate a rule when the current processing state predicts that the rule is relevant, insufficiently expressed, and that a short reactivation has positive expected value.

In implementation terms, this means a tiny learned **Expected Value of Focus** gate combining:

1. content-addressed relevance: which stored rule matches the current processing state;
2. obligation state: is that rule still pending, threatened, or nearing its last safe execution point;
3. a counterfactual probe: does a weak focused forward change the trajectory in a direction predicted to help;
4. intervention cost: how much does it disturb the model’s native distribution?

That is closer to Miller’s control account than any single observable such as entropy, attention mass, or a clock.

## 1. What actually determines WHEN in Miller’s framework

### The neuroscience does not contain a periodic refresh clock

Miller and Cohen’s foundational account says that PFC representations of goals and task rules provide bias signals that guide processing along currently relevant pathways. Context and internal state activate the appropriate “rulemap”; the rule representation then biases competition elsewhere. [Miller & Cohen, 2001](https://www.annualreviews.org/content/journals/10.1146/annurev.neuro.24.1.167), [Miller’s rulemap account](https://pmc.ncbi.nlm.nih.gov/articles/PMC3898679/)

The later beta/gamma account adds temporal structure:

- Deep-layer alpha/beta carries top-down and inhibitory control.
- Superficial gamma is associated with expression, encoding, or readout of working-memory content.
- Beta protects or suppresses; gamma bursts briefly express selected content.
- When content is about to be needed, beta falls and content-specific gamma/spiking rises.
- When it is no longer needed, beta rises and gamma/content expression falls. [Working Memory 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC8112390/)

Critically, the bursts are not a metronome. Single-trial gamma bursts were irregular; apparent slow periodicity emerged after averaging. [Gamma and beta bursts underlie working memory](https://pmc.ncbi.nlm.nih.gov/articles/PMC5220584/)

The strongest empirical answer to WHEN is therefore **anticipation of use**. In Miller’s sequence task, the relevant object’s gamma and informative spiking increased before the expected test object, with reduced beta; this occurred only before relevant tests. [Gamma and beta bursts during working-memory readout](https://pubmed.ncbi.nlm.nih.gov/29374153/)

So the biologically defensible mapping is:

| Neural idea | Transformer analog | Verdict |
|---|---|---|
| Learned context predicts impending need | Current hidden state retrieves a rule-use prototype | Most Miller-faithful |
| ACC-like conflict or expected control value | Predict intervention utility from native/focused counterfactuals | Best automatic firing decision |
| Beta hold / gamma burst | Default no-focus state plus short, gated focus burst | Faithful actuator schedule |
| Periodic replay | Refractory/eligibility schedule, never the decision itself | Supporting mechanism only |
| Low attention mass | “Rule is visually quiet” | Symptom, not diagnosis |

### Conflict monitoring complements Miller

The ACC conflict-monitoring account proposes that incompatible response tendencies signal a need for more top-down control. The Expected Value of Control formulation goes further: choose the identity and intensity of control by predicted benefit minus its cost. [Conflict monitoring and cognitive control](https://pubmed.ncbi.nlm.nih.gov/11488380/), [Expected Value of Control](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

That is almost exactly your measured problem:

\[
\operatorname{EVF}(s,r)=
\mathbb{E}[\text{utility with focus}-\text{utility without focus}\mid s,r]
-\operatorname{cost}(\text{focus}).
\]

The current `ψ<τ` trigger estimates neither term. It estimates only whether a span received little native attention.

### Content-addressable reactivation is the best biological/engineering bridge

In the rulemap account, external and internal context cues complete the relevant rule representation. Activity-silent working-memory research likewise finds that latent contents can be reactivated by appropriate cues or “pings.” [Activity-silent working memory review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10158524/)

For Stencil:

- Each rule/memory has a learned key \(k_m\).
- Current `h20` produces a query \(q_t\).
- Similarity retrieves the likely relevant rule.
- A separate utility gate decides whether retrieving it into active processing is worth doing now.

This separates WHERE from WHEN correctly. Similarity selects the candidate; it must not itself authorize intervention. The PRESS program already demonstrated why: lookalike contexts can retrieve the right type without establishing that the rule is live.

### Where an oscillator still fits

An oscillator could provide:

- a refractory period after a burst;
- time-division multiplexing among several memories;
- an eligibility window for probing dormant rules;
- a weak “do not let this rule go unexamined forever” prior.

It should not directly command a press. Fixed token-period refresh is less Miller-faithful than a predictive gate and would replay the same false-positive problem periodically.

## 2. Automatic inference-time signals

First, precision and recall cannot be identified completely from the 15/12 anatomy. Among outcome-changing calls, the present gate’s conditional positive predictive value is:

\[
15/(15+12)=55.6\%.
\]

That omits all fired-but-no-effect calls, so the true per-fire precision is lower. Recall is unknown because we do not know how many helpful opportunities the policy failed to activate.

For any proposed gate, let:

- \(r_+\): fraction of the 15 helpful interventions retained;
- \(r_-\): fraction of the 12 harmful interventions retained.

Then:

\[
\mathrm{PPV}=\frac{15r_+}{15r_+ + 12r_-},\qquad
\mathrm{net}=15r_+-12r_-.
\]

The present net is \(+3\). A useful pilot target is approximately \(r_+\ge .60,\ r_-\le .25\): nine repairs, three regressions, PPV 75%, net \(+6\).

The ranges below are design priors, not measured claims.

### 1. Obligation-state estimate plus counterfactual utility

Expected performance: highest precision; target 75–85% PPV at 55–75% recall.

Maintain a learned state per selected rule:

- inactive/not applicable;
- pending;
- partially satisfied;
- satisfied;
- threatened or nearly impossible;
- remaining response-budget fraction.

The tracker consumes the natural-language rule representation, `h20`, and the generated prefix. It does not call a verifier at inference.

This attacks the actual distinction between your repairs and regressions. A keyword rule that has already been satisfied does not need focus even if prompt attention is low. A required placeholder still absent near the response boundary does.

Mention Flags established the basic idea of updating per-constraint states as generation proceeds, although its mechanism uses explicit lexical matching and is narrower than the required learned tracker. [Mention Flags](https://aclanthology.org/2021.acl-long.9/) NeuroLogic similarly tracks partially satisfied logical constraints, but as an explicit decoding algorithm. [NeuroLogic](https://aclanthology.org/2021.naacl-main.339/)

Cheap pilot:

1. Use your checkers to produce per-prefix pending/satisfied labels offline.
2. Include canonical, base, wave, and minimal-violation prefixes.
3. Train a 64–128-dimensional GRU using rule text plus prefix `h20`.
4. Hold out whole constraint families, not rows.
5. Evaluate whether its pending/urgency score separates the 15 repairs from 12 regressions.

If it cannot generalize state across held-out families, it is a learned IFEval checker, not a general focus controller.

### 2. Signed rule-conditioned counterfactual

Expected performance:

- KL alone: high recall, only roughly 55–65% PPV.
- KL plus predicted progress: plausible 70–85% PPV.

At a candidate moment compute:

- \(P_0\): ordinary next-token distribution;
- \(P_1\): weak, safe-dose focused distribution.

Then measure:

- symmetric KL or Jensen–Shannon divergence;
- top-\(k\) overlap;
- change in probability assigned to tracker-predicted progress;
- native-distribution cost;
- whether the focused distribution sharpens or destabilizes.

The important correction is that **large KL is not a reason to focus**. It says the actuator has leverage. The 15 repairs and 12 regressions are both likely high-leverage events. The gate needs a signed value estimate:

\[
\widehat{\Delta U}_t
=
\widehat V(P_1,s_t,r)-\widehat V(P_0,s_t,r)
-\lambda D_{\mathrm{JS}}(P_1,P_0).
\]

This is an inference-time intervention experiment, not an oracle: both forwards are produced automatically by the same frozen model. The oracle enters only if an inference-time checker or future ground truth is consulted.

Cheap pilot:

- Teacher-force the stored base prefixes through normal and weak-focus forwards.
- Cache \(P_0,P_1\) at the first divergence and obligation-sensitive positions.
- Test KL alone, signed tracker progress, and their combination against helpful/harmful labels.
- Use leave-topic and leave-constraint-family-out folds.

If KL is equally high on repairs and regressions, that is expected. If the signed tracker delta also cannot separate them, kill the architecture.

### 3. Uncertainty of the governing-rule readout

Expected on B3: potentially high precision when it fires, but probably under 30% recall.

You already proved the focused rule is linearly readable with 100% non-NULL accuracy. That makes a readout-margin gate attractive but also predicts a likely null result here: the model generally knows which rule exists. The problem is applying it at the right generative moment.

Useful features are:

- margin between the selected rule and runner-up;
- entropy over rule identities;
- change in margin over recent tokens;
- inconsistency between current readout and the recurrent rule state.

This should become much more useful on Multi-IF or compaction streams, where the governing rule may genuinely fade or compete with stale rules.

CAST shows that hidden-state patterns can condition whether activation steering is applied, although its prompt-category refusal task is much easier than token-level obligation timing. [Conditional Activation Steering](https://arxiv.org/abs/2409.05907)

Cheap pilot: replay stored prefixes, record W2 logits by token, and compare pre-divergence margin trajectories for repairs versus regressions. If both remain confidently correct, rule-readout uncertainty cannot solve B3 and should be retained only for long-horizon use.

### 4. Decoder entropy and margin trajectories

Expected: 50–60% PPV and 40–70% recall alone.

Raw entropy is task-general and free. It is also nonspecific:

- Fluent wording choices can have high entropy but pose no rule risk.
- A model can confidently omit a keyword.
- Entropy rises at punctuation, enumeration, and ordinary branch points.
- Low top-1 margin indicates competing tokens, not necessarily conflict with a rule.

Use temporal surprise rather than absolute entropy:

\[
z_t = \frac{H_t-\operatorname{median}(H_{t-w:t-1})}
{\operatorname{MAD}(H_{t-w:t-1})+\epsilon}.
\]

Also useful:

- top-1/top-2 margin collapse;
- entropy acceleration;
- disagreement among a few deterministic perturbed forwards;
- entropy localized to tracker-predicted obligation boundaries.

Semantic entropy can detect some confabulations and support selective abstention, but it targets uncertainty over answer meaning rather than instruction compliance. [Semantic entropy](https://www.nature.com/articles/s41586-024-07421-0)

More relevant is Attribution-Guided Decoding: its adaptive variant uses entropy to decide when guidance is warranted and reports Llama-3.1 instruction success improving from 66.0% to 79.1%. But entropy is used as a coarse economizer around a rule-specific attribution mechanism, not as a complete diagnosis. [Attribution-Guided Decoding](https://proceedings.iclr.cc/paper_files/paper/2026/hash/da30215ee52c1daaaaddada8137cfd0b-Abstract-Conference.html)

Cheap pilot: teacher-force every stored response, extract entropy/margin windows before the first helpful or harmful divergence, and fit only a three-feature logistic baseline. This is the baseline every richer gate must beat.

### 5. Attention-mass level or trend

Measured conditional PPV: 55.6% among outcome-changing calls; true per-fire PPV lower.

It failed because attention mass answers the wrong question:

> “How much is this head currently reading this span?”

The desired question is:

> “Would forcing this head to read the span improve expected task utility now?”

Low mass has many benign explanations:

- the head is irrelevant to instruction transport;
- the rule has already been integrated into the residual stream;
- a different layer/head read it earlier;
- the obligation is satisfied;
- the current token needs local response context;
- the rule matters later, not now.

A falling trend may be marginally better than a fixed threshold, but it remains unsigned. Worse, your dose experiment shows that more intervention creates no additional repairs: the limitation is not failure to detect sufficiently low attention.

What its failure predicts: raw entropy, readout uncertainty, or context similarity will also fail if treated as sufficient conditions. Each is a symptom. A successful gate must estimate **counterfactual benefit** or at least combine relevance with pending obligation state.

## 3. One concrete architecture

I recommend a **Predictive Reactivation / Expected Value of Focus gate**.

### State

For each autonomously identified rule span \(m\):

- `key_m`: existing learned address key;
- `rule_m`: pooled rule representation;
- `z_m ∈ R^128`: recurrent obligation/progress state;
- `age_m`: tokens since last reactivation;
- `burst_m`: current burst/refractory state.

No type ID, checker state, or generator metadata is available at inference.

### Inputs per generation step

Cheap path, every token:

- current `h20`;
- decoder entropy, top-1 margin, and their recent deltas;
- learned rule-readout logits and margin;
- selected rule key similarity;
- natural attention-mass summaries, retained only as features;
- per-rule recurrent state;
- normalized response length and remaining model budget.

The controller updates:

\[
z_{m,t}=\operatorname{GRU}(z_{m,t-1},
[h^{20}_t,\operatorname{rule}_m,\operatorname{embed}(y_t)]).
\]

It predicts:

- \(p_{\text{pending}}\);
- \(p_{\text{relevant-now}}\);
- \(p_{\text{already-satisfied}}\);
- urgency/last-safe-opportunity;
- probability that a focus burst will help or harm.

### Two-stage firing

Stage 1: cheap eligibility screen.

Probe only when:

\[
p_{\text{pending}}\,
p_{\text{relevant-now}}\,
p_{\text{need}}
>\theta_{\text{probe}}.
\]

Stage 2: automatic counterfactual.

Compute the weak focused forward \(P_1\), compare with native \(P_0\), and estimate:

\[
\widehat{\mathrm{EVF}} =
p_{\text{pending}}
\left[
\widehat V(P_1,z_m)-\widehat V(P_0,z_m)
\right]
-\lambda D_{\mathrm{JS}}(P_1,P_0)
-c_{\text{compute}}.
\]

Fire only if a calibrated lower confidence bound on EVF is positive. If it fires, use the already-computed \(P_1\); otherwise use \(P_0\).

A burst lasts one token by default and can continue for a small registered maximum—say four tokens—only while EVF remains positive. Then enter a short refractory state. This gives irregular, task-cued bursts rather than continuous attention pressure.

### Neural mapping

- Stored rule and recurrent state: activity-silent/task-rule representation.

- base 75.66% vs wave-w0ce 74.37% (full 1319, 4-shot); discordants 80/63;
  Tango upper 2.80pt > 1.0pt margin -> NON_INFERIOR false. Zero timeouts,
  1 truncation per arm. Both B2 probes (MMLU 2.69pt bound, GSM8K 2.80pt bound)
  agree: w0-ce fires off-distribution and harms. B2 CLOSED as a recorded
  honest finding; the binding external-claim gate remains the B4-era rerun
  with the B3 wave.

## 2026-08-31 — IFBench verifiers vendored (fable subagent); B3 dev gate running

- vendor/ifbench @ github sha fcd289db (per-file provenance in PIN.json); 58/58
  class goldens green (175 tests incl. per-class random-state checks — verdicts
  are seed-independent, no per-row pin needed, unlike IFEval 1122/1129).
  Patches: relative imports, no import-time nltk downloads (stopwords +
  averaged_perceptron_tagger_eng added to vendor/nltk_data), absl->stdlib
  logging, emoji/syllapy vendored under _vendor_deps.
- Reading caveats recorded for IFBench scores: this is the maintained fork
  (carries post-paper bug fixes); words:start_verb POS-tags the raw first
  token, so common imperatives ("Run", "Remember") can be falsely failed —
  affects absolute scores, not paired comparisons.
- B3 dev-200 generation gate: base arm complete, adherence 0.8650 -> each
  wave seed needs >= 0.8850 (registered +2.0pt).

## 2026-08-31 — dev-gate FAIL diagnosed by dual failure-analysis; v4.2 amendment staged

- Official gate (partial): base 0.865, wave-s0 0.755 (-11pts); proxy arms
  finishing. 29 flips vs 7 fixes, concentrated on include-X constraints.
- FABLE (empirical, causal): my style-pull hypothesis REFUTED — wave outputs
  are as natural as base (NLL 0.302 vs 0.232 nats/tok; canonicals 5.73!) with
  ZERO filler leakage. Mechanism proven: gain saturated 2.0 on 100% of tokens;
  the bias halves attention over the model's own recent output in layers 20-27
  (recent-20 mass 0.15->0.09, 0.12->0.06, 0.13->0.07) -> lost running state:
  23/30 failures are NEAR-MISSES (3-of-4 placeholders, caps slips, count
  overshoot, repetition loops). Causal: inference gain x0.25 recovers 24/29
  flips — but only to base parity, never gate-passing (+2).
- SOL (analytical): ranked causes — (1) objective/teacher-forcing mismatch
  HIGH (CE on one canonical rewards imitation, not constraint execution;
  obligation tokens are rare and swamped by filler tokens), (2) saturated
  always-on field MEDIUM-HIGH, (3) word-salad canonicals as the training-time
  driver MEDIUM (5.7 nats/tok = unpredictable-from-context by construction ->
  "copy from prompt at max gain everywhere" is CE-optimal -> saturation).
  Deeper lesson recorded: sequence CE against ONE canonical is the wrong
  primary objective for open-generation constraint tasks.
- CONVERGED FIX (both reviewers): retrain on NATURAL canonicals (predictable
  from context, so gain must learn selective firing) + beta_max 1.0 at retrain.
  v4.2 candidate builder committed: topic-conditioned openers, varied natural
  pool, natural keyword-carrier sentences, word-cap trim; bullets x n_words_max
  retired (natural sentences too long). tests 9/9. FROZEN v3.2 train/dev files
  on disk are now GENERATOR-DIVERGENT — refreeze happens only after the
  amendment review clears; pilot (natural + beta_max 1.0, seed 0) queued.

## 2026-08-31 — v4.2 data REJECTED by dual manual curation (Brian-directed); v4.3 designed

- Opus 5 curator (read all 178 distinct surface forms + 211 full rows + re-ran
  all checkers): DO NOT FREEZE. 895/4473 mutations untargeted (truncation
  violates 2-3 constraints at once -> the fire-everywhere prior via negatives);
  bullets rows (277) 0% topic-grounded; title/postscript/placeholders
  satisfiable by memorizing 1-2 literals; TTR 0.0014 (12 sentences = 67.5% of
  tokens); DEV SHARES topics/pool with train — not a generalization holdout.
- sol curator: REWORK. Crux analysis: prompt attention genuinely needed only at
  first-keyword + numeric-control positions; most CE is filler/fixed-template/
  response-local. Prescription: obligation VALUES must vary per row and derive
  from the prompt; canonicals should be frozen-Qwen greedy outputs minimally
  edited for compliance; EOS supervision; obligation-token weighting.
- v4.3 DESIGN (both curators + fable's causal analysis):
  1. Base texts = frozen Qwen greedy responses to 40 topics x 3 task phrasings
     (120 texts), minimally EDITED per row for compliance; edit spans recorded
     as obligation spans in the dataset.
  2. Obligation values randomized per row and SPECIFIED in the prompt
     (exact title text, postscript phrase, placeholder names).
  3. Mutations rebuilt minimal+targeted (single-constraint violations).
  4. Trainer: EOS in targets; obligation-span CE upweighting.
  5. Topic split 30 train / 10 dev-only (true generalization holdout).
  6. beta_max 1.0 at retrain (fable).

## 2026-08-31 — v4.4 pilot: gate FAIL again (base 0.8418, wave-s0 0.7959)

- The full rework (curated natural data, obligation-weighted CE + EOS,
  beta_max 1.0) cut the harm from -11.0pts to -4.6pts — direction right,
  outcome still a FAIL vs the registered base+2 gate. Dev task CE 1.50
  (vs 4.46 old recipe): the objective now concentrates where the prompt
  matters, yet free-generation adherence still degrades.
- Dose sweep on the retrained wave running (x0.5, x0.25). If NO dose beats
  base+2, both the amplitude story and the objective story are closed for
  this recipe family, and the program-level question goes to the reviewers
  and Brian: the emerging scope hypothesis is that the wave mechanism helps
  when focus-critical information is PROVABLY OUT OF REACH (W3 sealed win:
  +18.5pts with the ledger chunk-deleted) and is parity-to-harmful when the
  base model can already read the prompt (all B3 gates, both B2 probes).
  That is a coherent boundary for the theory, not a failure of the toy-scale
  results — but it bounds the IFEval claim as registered.

## 2026-08-31 — dose sweep: the wave HELPS at low dose (+1.5pts above base)

- v4.4 wave-s0 on dev-v43: gain x1.0 -> 0.7959, x0.5 -> 0.8214, x0.25 ->
  0.8571 vs base 0.8418. NON-MONOTONE: quarter-dose BEATS base by +1.5pts
  (gate needs +2.0). First positive generation-time delta of the program.
- Academic research (results/research-wave-generation.md): the strong scope
  hypothesis is REFUTED — SpotLight (2505.12025) reports positive IFEval
  deltas at 3-8B via DEFICIT-TRIGGERED steering (bias only when per-step
  attention to instruction spans is deficient; zero otherwise); its published
  critique of static bias predicts our x1.0 result. Contrast-pair training
  literature exists for our mutation pairs (MuSC 2502.11541); GRPO-with-
  checker-reward mature at this scale; obligation-state gating unpublished
  (open ground). Ranked: (1) deficit-triggered wave, (2) token-aware contrast
  + GRPO on the 264k controller, (3) scope-graded battery registration.

## 2026-08-31 — sol results review: sweep legit-but-unauditable; data EXHAUSTED; deficit-trigger registered as the LAST rescue

- A (accuracy): x1.0 arm fully audited (165/196 base, 156/196 wave, 6 fixes/15
  regressions). x0.5/x0.25 numbers plausible but NOT auditable — I ran the
  sweep without per-row records (the playbook rule violated a third time;
  lesson: EVERY evaluative run writes records, exploratory or not). n=196
  cannot distinguish +1.5 from +2.0 (best-case paired p=0.125); the gate miss
  is exactly one item. Post-hoc scaling = legitimate exploration, NOT a gate
  result (registered operating point was beta 1.0; x0.25 chosen after seeing
  this dev set; seed 0 only).
- B (data): EXHAUSTED — registered ruling: no v4.5 data curation. Residual
  label note (12.8% weighted-token fraction; 1.6% pathological rows) documented
  for any future objective reuse; cannot explain a one-item miss.
- C (path): REGISTER deficit-triggered steering (SpotLight-adapted): frozen
  v4.4 Wq/Wk select the governing constraint span; per step/layer/head compute
  post-softmax mass psi on it; zero bias if psi >= tau; else uniform span bias
  min(b_max, logit(tau) - logit(psi)) (exact odds correction — sol corrected
  the research note's log-ratio). Deterministic battery: zero-deficit ->
  BITWISE base logits; forced deficit -> finite nonzero; uncapped post-bias
  mass == tau; full intervention logging. tau from a frozen grid on a NEW
  calibration stream; ONE confirmation on >= 512 fresh prompt-disjoint rows;
  gate +2.0pts AND one-sided exact McNemar p < 0.05; seed-1 replication before
  sealed IFEval. STOP-LOSS: iteration 3 is the LAST single-turn rescue — no
  recalibration after confirmation; failure CLOSES the line; contrast/GRPO
  would need Brian's separate authorization.

## 2026-08-31 — fable verification: numbers ACCURATE, +1.5 NOT significant; v4.5 launched

- Fable reproduced x0.25 BIT-FOR-BIT (168/196 = 0.857143, fresh code path);
  base/wave-s0 rescored 0-mismatch; training record + shas verified; no
  contamination. STATISTICS: 7-vs-4 discordants -> McNemar p=0.549, delta CI
  [-1.8, +4.8]pt; ~1900 paired rows to confirm ANY positive effect. The honest
  statement: quarter-dose is indistinguishable from base AND from the gate at
  n=196. FINDING-1 fixed: v4.4 checkpoint was working-tree-only, now committed.
  FINDING-2 stands: x0.5 sweep number is WORKLOG-prose-only (descriptive).
- Confirmation stream extended 512 -> 1024 PRE-RUN on the power analysis
  (registered in the manifest note). Deficit-gate mechanism committed with
  4/4 battery (bitwise-base at zero deficit; exact odds correction verified
  numerically). Calibration chain launched: v4.4 seed-1 training then the
  one-shot tau x b_max grid on cal-v45.

## 2026-08-31 — Brian's ruling: Multi-IF is the decisive experiment; "go from there" on its data

- sol xhigh eval+research (results/b3-eval-research-sol.md): confirmation pass
  odds ~32%; scalar deficit thresholds condemned (15 repairs / 12 regressions,
  amplitude not the missing ingredient; oracle WHEN-chooser ceiling +7.5);
  untried families mapped (retrieval branch, obligation tracker, causal WHEN
  labels); constrained decoding named the honest single-turn ceiling; MMMT-IF
  +22.3pt from re-appending dispersed instructions = published proof the
  multi-turn failure is FOCUS/RETRIEVAL — the wave's arena.
- ORDER: sealed confirmation completes as registered (stop-loss honored either
  way), then Multi-IF three arms (base / deficit-wave user-turn spans /
  static-x0.25) regardless of outcome. Next program decisions wait for
  Multi-IF data (Brian).

## 2026-08-31 — BRIAN'S RULING: v4.5 confirmation killed mid-run; EVF program authorized

- Confirmation seed-0 stopped at Brian's direction (~100/1024 base records
  retained untouched; recorded ABANDONED-BY-RULING). EVF-PLAN.md committed:
  Phase E0 = kill-fast pilot probe on the recorded 15/12 calibration anatomy
  (registered gate r+>=0.60 / r-<=0.25 under topic AND family holdout);
  E1 (GRU tracker + two-stage EVF firing) gated on E0 + separate go.
  Red/green TDD + deterministic proofs required throughout.

## 2026-08-31 — EVF E0 pilot: registered gate FAIL (family-holdout kill criterion triggered)

- 15/12 anatomy, 11 registered features, deterministic probe. Topic folds:
  r+ 0.733 / r- 0.417 (needs <=0.25). Family folds: r+ 0.733 / r- 0.667 —
  near-indiscriminate under family holdout -> the registered kill criterion
  fires. Per-item features committed (results/qwen/e0-pilot.json).
- Honest caveats for the review: n=27 is tiny for 11 features; the gate was
  registered knowing this. The pre-registered sol+fable review of the E0
  result convenes before ANY next step.
Uninstalled 1 package in 0.30ms
Installed 1 package in 2ms
[base] 0/909
{"ci": 0, "key": "1000:1:en", "scores": {"1": {"prompt_level_strict_acc": false, "inst_level_strict_acc": [false, true, false], "prompt_level_loose_acc": false, "inst_level_loose_acc": [false, true, false]}, "2": {"prompt_level_strict_acc": false, "inst_level_strict_acc": [false, true, true, true], "prompt_level_loose_acc": false, "inst_level_loose_acc": [false, true, true, true]}, "3": {"prompt_level_strict_acc": false, "inst_level_strict_acc": [false, true, false, true, true], "prompt_level_loose_acc": false, "inst_level_loose_acc": [false, true, false, true, true]}}, "responses": {"1": "Raymond III, Count of Tripoli, was a significant figure in the history of the County of Tripoli during the 11th century. He was the son of Raymond II, Count of Tripoli, and was born in 1020. Raymond III played a crucial role in the political and military affairs of the County, particularly during the reign of his father. His leadership was marked by efforts to expand the territory of the County and to strengthen its position against external threats.\n\n*highlighted section part 1*  \nRaymond III was known for his strategic military campaigns and his ability to maintain control over the region. He was instrumental in defending the County against invasions from the Byzantine Empire and the Holy Roman Empire. His military successes helped to solidify the influence of the Count of Tripoli in the region.\n\n*highlighted section part 2*  \nOne of the most notable events in his reign was the Battle of Cresson in 1047, where he led a successful defense against a major invasion. This victory was a turning point in the history of the County and demonstrated his military prowess.\n\n*highlighted section part 3*  \nRaymond III's rule ended in 1055 when he was defeated by the Byzantine Emperor Alexios Komnenos. His defeat marked the end of the Count of Tripoli's influence in the region and led to the eventual loss of the County to the Byzantine Empire.\n\nRaymond III's legacy is one of military leadership and political influence, and he remains an important figure in the history of the County of Tripoli. His contributions to the region's stability and defense are still recognized today.", "2": "Raymond III, Count of Tripoli, was a prominent figure in the 11th century and played a key role in the political and military affairs of the County of Tripoli. He was the son of Raymond II and was born in 1020. Raymond III was a strong advocate for the interests of the Crusader states and was involved in the broader context of the Crusades. His reign was marked by efforts to maintain the independence of the County of Tripoli against the growing influence of the Byzantine Empire and the Muslim powers in the region.\n\n*highlighted section part 1*  \nRaymond III was a key figure in the Crusader presence in the region and supported the Crusader cause. His leadership helped to establish and strengthen the Crusader presence in Lebanon, a crucial area for the Crusader states. The County of Tripoli was strategically located in Lebanon, and Raymond III's efforts were vital in securing the region's position.\n\n*highlighted section part 2*  \nDuring his reign, Raymond III faced significant challenges from the Muslim powers, particularly the Seljuk Empire. He was involved in several conflicts with the Muslim forces and worked to defend the County against invasions. His military campaigns were a crucial part of the broader struggle between the Crusader states and the Muslim world.\n\n*highlighted section part 3*  \nRaymond III's rule ended in 1055 when he was defeated by the Byzantine Emperor Alexios Komnenos. His defeat marked the end of the Count of Tripoli's influence in the region and led to the eventual loss of the County to the Byzantine Empire. The loss of Tripoli to the Byzantines had significant implications for the Crusader presence in Lebanon and the broader region.\n\nRaymond III's legacy is one of military leadership and political influence, and he remains an important figure in the history of the County of Tripoli. His contributions to the region's stability and defense are still recognized today. The Crusader presence in Lebanon was a crucial part of his legacy, and his efforts helped to shape the political landscape of the region.", "3": "Raymond III, Count of Tripoli, was a prominent figure in the 11th century and played a key role in the political and military affairs of the County of Tripoli. He was the son of Raymond II and was born in 1020. Raymond III was a strong advocate for the interests of the Crusader states and was involved in the broader context of the Crusades. His reign was marked by efforts to maintain the independence of the County of Tripoli against the growing influence of the Byzantine Empire and the Muslim powers in the region.\n\n*highlighted section part 1*  \nRaymond III was a key figure in the Crusader presence in the region and supported the Crusader cause. His leadership helped to establish and strengthen the Crusader presence in Lebanon, a crucial area for the Crusader states. The County of Tripoli was strategically located in Lebanon, and Raymond III's efforts were vital in securing the region's position.\n\n*highlighted section part 2*  \nDuring his reign, Raymond III faced significant challenges from the Muslim powers, particularly the Seljuk Empire. He was involved in several conflicts with the Muslim forces and worked to defend the County against invasions. His military campaigns were a crucial part of the broader struggle between the Crusader states and the Muslim world.\n\n*highlighted section part 3*  \nRaymond III's rule ended in 1055 when he was defeated by the Byzantine Emperor Alexios Komnenos. His defeat marked the end of the Count of Tripoli's influence in the region and led to the eventual loss of the County to the Byzantine Empire. The loss of Tripoli to the Byzantines had significant implications for the Crusader presence in Lebanon and the broader region.\n\nthis overview provides a glimpse into the complexities and intrigues of crusader-era politics and warfare."}, "gen": {"1": {"n": 340, "truncated": false, "timeout": false}, "2": {"n": 427, "truncated": false, "timeout": false}, "3": {"n": 375, "truncated": false, "timeout": false}}}
exec
/bin/bash -lc "sed -n '1,420p' src/stencil/evf.py && sed -n '1,340p' tests/test_evf_pilot.py && rg -n 'b3-deficit-cal|t30-b3|selected|results' scripts/b3_deficit* src/stencil/bench.py | head -n 240" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
# ruff: noqa: E501
"""EVF Phase E0 pilot library (EVF-PLAN.md; red/green TDD).

Pure-python probe machinery is dependency-free and deterministic by
construction (zero-init logistic GD, fixed iteration count). Feature
extraction is a teacher-forced pass through the frozen trunk plus one
weak-focus counterfactual forward — deterministic, proven bitwise by
tests/test_evf_pilot.py.
"""
import json
import math
import random
from pathlib import Path

TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
WAVE_LAYERS = range(20, 28)


def first_divergence(tok, a, b):
    """index of the first differing TOKEN between texts a and b
    (None if their token id sequences are identical)."""
    ia, ib = tok.encode(a).ids, tok.encode(b).ids
    n = min(len(ia), len(ib))
    for k in range(n):
        if ia[k] != ib[k]:
            return k
    if len(ia) == len(ib):
        return None
    return n


def _load_records(root, arm):
    d = Path(root) / "results" / "qwen" / "b3-deficit-cal"
    base, wave = {}, {}
    for p in d.glob("base-*.json"):
        r = json.loads(p.read_text())
        base[r["i"]] = r
    for p in d.glob(f"{arm}-*.json"):
        r = json.loads(p.read_text())
        wave[r["i"]] = r
    rows = [json.loads(line) for line in open(Path(root) / "data" / "b3" / "cal-v45.jsonl")]
    return base, wave, rows


def load_anatomy(root, arm="t30-b3"):
    """discordant rows (repair label=1 / regression label=0), joined."""
    base, wave, rows = _load_records(root, arm)
    out = []
    for i in sorted(base):
        b, w = base[i], wave[i]
        if b["adherent"] == w["adherent"]:
            continue
        out.append({"row": rows[i], "i": i,
                    "base_response": b["response"], "wave_response": w["response"],
                    "base_adherent": b["adherent"], "wave_adherent": w["adherent"],
                    "label": int(w["adherent"])})
    return out


def load_controls(root, arm="t30-b3", n=30, seed=11):
    """seeded sample of concordant rows (matched control points)."""
    base, wave, rows = _load_records(root, arm)
    conc = [i for i in sorted(base) if base[i]["adherent"] == wave[i]["adherent"]]
    rng = random.Random(seed)
    pick = sorted(rng.sample(conc, n))
    return [{"row": rows[i], "i": i,
             "base_response": base[i]["response"], "wave_response": wave[i]["response"],
             "base_adherent": base[i]["adherent"], "wave_adherent": wave[i]["adherent"]}
            for i in pick]


def load_model(root):
    import torch
    from tokenizers import Tokenizer

    from stencil import determinism  # noqa: F401
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController
    root = Path(root)
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(root / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    return m, tok, ctrl.eval()


def constraint_spans_of(tok, prompt):
    ptxt = TMPL.format(p=prompt)
    enc = tok.encode(ptxt)
    spans, start = [], 0
    while True:
        i = ptxt.find("Constraint:", start)
        if i < 0:
            break
        j = ptxt.find("Constraint:", i + 1)
        end = j if j > 0 else ptxt.find("<|im_end|>", i)
        toks = [ti for ti, (a, b) in enumerate(enc.offsets) if a < end and b > i]
        if toks:
            spans.append((toks[0], toks[-1] + 1))
        start = i + 1
    return spans


def extract_features(m, tok, ctrl, item, probe_pos=None):
    """registered E0 feature set at the divergence point (or probe_pos)."""
    import torch
    import torch.nn.functional as F
    row = item["row"]
    k = first_divergence(tok, item["base_response"], item["wave_response"])
    shared = tok.encode(item["base_response"]).ids[: (k if k is not None else 0)]
    if probe_pos is not None:
        shared = shared[:probe_pos]
    p_ids = tok.encode(TMPL.format(p=row["prompt"])).ids
    P = len(p_ids)
    ids = p_ids + shared
    toks = torch.tensor([ids], device="cuda")
    spans = constraint_spans_of(tok, row["prompt"])
    with torch.no_grad():
        logits, h20 = m(toks, capture_hidden=20)
        lp = F.log_softmax(logits[0, -6:].float(), dim=-1)
        probs = lp.exp()
        ents = (-(probs * lp).sum(-1)).tolist()
        tops = probs.topk(2, dim=-1).values
        margins = (tops[:, 0] - tops[:, 1]).tolist()
        # rule readout via the frozen wave's q/k
        q = F.normalize(ctrl.W_q(h20[0, -1:].float()), dim=-1)
        kk = F.normalize(ctrl.W_k(h20[0, :P].float()), dim=-1)
        scores = (q @ kk.T)[0]
        span_scores = sorted((float(scores[a:b].mean()) for a, b in spans), reverse=True) or [0.0]
        best_span = max(spans, key=lambda ab: float(scores[ab[0]:ab[1]].mean())) if spans else (0, 1)
        # natural attention mass on the governing span (layers 20-27, last row)
        pm = torch.zeros(len(ids), dtype=torch.bool, device="cuda")
        pm[best_span[0]:best_span[1]] = True
        sink = {}
        m(toks, attn_probe=(pm, sink))
        attn_mass = sum(sink.values()) / len(sink)
        # weak-focus counterfactual: b=1.0 on the governing span, last row
        T = len(ids)
        bias = torch.zeros(T, T, device="cuda")
        bias[-1, best_span[0]:best_span[1]] = 1.0
        l1 = m(toks, attn_bias={L: bias for L in WAVE_LAYERS})[0, -1].float()
        p0 = F.log_softmax(logits[0, -1].float(), dim=-1)
        p1 = F.log_softmax(l1, dim=-1)
        kl = float((p1.exp() * (p1 - p0)).sum())
        mix = torch.logsumexp(torch.stack([p0, p1]), dim=0) - math.log(2)
        js = 0.5 * float((p0.exp() * (p0 - mix)).sum()) + 0.5 * float((p1.exp() * (p1 - mix)).sum())
        ob_ids = sorted({tid for kkey, sps in row["obligation_spans"].items()
                         for a, b in sps
                         for tid in tok.encode(row["canonical"][a:b]).ids})
        ob_shift = float((p1[ob_ids] - p0[ob_ids]).mean()) if ob_ids else 0.0
    return {
        "entropy": float(ents[-1]), "margin": float(margins[-1]),
        "entropy_delta5": float(ents[-1] - ents[0]), "margin_delta5": float(margins[-1] - margins[0]),
        "readout_top": span_scores[0],
        "readout_margin": span_scores[0] - (span_scores[1] if len(span_scores) > 1 else 0.0),
        "attn_mass_span": float(attn_mass),
        "kl_focus": kl, "js_focus": js, "obligation_shift": ob_shift,
        "rel_pos": len(shared) / max(1, len(shared) + 32),
    }


# --- deterministic probe ----------------------------------------------------

def _standardize(feats):
    keys = sorted(feats[0])
    mu = {k: sum(f[k] for f in feats) / len(feats) for k in keys}
    sd = {k: (sum((f[k] - mu[k]) ** 2 for f in feats) / len(feats)) ** 0.5 or 1.0 for k in keys}
    return keys, mu, sd


def fit_probe(feats, labels, seed=0, l2=1.0, iters=500, lr=0.1):
    """zero-init logistic GD — deterministic (seed kept for signature)."""
    keys, mu, sd = _standardize(feats)
    X = [[(f[k] - mu[k]) / sd[k] for k in keys] for f in feats]
    w = [0.0] * len(keys)
    b = 0.0
    n = len(X)
    for _ in range(iters):
        gw = [l2 * wi / n for wi in w]
        gb = 0.0
        for x, y in zip(X, labels):
            z = sum(wi * xi for wi, xi in zip(w, x)) + b
            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
            e = p - y
            for j in range(len(w)):
                gw[j] += e * x[j] / n
            gb += e / n
        w = [wi - lr * gi for wi, gi in zip(w, gw)]
        b -= lr * gb
    return {"keys": keys, "mu": mu, "sd": sd, "w": w, "b": b}


def predict(model, f):
    z = sum(wi * (f[k] - model["mu"][k]) / model["sd"][k]
            for wi, k in zip(model["w"], model["keys"])) + model["b"]
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))


def gate_eval(feats, labels, groups, seed=0, threshold=0.5):
    """leave-one-group-out CV; returns held-out repair recall (r_plus)
    and regression fire-rate (r_minus)."""
    preds = {}
    for g in sorted(set(groups)):
        tr = [i for i in range(len(feats)) if groups[i] != g]
        te = [i for i in range(len(feats)) if groups[i] == g]
        if not tr or not te:
            continue
        model = fit_probe([feats[i] for i in tr], [labels[i] for i in tr], seed=seed)
        for i in te:
            preds[i] = predict(model, feats[i]) >= threshold
    pos = [i for i in preds if labels[i] == 1]
    neg = [i for i in preds if labels[i] == 0]
    r_plus = sum(preds[i] for i in pos) / len(pos) if pos else 0.0
    r_minus = sum(preds[i] for i in neg) / len(neg) if neg else 1.0
    return {"r_plus": r_plus, "r_minus": r_minus, "n_pos": len(pos), "n_neg": len(neg)}
# ruff: noqa: E501
"""EVF Phase E0 pilot — red/green TDD.

Fixture tests are hand-executed first (playbook): the divergence finder
fixtures below were computed by hand before src/stencil/evf.py existed.
GPU tests prove deterministic feature extraction (bitwise across runs).
"""
import json
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent


# --- divergence finder (pure, CPU) -----------------------------------------

def test_first_divergence_token_fixtures():
    from tokenizers import Tokenizer

    from stencil.evf import first_divergence
    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    # hand-executed: identical texts -> None
    assert first_divergence(tok, "The lake was calm.", "The lake was calm.") is None
    # hand-executed: "The lake was calm." vs "The lake was blue." share
    # "The lake was" -> ids diverge at the token covering "calm"/"blue".
    a, b = "The lake was calm.", "The lake was blue."
    ia, ib = tok.encode(a).ids, tok.encode(b).ids
    k = first_divergence(tok, a, b)
    assert k is not None and 0 < k <= min(len(ia), len(ib))
    assert ia[:k] == ib[:k] and (k == min(len(ia), len(ib)) or ia[k] != ib[k])
    # hand-executed: divergence at the very first token
    assert first_divergence(tok, "Alpha beta.", "Gamma beta.") == 0
    # one text a strict prefix of the other -> divergence at the shorter length
    p, q = "Same start here", "Same start here and more"
    assert first_divergence(tok, p, q) == len(tok.encode(p).ids)


def test_discordant_anatomy_counts():
    from stencil.evf import load_anatomy
    anat = load_anatomy(ROOT, arm="t30-b3")
    repairs = [r for r in anat if r["label"] == 1]
    regressions = [r for r in anat if r["label"] == 0]
    assert len(repairs) == 15 and len(regressions) == 12
    for r in anat:
        assert r["base_response"] and r["wave_response"]
        assert r["row"]["prompt"]  # joined with the cal-v45 dataset row
        assert r["base_adherent"] != r["wave_adherent"]
        assert r["label"] == int(r["wave_adherent"])


def test_concordant_controls():
    from stencil.evf import load_controls
    ctl = load_controls(ROOT, arm="t30-b3", n=30, seed=11)
    assert len(ctl) == 30
    assert all(c["base_adherent"] == c["wave_adherent"] for c in ctl)
    # deterministic draw
    ctl2 = load_controls(ROOT, arm="t30-b3", n=30, seed=11)
    assert [c["row"]["key"] for c in ctl] == [c2["row"]["key"] for c2 in ctl2]


# --- feature extraction (GPU) ----------------------------------------------

@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")
def test_feature_extraction_bitwise_deterministic():
    from stencil.evf import extract_features, load_anatomy, load_model
    m, tok, ctrl = load_model(ROOT)
    anat = load_anatomy(ROOT, arm="t30-b3")
    item = anat[0]
    f1 = extract_features(m, tok, ctrl, item)
    f2 = extract_features(m, tok, ctrl, item)
    assert f1.keys() == f2.keys()
    for k in f1:
        assert f1[k] == f2[k], k  # bitwise-equal floats (deterministic proof)
    # registered feature set present
    for k in ("entropy", "margin", "entropy_delta5", "margin_delta5",
              "readout_top", "readout_margin", "attn_mass_span",
              "kl_focus", "js_focus", "obligation_shift"):
        assert k in f1, k


# --- probe fit + gate (CPU, deterministic) ---------------------------------

def test_probe_fit_deterministic_and_gate_math():
    from stencil.evf import fit_probe, gate_eval
    # synthetic separable fixture (hand-built): feature x separates labels
    feats = [{"x": float(i >= 10), "y": 0.5} for i in range(20)]
    labels = [int(i >= 10) for i in range(20)]
    groups = [f"t{i % 4}" for i in range(20)]
    w1 = fit_probe(feats, labels, seed=0)
    w2 = fit_probe(feats, labels, seed=0)
    assert w1 == w2  # deterministic fit
    res = gate_eval(feats, labels, groups, seed=0)
    assert res["r_plus"] == 1.0 and res["r_minus"] == 0.0
    # anti-separable fixture: shuffled labels cannot pass the gate
    import random
    rng = random.Random(3)
    bad = labels[:]
    rng.shuffle(bad)
    res2 = gate_eval(feats, bad, groups, seed=0)
    assert not (res2["r_plus"] >= 0.60 and res2["r_minus"] <= 0.25)
src/stencil/bench.py:46:    return ifeval_utils.process_results(row, [response])
scripts/b3_deficit_conf.py:27:CKPT = ROOT / "results" / "qwen" / ("b3-ce-s0.pt" if SEED == 0 else "b3-ce-s1.pt")
scripts/b3_deficit_conf.py:29:cal = json.loads((ROOT / "results" / "qwen" / "b3-deficit-cal.json").read_text())
scripts/b3_deficit_conf.py:30:sel = cal["results"][cal["selected"]]
scripts/b3_deficit_conf.py:71:outdir = ROOT / "results" / "qwen" / f"b3-deficit-conf-s{SEED}"
scripts/b3_deficit_conf.py:124:(ROOT / "results" / "qwen" / f"b3-deficit-conf-s{SEED}.json").write_text(json.dumps(out, indent=1))
scripts/b3_deficit_cal.py:29:ctrl.load_state_dict(torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
scripts/b3_deficit_cal.py:62:outdir = ROOT / "results" / "qwen" / "b3-deficit-cal"
scripts/b3_deficit_cal.py:83:        n_int = len(log)  # steps with a selected span (intervention opportunity)
scripts/b3_deficit_cal.py:93:results = {"base": run_arm("base", None, None)}
scripts/b3_deficit_cal.py:94:print("[base]", results["base"], flush=True)
scripts/b3_deficit_cal.py:97:    results[name] = {"tau": tau, "b_max": bm, **run_arm(name, tau, bm)}
scripts/b3_deficit_cal.py:98:    print(f"[{name}]", results[name], flush=True)
scripts/b3_deficit_cal.py:99:grid = {k: v for k, v in results.items() if k != "base"}
scripts/b3_deficit_cal.py:101:out = {"results": results, "selected": best,
scripts/b3_deficit_cal.py:102:       "ctrl_sha256": hashlib.sha256((ROOT / "results" / "qwen" / "b3-ce-s0.pt").read_bytes()).hexdigest()}
scripts/b3_deficit_cal.py:103:(ROOT / "results" / "qwen" / "b3-deficit-cal.json").write_text(json.dumps(out, indent=1))
scripts/b3_deficit_cal.py:104:print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))

exec
/bin/bash -lc "sed -n '1,240p' results/qwen/b3-deficit-cal/base-000.json && sed -n '1,240p' results/qwen/b3-deficit-cal/t30-b3-000.json && sed -n '1,260p' scripts/b3_deficit_cal.py && rg -n 'def run_one|strict|instruction_id|combo|adherent' src/stencil/b3_gen.py src/stencil/bench.py scripts/b3_deficit_cal.py | head -n 220" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
{"i": 0, "adherent": false, "n_gen": 166, "truncated": false, "timeout": false, "n_interventions": 0, "response": "Patching a canvas sail is a simple yet important task that ensures your boat remains safe and efficient. Start by inspecting the sail for tears, holes, or loose seams. Use a strong, waterproof glue or a specialized sail repair tape to stitch the damaged areas. Make sure the stitches are tight and secure, and allow the repair to dry completely. A well-patched sail will reduce drag and improve performance. \n\nIf the damage is more extensive, consider using a lantern-shaped patch, which provides a clean and durable solution. A lantern-shaped patch can be cut from a piece of canvas and sewn into place, offering both strength and a neat appearance. This method is especially useful for larger tears or holes. Always ensure the patch is properly aligned and secured with strong stitching. \n\nP.P.S. Do not forget the weather."}{"i": 0, "adherent": true, "n_gen": 188, "truncated": false, "timeout": false, "n_interventions": 188, "response": "Patching a canvas sail is a crucial step in maintaining its performance and longevity. Start by inspecting the sail for tears, holes, or frayed edges. Use a strong, waterproof glue or a specialized sail repair tape to secure the damaged area. Apply the repair in a way that blends with the existing fabric, ensuring it is both secure and aesthetically pleasing. A well-patched sail will perform better and last longer, allowing you to enjoy your sailing adventures with confidence.\n\nA lantern can be used to illuminate the repair area, making it easier to see the details and ensure the patch is applied correctly. The lantern’s light can also help you spot any hidden flaws in the sail. By using a lantern, you can work more efficiently and with greater precision. The lantern’s glow can serve as a reminder of the importance of careful work and attention to detail when patching a sail.\n\nP.P.S. Do not forget the weather."}# ruff: noqa
"""v4.5 tau calibration (ONE SHOT, registered): base + frozen grid
tau {0.10,0.20,0.30,0.45} x b_max {3.0,6.0} on cal-v45 (200 rows).
Selection: highest adherence; ties -> LOWER intervention rate.
Per-item atomic records for every arm. Seed-0 Wq/Wk only."""
import json, random, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.bench import TMPL, generate_deficit
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

sys.path.insert(0, str(ROOT / "vendor"))
import langdetect
langdetect.DetectorFactory.seed = 0
from ifeval import instructions_registry

GRID = [(t, b) for t in (0.10, 0.20, 0.30, 0.45) for b in (3.0, 6.0)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
ctrl = WaveController(beta_max=1.0).cuda()
ctrl.load_state_dict(torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
ctrl = ctrl.eval()
rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "cal-v45.jsonl")]
assert len(rows) == 200


def prompt_spans_of(row):
    ptxt = TMPL.format(p=row["prompt"])
    enc = tok.encode(ptxt)
    spans, start = [], 0
    while True:
        i = ptxt.find("Constraint:", start)
        if i < 0:
            break
        j = ptxt.find("Constraint:", i + 1)
        end = j if j > 0 else ptxt.find("<|im_end|>", i)
        toks = [ti for ti, (a, b) in enumerate(enc.offsets) if a < end and b > i]
        if toks:
            spans.append((toks[0], toks[-1] + 1))
        start = i + 1
    return spans


def adherent(row, text):
    random.seed(row["key"])
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in kw.items() if v})
        if not (text.strip() and inst.check_following(text)):
            return False
    return True


outdir = ROOT / "results" / "qwen" / "b3-deficit-cal"
outdir.mkdir(parents=True, exist_ok=True)


def run_arm(name, tau, b_max):
    n_ok, n_interv, n_steps = 0, 0, 0
    for i, r in enumerate(rows):
        rec_p = outdir / f"{name}-{i:03d}.json"
        if rec_p.exists():
            rec = json.loads(rec_p.read_text())
            n_ok += rec["adherent"]; n_interv += rec["n_interventions"]; n_steps += rec["n_gen"]
            continue
        if tau is None:
            from stencil.bench import generate_cached
            text, n, tr, to = generate_cached(m, tok, r["prompt"], deadline_s=300)
            log = []
        else:
            text, n, tr, to, log = generate_deficit(
                m, tok, r["prompt"], ctrl, prompt_spans_of(r), tau, b_max, deadline_s=300)
        ok = adherent(r, text)
        n_ok += ok; n_steps += n
        n_int = len(log)  # steps with a selected span (intervention opportunity)
        n_interv += n_int
        rec = {"i": i, "adherent": bool(ok), "n_gen": n, "truncated": bool(tr),
               "timeout": bool(to), "n_interventions": n_int, "response": text}
        tmp = rec_p.with_suffix(".tmp"); tmp.write_text(json.dumps(rec, ensure_ascii=False)); tmp.rename(rec_p)
        if i % 50 == 0:
            print(f"[{name}] {i}/200 adh {n_ok/(i+1):.3f}", flush=True)
    return {"adherence": n_ok / 200, "interventions_per_token": (n_interv / max(1, n_steps))}


results = {"base": run_arm("base", None, None)}
print("[base]", results["base"], flush=True)
for tau, bm in GRID:
    name = f"t{int(tau*100):02d}-b{int(bm)}"
    results[name] = {"tau": tau, "b_max": bm, **run_arm(name, tau, bm)}
    print(f"[{name}]", results[name], flush=True)
grid = {k: v for k, v in results.items() if k != "base"}
best = max(grid, key=lambda k: (grid[k]["adherence"], -grid[k]["interventions_per_token"]))
out = {"results": results, "selected": best,
       "ctrl_sha256": hashlib.sha256((ROOT / "results" / "qwen" / "b3-ce-s0.pt").read_bytes()).hexdigest()}
(ROOT / "results" / "qwen" / "b3-deficit-cal.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
scripts/b3_deficit_cal.py:26:m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
scripts/b3_deficit_cal.py:52:def adherent(row, text):
scripts/b3_deficit_cal.py:54:    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
scripts/b3_deficit_cal.py:72:            n_ok += rec["adherent"]; n_interv += rec["n_interventions"]; n_steps += rec["n_gen"]
scripts/b3_deficit_cal.py:81:        ok = adherent(r, text)
scripts/b3_deficit_cal.py:85:        rec = {"i": i, "adherent": bool(ok), "n_gen": n, "truncated": bool(tr),
src/stencil/bench.py:6:lm-eval's pinned copy of Google's code) — strict + loose, four metrics.
src/stencil/bench.py:53:        "prompt_level_strict_acc": sum(p["prompt_level_strict_acc"] for p in per_prompt) / n,
src/stencil/bench.py:54:        "inst_level_strict_acc": ifeval_utils.agg_inst_level_acc(
src/stencil/bench.py:55:            [p["inst_level_strict_acc"] for p in per_prompt]),
src/stencil/b3_gen.py:7:VENDORED verifier instruction_id so canonical responses are checked by
src/stencil/b3_gen.py:181:    """allowed unordered pairs; a combo is valid iff every pair is allowed.
src/stencil/b3_gen.py:207:            allowed.add(tuple(sorted((a, b))))  # canonical order == combo_ok's lookup order
src/stencil/b3_gen.py:212:def combo_ok(combo, matrix):
src/stencil/b3_gen.py:213:    if len(combo) == 1:
src/stencil/b3_gen.py:215:    if any(c in matrix["singletons"] for c in combo):
src/stencil/b3_gen.py:218:    for i, a in enumerate(combo):
src/stencil/b3_gen.py:219:        for b in combo[i + 1:]:
src/stencil/b3_gen.py:225:def build_canonical(rng, combo, kwargs_by_key, topic=None):
src/stencil/b3_gen.py:226:    """canonical adherent response for a constraint combo (registered
src/stencil/b3_gen.py:230:    for key in combo:
src/stencil/b3_gen.py:244:    if "json_fmt" in combo:
src/stencil/b3_gen.py:246:    if "two_resp" in combo:
src/stencil/b3_gen.py:248:    if "bullets" in combo:
src/stencil/b3_gen.py:252:        if "n_words_min" in combo:
src/stencil/b3_gen.py:263:    if "n_words_max" in combo:
src/stencil/b3_gen.py:274:    if "title" in combo:
src/stencil/b3_gen.py:276:    if "placeholders" in combo:
src/stencil/b3_gen.py:280:    if "postscript" in combo:
src/stencil/b3_gen.py:282:    if "caps" in combo:
src/stencil/b3_gen.py:284:    if "lower" in combo:
src/stencil/b3_gen.py:302:        # resample the combo WITHIN the drawn size so combo-size frequency
src/stencil/b3_gen.py:305:        combo = None
src/stencil/b3_gen.py:308:            if combo_ok(cand, matrix):
src/stencil/b3_gen.py:309:                combo = cand
src/stencil/b3_gen.py:311:        if combo is None:
src/stencil/b3_gen.py:313:        kwargs_by_key = {k: CONSTRAINTS[k]["sample"](rng) for k in combo}
src/stencil/b3_gen.py:318:        for k in combo:
src/stencil/b3_gen.py:332:        phrases = [CONSTRAINTS[k]["phrase"](kwargs_by_key[k]) for k in combo]
src/stencil/b3_gen.py:336:        canonical = build_canonical(rng, combo, kwargs_by_key, topic=topic)
src/stencil/b3_gen.py:337:        mutations = {k: CONSTRAINTS[k]["mutate"](canonical, kwargs_by_key[k]) for k in combo}
src/stencil/b3_gen.py:341:            "instruction_id_list": [CONSTRAINTS[k]["iid"] for k in combo],
src/stencil/b3_gen.py:342:            "kwargs": [kwargs_by_key[k] for k in combo],
src/stencil/b3_gen.py:343:            "combo": combo,
src/stencil/b3_gen.py:362:        for iid, kw, key in zip(r["instruction_id_list"], r["kwargs"], r["combo"]):
src/stencil/b3_gen.py:381:    for key, kw in zip(row["combo"], row["kwargs"]):

exec
/bin/bash -lc "PYTHONPATH=src:vendor python - <<'PY'
import json,random
from pathlib import Path
from ifeval import instructions_registry
root=Path('.')
rows=[json.loads(x) for x in open('data/b3/cal-v45.jsonl')]
FAMILY={'caps':'change_case','lower':'change_case','kw_exist':'keywords','kw_freq':'keywords','kw_forbid':'keywords','n_words_min':'length','n_words_max':'length','n_sent':'length','bullets':'format','title':'format','json_fmt':'format','placeholders':'content','postscript':'content','two_resp':'combination'}

def cells(row,text):
 random.seed(row['key']); out=[]
 for iid,kw,key in zip(row['instruction_id_list'],row['kwargs'],row['combo']):
  inst=instructions_registry.INSTRUCTION_DICT[iid](iid); inst.build_description(**{k:v for k,v in kw.items() if v})
  out.append((key,bool(text.strip() and inst.check_following(text))))
 return out
counts={'first_matches_changed':0,'single_changed':0,'multi_changed':0,'total':0}
for i,row in enumerate(rows):
 bp=Path(f'results/qwen/b3-deficit-cal/base-{i:03d}.json'); wp=Path(f'results/qwen/b3-deficit-cal/t30-b3-{i:03d}.json')
 if not bp.exists() or not wp.exists(): continue
 b=json.loads(bp.read_text());w=json.loads(wp.read_text())
 if b['adherent']==w['adherent']: continue
 bc=cells(row,b['response']); wc=cells(row,w['response']); ch=[k for (k,x),(_,y) in zip(bc,wc) if x"'!=y]
 counts['"'total']+=1; counts['first_matches_changed']+=bool(row['combo'][0] in ch); counts['single_changed']+=len(ch)==1; counts['multi_changed']+=len(ch)>1
 print(i,b['adherent'],'->',w['adherent'],'combo',row['combo'],'changed',ch,'base',bc,'wave',wc)
print(counts)
PY" in /home/bmarti44/stencil-llm
 exited 127 in 0ms:
/bin/bash: line 1: python: command not found

exec
/bin/bash -lc "PYTHONPATH=src:vendor /usr/bin/python3 - <<'PY'
import json,random
from pathlib import Path
from ifeval import instructions_registry
rows=[json.loads(x) for x in open('data/b3/cal-v45.jsonl')]
def cells(row,text):
 random.seed(row['key']); out=[]
 for iid,kw,key in zip(row['instruction_id_list'],row['kwargs'],row['combo']):
  inst=instructions_registry.INSTRUCTION_DICT[iid](iid); inst.build_description(**{k:v for k,v in kw.items() if v})
  out.append((key,bool(text.strip() and inst.check_following(text))))
 return out
counts={'first_matches_changed':0,'single_changed':0,'multi_changed':0,'total':0}
for i,row in enumerate(rows):
 bp=Path(f'results/qwen/b3-deficit-cal/base-{i:03d}.json'); wp=Path(f'results/qwen/b3-deficit-cal/t30-b3-{i:03d}.json')
 if not bp.exists() or not wp.exists(): continue
 b=json.loads(bp.read_text());w=json.loads(wp.read_text())
 if b['adherent']==w['adherent']: continue
 bc=cells(row,b['response']); wc=cells(row,w['response']); ch=[k for (k,x),(_,y) in zip(bc,wc) if x"'!=y]
 counts['"'total']+=1; counts['first_matches_changed']+=bool(row['combo'][0] in ch); counts['single_changed']+=len(ch)==1; counts['multi_changed']+=len(ch)>1
 print(i,b['adherent'],'->',w['adherent'],'combo',row['combo'],'changed',ch)
print(counts)
PY" in /home/bmarti44/stencil-llm
 exited 1 in 0ms:
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
  File "/home/bmarti44/stencil-llm/vendor/ifeval/instructions_registry.py", line 17, in <module>
    from . import instructions
  File "/home/bmarti44/stencil-llm/vendor/ifeval/instructions.py", line 25, in <module>
    import langdetect
ModuleNotFoundError: No module named 'langdetect'

exec
/bin/bash -lc 'ls -d .venv/bin/python* 2>/dev/null || true; command -v python3; find /home/bmarti44/.cache/uv -maxdepth 4 -type f -name python -o -name python3 2>/dev/null | head' in /home/bmarti44/stencil-llm
 succeeded in 0ms:
.venv/bin/python
.venv/bin/python3
.venv/bin/python3.12
/usr/bin/python3
/home/bmarti44/.cache/uv/archive-v0/MHE7YyLVIXPJfd4pX7EtV/bin/python3
/home/bmarti44/.cache/uv/archive-v0/9kDt5t9iJzgC2Fqz2xu60/bin/python3
/home/bmarti44/.cache/uv/archive-v0/ljmK31kRR6FGwODHQQynM/bin/python3
/home/bmarti44/.cache/uv/archive-v0/1_m7yZnFsThOYClc7G8GO/bin/python3
/home/bmarti44/.cache/uv/archive-v0/1_KlKUsW-BshMtI9NYRwD/bin/python3
/home/bmarti44/.cache/uv/archive-v0/BriZ7UKYIuvJsBdf52gKy/bin/python3
/home/bmarti44/.cache/uv/archive-v0/0OPj9icHOeRubmASQsi_L/bin/python3
/home/bmarti44/.cache/uv/archive-v0/tL1VD6USEZJoqgjxoY7im/bin/python3
/home/bmarti44/.cache/uv/archive-v0/A7yBgZZM6lnG0E9me44iy/bin/python3
/home/bmarti44/.cache/uv/archive-v0/Z552Cq45EJKH7dcn8hwbL/bin/python3

exec
/bin/bash -lc "PYTHONPATH=src:vendor .venv/bin/python - <<'PY'
import json,random
from pathlib import Path
from ifeval import instructions_registry
rows=[json.loads(x) for x in open('data/b3/cal-v45.jsonl')]
def cells(row,text):
 random.seed(row['key']); out=[]
 for iid,kw,key in zip(row['instruction_id_list'],row['kwargs'],row['combo']):
  inst=instructions_registry.INSTRUCTION_DICT[iid](iid); inst.build_description(**{k:v for k,v in kw.items() if v})
  out.append((key,bool(text.strip() and inst.check_following(text))))
 return out
counts={'first_matches_changed':0,'single_changed':0,'multi_changed':0,'total':0}
for i,row in enumerate(rows):
 bp=Path(f'results/qwen/b3-deficit-cal/base-{i:03d}.json'); wp=Path(f'results/qwen/b3-deficit-cal/t30-b3-{i:03d}.json')
 if not bp.exists() or not wp.exists(): continue
 b=json.loads(bp.read_text());w=json.loads(wp.read_text())
 if b['adherent']==w['adherent']: continue
 bc=cells(row,b['response']); wc=cells(row,w['response']); ch=[k for (k,x),(_,y) in zip(bc,wc) if x"'!=y]
 counts['"'total']+=1; counts['first_matches_changed']+=bool(row['combo'][0] in ch); counts['single_changed']+=len(ch)==1; counts['multi_changed']+=len(ch)>1
 print(i,b['adherent'],'->',w['adherent'],'combo',row['combo'],'changed',ch)
print(counts)
PY" in /home/bmarti44/stencil-llm
 succeeded in 478ms:
0 False -> True combo ['kw_forbid', 'kw_freq', 'postscript'] changed ['kw_freq']
28 False -> True combo ['kw_exist', 'kw_forbid'] changed ['kw_forbid']
34 False -> True combo ['caps', 'placeholders', 'title'] changed ['caps']
37 True -> False combo ['kw_forbid', 'n_words_max', 'title'] changed ['n_words_max']
44 False -> True combo ['bullets', 'kw_exist', 'placeholders'] changed ['kw_exist']
46 False -> True combo ['kw_forbid', 'kw_freq', 'placeholders'] changed ['kw_freq']
50 True -> False combo ['bullets', 'kw_forbid'] changed ['bullets']
70 False -> True combo ['placeholders'] changed ['placeholders']
71 True -> False combo ['kw_freq', 'n_words_max', 'title'] changed ['kw_freq']
74 True -> False combo ['kw_exist', 'kw_freq', 'n_words_min'] changed ['kw_freq']
89 False -> True combo ['caps', 'placeholders'] changed ['caps']
90 True -> False combo ['n_words_min', 'placeholders'] changed ['n_words_min']
94 True -> False combo ['n_sent', 'placeholders', 'title'] changed ['n_sent']
96 True -> False combo ['kw_freq', 'n_words_max'] changed ['kw_freq']
102 False -> True combo ['placeholders'] changed ['placeholders']
123 False -> True combo ['caps', 'n_words_max'] changed ['caps']
124 True -> False combo ['kw_exist', 'kw_freq', 'postscript'] changed ['kw_exist', 'kw_freq']
130 False -> True combo ['kw_freq', 'n_words_min', 'placeholders'] changed ['kw_freq']
132 False -> True combo ['caps', 'n_sent', 'placeholders'] changed ['placeholders']
133 True -> False combo ['kw_forbid', 'n_sent'] changed ['n_sent']
134 False -> True combo ['caps', 'n_sent'] changed ['caps']
142 False -> True combo ['bullets', 'lower'] changed ['bullets']
145 False -> True combo ['kw_exist', 'postscript'] changed ['kw_exist']
164 True -> False combo ['caps'] changed ['caps']
170 True -> False combo ['kw_forbid', 'n_words_max', 'postscript'] changed ['n_words_max']
176 True -> False combo ['kw_freq', 'n_words_min', 'placeholders'] changed ['kw_freq']
178 False -> True combo ['kw_freq', 'n_words_min', 'placeholders'] changed ['kw_freq']
{'first_matches_changed': 18, 'single_changed': 26, 'multi_changed': 1, 'total': 27}

exec
/bin/bash -lc ".venv/bin/python - <<'PY'
from math import sqrt
from scipy.stats import binom, norm

def wilson(k,n,z=1.959963984540054):
 p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
for k,n,name in [(11,15,'current r+'),(5,12,'topic r-'),(8,12,'family r-'),(110,150,'10x observed r+'),(50,120,'10x topic r-'),(80,120,'10x family r-'),(90,150,'target r+'),(30,120,'target r-')]:
 print(name,k/n,wilson(k,n))
# One-sided exact rejection regions and powers: positive H0<=.60 vs alt .733; negative H0>=.25 and desire lower, alt .15/.10.
alpha=.05
# upper tail smallest k with P_H0(X>=k)<=alpha
for n,p0,p1,kind in [(150,.6,11/15,'upper'),(120,.25,.15,'lower'),(120,.25,.10,'lower'),(120,.25,5/12,'lower')]:
 if kind=='upper':
  crit=next(k for k in range(n+1) if binom.sf(k-1,n,p0)<=alpha)
  power=binom.sf(crit-1,n,p1)
 else:
  crit=max(k for k in range(n+1) if binom.cdf(k,n,p0)<=alpha)
  power=binom.cdf(crit,n,p1)
 print(n,p0,p1,kind,'crit',crit,'power',power)
PY" in /home/bmarti44/stencil-llm
 exited 1 in 0ms:
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
ModuleNotFoundError: No module named 'scipy'

exec
/bin/bash -lc ".venv/bin/python - <<'PY'
from math import sqrt,comb

def wilson(k,n,z=1.959963984540054):
 p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h

def cdf(k,n,p): return sum(comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))
def sf(km1,n,p): return 1-cdf(km1,n,p)
for k,n,name in [(11,15,'current r+'),(5,12,'topic r-'),(8,12,'family r-'),(110,150,'10x observed r+'),(50,120,'10x topic r-'),(80,120,'10x family r-'),(90,150,'target r+'),(30,120,'target r-')]: print(name,round(k/n,4),tuple(round(x,4) for x in wilson(k,n)))
for n,p0,p1,kind in [(150,.6,11/15,'upper'),(120,.25,.15,'lower'),(120,.25,.10,'lower'),(120,.25,5/12,'lower')]:
 if kind=='upper':
  crit=next(k for k in range(n+1) if sf(k-1,n,p0)<=.05); power=sf(crit-1,n,p1)
 else:
  crit=max(k for k in range(n+1) if cdf(k,n,p0)<=.05); power=cdf(crit,n,p1)
 print('power',n,p0,p1,kind,'crit',crit,'power',round(power,4))
PY" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
current r+ 0.7333 (0.4805, 0.891)
topic r- 0.4167 (0.1933, 0.6805)
family r- 0.6667 (0.3906, 0.8619)
10x observed r+ 0.7333 (0.6574, 0.7976)
10x topic r- 0.4167 (0.3324, 0.5061)
10x family r- 0.6667 (0.5783, 0.7447)
target r+ 0.6 (0.52, 0.675)
target r- 0.25 (0.1811, 0.3344)
power 150 0.6 0.7333333333333333 upper crit 101 power 0.958
power 120 0.25 0.15 lower crit 21 power 0.8163
power 120 0.25 0.1 lower crit 21 power 0.9962
power 120 0.25 0.4166666666666667 lower crit 21 power 0.0

web search: 
web search: site:arxiv.org selective prediction sample complexity risk coverage held out groups calibration paper ...
exec
/bin/bash -lc "nl -ba EVF-PLAN.md | sed -n '1,180p'; nl -ba scripts/e0_pilot.py | sed -n '1,180p'; nl -ba src/stencil/evf.py | sed -n '1,310p'; nl -ba scripts/b4_multiif.py | sed -n '1,260p'; nl -ba BENCH-WAVE-PLAN.md | sed -n '638,725p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	# EVF — Predictive Reactivation / Expected Value of Focus (the WHEN program)
     2	
     3	Authorized by Brian 2026-08-31 ("kill what is currently running and run
     4	this new program instead — red/green TDD, deterministic proof it's
     5	implemented correctly"), superseding the v4.5 confirmation mid-run (its
     6	partial records are retained untouched under results/qwen/
     7	b3-deficit-conf-s0/; the seed-0 sealed attempt is recorded ABANDONED-
     8	BY-RULING, not failed). Design: sol xhigh spec, results/
     9	b3-when-design-sol.md. BENCH-WAVE-PLAN.md machinery (data freezes,
    10	verifier vendoring, stats) is inherited; the single-turn stop-loss is
    11	superseded by this authorization.
    12	
    13	## The isolated bottleneck (established)
    14	
    15	Amplitude solved (2x force = 0 extra repairs). WHERE solved (K-perm
    16	kills the benefit). WHEN is open: the psi<tau attention trigger makes
    17	12 bad calls per 15 good; oracle WHEN ceiling +7.5pts vs +1.5 harvested.
    18	
    19	## Phase E0 — the decisive pilot probe (kill-fast; THIS phase only is
    20	authorized to run before its gate reports)
    21	
    22	Data: the recorded calibration discordants (t30-b3 vs base, 15 repairs
    23	+ 12 regressions) + concordant controls, from
    24	results/qwen/b3-deficit-cal/ per-item records. No new generation on any
    25	frozen evaluation stream; teacher-forced feature passes only.
    26	
    27	Per discordant row:
    28	1. Find the FIRST divergence token between the base and wave responses
    29	   (shared prefix p; the WHEN decision that mattered happened there).
    30	2. Teacher-force prompt+shared-prefix through the trunk once; cache at
    31	   the divergence point (and at 2 matched control points in concordant
    32	   rows): h20; decoder entropy, top-1 margin and their deltas over the
    33	   last 5 tokens; the frozen wave's rule-readout features (per-span q/k
    34	   scores: max, margin between top-2 spans); natural attention-mass
    35	   summary on the governing span (layers 20-27 mean).
    36	3. One additional weak-focus forward (the selected t30-b3 field scaled
    37	   to b=1.0 on the governing span) at the same prefix; cache
    38	   KL(P1||P0), JS divergence, and the obligation-token probability
    39	   shift (mean delta log-prob of the row's obligation-span tokens).
    40	4. Labels: repair=1, regression=0 (verifier-derived, offline).
    41	
    42	Probe: L2-regularized logistic regression (deterministic solver, fixed
    43	seed), leave-one-topic-out AND leave-one-constraint-family-out folds.
    44	
    45	GATE E0 (registered): held-out repair recall r+ >= 0.60 with
    46	regression fire-rate r- <= 0.25 on the 15/12 anatomy, in BOTH fold
    47	schemes. KILL immediately if: focused-vs-native divergence features are
    48	indistinguishable between repairs and regressions AND obligation/
    49	readout features add no held-out discrimination; or performance
    50	disappears under family holdout; or the probe works only via constraint
    51	type or response position.
    52	
    53	## Phase E1 (only if E0 passes; separate go)
    54	
    55	Recurrent obligation tracker (GRU 128/rule) + two-stage firing
    56	(eligibility screen -> one-token counterfactual -> calibrated
    57	lower-confidence-bound EVF > 0), bursts <= 4 tokens + refractory;
    58	labels from offline verifier-scored counterfactual rollouts; safe-dose
    59	interval requirement (a BROAD non-harmful tau/threshold plateau, not
    60	one winning scalar) and behavioral gates per sol's spec sections
    61	(offline discrimination, safe-dose, behavioral) — registered in full
    62	before any E1 training run.
    63	
    64	## Process
    65	
    66	Red/green TDD throughout: every component gets a failing test first;
    67	deterministic proof = bitwise-identical feature extraction across two
    68	runs, fixed-seed probe fits, and fixture-exact tests for divergence
    69	finding and label derivation. Reviews: sol + fable on the E0 result
    70	before any E1 work. Playbook governs (per-item records from the first
    71	row of anything evaluative; git add -f for results; smoke before
    72	sealing).
     1	# ruff: noqa
     2	"""EVF Phase E0 — the registered kill-fast pilot (EVF-PLAN.md).
     3	Extracts the registered feature set at each discordant divergence point
     4	(15 repairs / 12 regressions from the t30-b3 calibration anatomy),
     5	fits the deterministic logistic probe, and evaluates the REGISTERED
     6	GATE under BOTH fold schemes: leave-one-TOPIC-out and leave-one-
     7	FAMILY-out (family = first-listed constraint's family; disclosed).
     8	GATE: r+ >= 0.60 AND r- <= 0.25 in BOTH schemes. Per-item features
     9	saved (playbook)."""
    10	import json, sys
    11	from pathlib import Path
    12	ROOT = Path(__file__).resolve().parent.parent
    13	sys.path.insert(0, str(ROOT / "src"))
    14	from stencil import determinism  # noqa: F401
    15	from stencil.evf import extract_features, gate_eval, load_anatomy, load_model
    16	
    17	FAMILY = {"caps": "change_case", "lower": "change_case", "kw_exist": "keywords",
    18	          "kw_freq": "keywords", "kw_forbid": "keywords", "n_words_min": "length",
    19	          "n_words_max": "length", "n_sent": "length", "bullets": "format",
    20	          "title": "format", "json_fmt": "format", "placeholders": "content",
    21	          "postscript": "content", "two_resp": "combination"}
    22	
    23	m, tok, ctrl = load_model(ROOT)
    24	anat = load_anatomy(ROOT, arm="t30-b3")
    25	feats, labels, topics, families, items = [], [], [], [], []
    26	for it in anat:
    27	    f = extract_features(m, tok, ctrl, it)
    28	    feats.append(f); labels.append(it["label"])
    29	    topics.append(it["row"]["topic"])
    30	    families.append(FAMILY[it["row"]["combo"][0]])
    31	    items.append({"i": it["i"], "label": it["label"], "topic": it["row"]["topic"],
    32	                  "family": FAMILY[it["row"]["combo"][0]], "features": f})
    33	    print(f"{it['i']}: label {it['label']} kl {f['kl_focus']:.4f} ob {f['obligation_shift']:.4f}", flush=True)
    34	
    35	res_topic = gate_eval(feats, labels, topics)
    36	res_family = gate_eval(feats, labels, families)
    37	gate = {"topic_folds": res_topic, "family_folds": res_family,
    38	        "PASS": bool(res_topic["r_plus"] >= 0.60 and res_topic["r_minus"] <= 0.25
    39	                     and res_family["r_plus"] >= 0.60 and res_family["r_minus"] <= 0.25)}
    40	out = {"items": items, "gate": gate}
    41	(ROOT / "results" / "qwen" / "e0-pilot.json").write_text(json.dumps(out, indent=1))
    42	print(json.dumps(gate, indent=1))
     1	# ruff: noqa: E501
     2	"""EVF Phase E0 pilot library (EVF-PLAN.md; red/green TDD).
     3	
     4	Pure-python probe machinery is dependency-free and deterministic by
     5	construction (zero-init logistic GD, fixed iteration count). Feature
     6	extraction is a teacher-forced pass through the frozen trunk plus one
     7	weak-focus counterfactual forward — deterministic, proven bitwise by
     8	tests/test_evf_pilot.py.
     9	"""
    10	import json
    11	import math
    12	import random
    13	from pathlib import Path
    14	
    15	TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    16	WAVE_LAYERS = range(20, 28)
    17	
    18	
    19	def first_divergence(tok, a, b):
    20	    """index of the first differing TOKEN between texts a and b
    21	    (None if their token id sequences are identical)."""
    22	    ia, ib = tok.encode(a).ids, tok.encode(b).ids
    23	    n = min(len(ia), len(ib))
    24	    for k in range(n):
    25	        if ia[k] != ib[k]:
    26	            return k
    27	    if len(ia) == len(ib):
    28	        return None
    29	    return n
    30	
    31	
    32	def _load_records(root, arm):
    33	    d = Path(root) / "results" / "qwen" / "b3-deficit-cal"
    34	    base, wave = {}, {}
    35	    for p in d.glob("base-*.json"):
    36	        r = json.loads(p.read_text())
    37	        base[r["i"]] = r
    38	    for p in d.glob(f"{arm}-*.json"):
    39	        r = json.loads(p.read_text())
    40	        wave[r["i"]] = r
    41	    rows = [json.loads(line) for line in open(Path(root) / "data" / "b3" / "cal-v45.jsonl")]
    42	    return base, wave, rows
    43	
    44	
    45	def load_anatomy(root, arm="t30-b3"):
    46	    """discordant rows (repair label=1 / regression label=0), joined."""
    47	    base, wave, rows = _load_records(root, arm)
    48	    out = []
    49	    for i in sorted(base):
    50	        b, w = base[i], wave[i]
    51	        if b["adherent"] == w["adherent"]:
    52	            continue
    53	        out.append({"row": rows[i], "i": i,
    54	                    "base_response": b["response"], "wave_response": w["response"],
    55	                    "base_adherent": b["adherent"], "wave_adherent": w["adherent"],
    56	                    "label": int(w["adherent"])})
    57	    return out
    58	
    59	
    60	def load_controls(root, arm="t30-b3", n=30, seed=11):
    61	    """seeded sample of concordant rows (matched control points)."""
    62	    base, wave, rows = _load_records(root, arm)
    63	    conc = [i for i in sorted(base) if base[i]["adherent"] == wave[i]["adherent"]]
    64	    rng = random.Random(seed)
    65	    pick = sorted(rng.sample(conc, n))
    66	    return [{"row": rows[i], "i": i,
    67	             "base_response": base[i]["response"], "wave_response": wave[i]["response"],
    68	             "base_adherent": base[i]["adherent"], "wave_adherent": wave[i]["adherent"]}
    69	            for i in pick]
    70	
    71	
    72	def load_model(root):
    73	    import torch
    74	    from tokenizers import Tokenizer
    75	
    76	    from stencil import determinism  # noqa: F401
    77	    from stencil.qwen3 import Qwen3
    78	    from stencil.wave import WaveController
    79	    root = Path(root)
    80	    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    81	    m = Qwen3()
    82	    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    83	    m = m.to(torch.bfloat16).cuda().eval()
    84	    ctrl = WaveController(beta_max=1.0).cuda()
    85	    ctrl.load_state_dict(torch.load(root / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    86	    return m, tok, ctrl.eval()
    87	
    88	
    89	def constraint_spans_of(tok, prompt):
    90	    ptxt = TMPL.format(p=prompt)
    91	    enc = tok.encode(ptxt)
    92	    spans, start = [], 0
    93	    while True:
    94	        i = ptxt.find("Constraint:", start)
    95	        if i < 0:
    96	            break
    97	        j = ptxt.find("Constraint:", i + 1)
    98	        end = j if j > 0 else ptxt.find("<|im_end|>", i)
    99	        toks = [ti for ti, (a, b) in enumerate(enc.offsets) if a < end and b > i]
   100	        if toks:
   101	            spans.append((toks[0], toks[-1] + 1))
   102	        start = i + 1
   103	    return spans
   104	
   105	
   106	def extract_features(m, tok, ctrl, item, probe_pos=None):
   107	    """registered E0 feature set at the divergence point (or probe_pos)."""
   108	    import torch
   109	    import torch.nn.functional as F
   110	    row = item["row"]
   111	    k = first_divergence(tok, item["base_response"], item["wave_response"])
   112	    shared = tok.encode(item["base_response"]).ids[: (k if k is not None else 0)]
   113	    if probe_pos is not None:
   114	        shared = shared[:probe_pos]
   115	    p_ids = tok.encode(TMPL.format(p=row["prompt"])).ids
   116	    P = len(p_ids)
   117	    ids = p_ids + shared
   118	    toks = torch.tensor([ids], device="cuda")
   119	    spans = constraint_spans_of(tok, row["prompt"])
   120	    with torch.no_grad():
   121	        logits, h20 = m(toks, capture_hidden=20)
   122	        lp = F.log_softmax(logits[0, -6:].float(), dim=-1)
   123	        probs = lp.exp()
   124	        ents = (-(probs * lp).sum(-1)).tolist()
   125	        tops = probs.topk(2, dim=-1).values
   126	        margins = (tops[:, 0] - tops[:, 1]).tolist()
   127	        # rule readout via the frozen wave's q/k
   128	        q = F.normalize(ctrl.W_q(h20[0, -1:].float()), dim=-1)
   129	        kk = F.normalize(ctrl.W_k(h20[0, :P].float()), dim=-1)
   130	        scores = (q @ kk.T)[0]
   131	        span_scores = sorted((float(scores[a:b].mean()) for a, b in spans), reverse=True) or [0.0]
   132	        best_span = max(spans, key=lambda ab: float(scores[ab[0]:ab[1]].mean())) if spans else (0, 1)
   133	        # natural attention mass on the governing span (layers 20-27, last row)
   134	        pm = torch.zeros(len(ids), dtype=torch.bool, device="cuda")
   135	        pm[best_span[0]:best_span[1]] = True
   136	        sink = {}
   137	        m(toks, attn_probe=(pm, sink))
   138	        attn_mass = sum(sink.values()) / len(sink)
   139	        # weak-focus counterfactual: b=1.0 on the governing span, last row
   140	        T = len(ids)
   141	        bias = torch.zeros(T, T, device="cuda")
   142	        bias[-1, best_span[0]:best_span[1]] = 1.0
   143	        l1 = m(toks, attn_bias={L: bias for L in WAVE_LAYERS})[0, -1].float()
   144	        p0 = F.log_softmax(logits[0, -1].float(), dim=-1)
   145	        p1 = F.log_softmax(l1, dim=-1)
   146	        kl = float((p1.exp() * (p1 - p0)).sum())
   147	        mix = torch.logsumexp(torch.stack([p0, p1]), dim=0) - math.log(2)
   148	        js = 0.5 * float((p0.exp() * (p0 - mix)).sum()) + 0.5 * float((p1.exp() * (p1 - mix)).sum())
   149	        ob_ids = sorted({tid for kkey, sps in row["obligation_spans"].items()
   150	                         for a, b in sps
   151	                         for tid in tok.encode(row["canonical"][a:b]).ids})
   152	        ob_shift = float((p1[ob_ids] - p0[ob_ids]).mean()) if ob_ids else 0.0
   153	    return {
   154	        "entropy": float(ents[-1]), "margin": float(margins[-1]),
   155	        "entropy_delta5": float(ents[-1] - ents[0]), "margin_delta5": float(margins[-1] - margins[0]),
   156	        "readout_top": span_scores[0],
   157	        "readout_margin": span_scores[0] - (span_scores[1] if len(span_scores) > 1 else 0.0),
   158	        "attn_mass_span": float(attn_mass),
   159	        "kl_focus": kl, "js_focus": js, "obligation_shift": ob_shift,
   160	        "rel_pos": len(shared) / max(1, len(shared) + 32),
   161	    }
   162	
   163	
   164	# --- deterministic probe ----------------------------------------------------
   165	
   166	def _standardize(feats):
   167	    keys = sorted(feats[0])
   168	    mu = {k: sum(f[k] for f in feats) / len(feats) for k in keys}
   169	    sd = {k: (sum((f[k] - mu[k]) ** 2 for f in feats) / len(feats)) ** 0.5 or 1.0 for k in keys}
   170	    return keys, mu, sd
   171	
   172	
   173	def fit_probe(feats, labels, seed=0, l2=1.0, iters=500, lr=0.1):
   174	    """zero-init logistic GD — deterministic (seed kept for signature)."""
   175	    keys, mu, sd = _standardize(feats)
   176	    X = [[(f[k] - mu[k]) / sd[k] for k in keys] for f in feats]
   177	    w = [0.0] * len(keys)
   178	    b = 0.0
   179	    n = len(X)
   180	    for _ in range(iters):
   181	        gw = [l2 * wi / n for wi in w]
   182	        gb = 0.0
   183	        for x, y in zip(X, labels):
   184	            z = sum(wi * xi for wi, xi in zip(w, x)) + b
   185	            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
   186	            e = p - y
   187	            for j in range(len(w)):
   188	                gw[j] += e * x[j] / n
   189	            gb += e / n
   190	        w = [wi - lr * gi for wi, gi in zip(w, gw)]
   191	        b -= lr * gb
   192	    return {"keys": keys, "mu": mu, "sd": sd, "w": w, "b": b}
   193	
   194	
   195	def predict(model, f):
   196	    z = sum(wi * (f[k] - model["mu"][k]) / model["sd"][k]
   197	            for wi, k in zip(model["w"], model["keys"])) + model["b"]
   198	    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
   199	
   200	
   201	def gate_eval(feats, labels, groups, seed=0, threshold=0.5):
   202	    """leave-one-group-out CV; returns held-out repair recall (r_plus)
   203	    and regression fire-rate (r_minus)."""
   204	    preds = {}
   205	    for g in sorted(set(groups)):
   206	        tr = [i for i in range(len(feats)) if groups[i] != g]
   207	        te = [i for i in range(len(feats)) if groups[i] == g]
   208	        if not tr or not te:
   209	            continue
   210	        model = fit_probe([feats[i] for i in tr], [labels[i] for i in tr], seed=seed)
   211	        for i in te:
   212	            preds[i] = predict(model, feats[i]) >= threshold
   213	    pos = [i for i in preds if labels[i] == 1]
   214	    neg = [i for i in preds if labels[i] == 0]
   215	    r_plus = sum(preds[i] for i in pos) / len(pos) if pos else 0.0
   216	    r_minus = sum(preds[i] for i in neg) / len(neg) if neg else 1.0
   217	    return {"r_plus": r_plus, "r_minus": r_minus, "n_pos": len(pos), "n_neg": len(neg)}
     1	# ruff: noqa
     2	"""Multi-IF English runner (EXPLORATORY, registered v3.1/v3.2): all 909
     3	conversations x 3 turns = 2727 turns; each arm consumes ITS OWN prior
     4	responses; history serialization = prior turns as user/assistant blocks
     5	WITHOUT think tags, final turn opens with the pinned assistant opener;
     6	turn t scored with turn t's instruction list/kwargs (the dataset's
     7	lists are already cumulative); per-turn-index (n=909) + pooled
     8	(n=2727) four metrics. Scoring seed pin: random.seed(stable hash of
     9	"key:turn") per scored turn (mirror of the IFEval per-row pin).
    10	Atomic per-conversation records; hash-verified resume.
    11	
    12	v4.1 hardening: CLOSED three-arm table (base, wave-s0, proxy-s0)
    13	with registered controller hashes; full provenance pin set; real 300s
    14	deadline with timeout recorded. SMOKE=<n conversations> only.
    15	"""
    16	import json
    17	import hashlib
    18	import os
    19	import sys
    20	import time
    21	from pathlib import Path
    22	
    23	ROOT = Path(__file__).resolve().parent.parent
    24	sys.path.insert(0, str(ROOT / "src"))
    25	from stencil import determinism  # noqa: F401
    26	import torch
    27	from tokenizers import Tokenizer
    28	
    29	from stencil.bench import EOS, MAX_NEW, aggregate, make_wave_bias_fn, provenance_pins
    30	from stencil.qwen3 import KVCache, Qwen3
    31	from stencil.wave import WaveController
    32	
    33	sys.path.insert(0, str(ROOT / "vendor"))
    34	import langdetect
    35	
    36	langdetect.DetectorFactory.seed = 0
    37	from ifeval import utils as ifeval_utils  # noqa: E402
    38	
    39	SMOKE = int(os.environ.get("SMOKE", "0"))
    40	OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    41	TIMEOUT_S = 300
    42	
    43	
    44	def _registered_sha(record):
    45	    return json.loads((ROOT / "results" / "qwen" / record).read_text())["selected_sha256"]
    46	
    47	
    48	def arms_table():
    49	    """v4.5 Multi-IF arms: base + DEFICIT-wave (v4.4 seed-0 Wq/Wk,
    50	    calibration-selected tau/b_max) + static-x0.25 comparator (same
    51	    controller; descriptive). Controller hash bound to the committed
    52	    training record (equivalent to a literal: the record is tracked)."""
    53	    sha = _registered_sha("b3-ce-s0.json")
    54	    return [("base", None, None),
    55	            ("deficit-wave-s0", "results/qwen/b3-ce-s0.pt", sha),
    56	            ("static25-wave-s0", "results/qwen/b3-ce-s0.pt", sha)]
    57	
    58	
    59	def seed_of(key, turn):
    60	    return int(hashlib.sha256(f"{key}:{turn}".encode()).hexdigest()[:8], 16)
    61	
    62	
    63	def turn_doc(row, t):
    64	    """(prompt_content, instruction_id_list, kwargs list) for turn t (1-3)."""
    65	    p = json.loads(row[f"turn_{t}_prompt"])["content"]
    66	    ids = json.loads(row[f"turn_{t}_instruction_id_list"])
    67	    kws = [json.loads(k) for k in json.loads(row[f"turn_{t}_kwargs"])]
    68	    return p, ids, kws
    69	
    70	
    71	def score_turn(row, t, response):
    72	    import random
    73	    p, ids, kws = turn_doc(row, t)
    74	    random.seed(seed_of(row["key"], t))
    75	    doc = {"key": 0, "prompt": p, "instruction_id_list": ids, "kwargs": kws}
    76	    return ifeval_utils.process_results(doc, [response])
    77	
    78	
    79	def user_turn_spans(history_text, enc):
    80	    """candidate spans for the deficit gate on Multi-IF: each USER
    81	    message's token span (instructions live in user turns and drift out
    82	    of focus across the conversation — the registered long-horizon
    83	    setting). The learned q/k selects among them per step."""
    84	    spans, start = [], 0
    85	    while True:
    86	        i = history_text.find("<|im_start|>user\n", start)
    87	        if i < 0:
    88	            break
    89	        j = history_text.find("<|im_end|>", i)
    90	        if j < 0:
    91	            break
    92	        toks = [ti for ti, (a, b) in enumerate(enc.offsets) if a < j and b > i]
    93	        if toks:
    94	            spans.append((toks[0], toks[-1] + 1))
    95	        start = j + 1
    96	    return spans
    97	
    98	
    99	def gen(m, tok, ctrl, history_text, mode, tau=None, b_max=None):
   100	    """cached greedy over an explicit conversation string; mode:
   101	    'base' | 'deficit' (registered adapter, user-turn spans) |
   102	    'static25' (v4.4 bias x0.25, descriptive comparator)."""
   103	    import time as _t
   104	
   105	    from stencil.bench import WAVE_LAYERS, make_deficit_hook, make_wave_bias_fn
   106	    ids = tok.encode(history_text).ids
   107	    enc = tok.encode(history_text)
   108	    cache = KVCache()
   109	    out = []
   110	    state = {}
   111	    P = len(ids)
   112	    hook = None
   113	    if mode == "deficit":
   114	        spans = user_turn_spans(history_text, enc)
   115	        state["cache_len"] = 0
   116	        hook = make_deficit_hook(ctrl, state, spans, tau, b_max)
   117	    elif mode == "static25":
   118	        inner = make_wave_bias_fn(ctrl, state)
   119	        def bias_fn(h20, Pp, past):
   120	            row = inner(h20, Pp, past)
   121	            return None if row is None else row * 0.25
   122	
   123	    t0 = _t.monotonic()
   124	    timed_out = False
   125	    with torch.no_grad():
   126	        if mode == "deficit":
   127	            logits = m(torch.tensor([ids], device="cuda"), cache=cache, deficit_hook=hook)
   128	        elif mode == "static25":
   129	            def bh(past):
   130	                def h(h20):
   131	                    row = bias_fn(h20, P, past)
   132	                    return None if row is None else {L: row for L in WAVE_LAYERS}
   133	                return (20, h)
   134	            logits = m(torch.tensor([ids], device="cuda"), cache=cache, bias_hook=bh(0))
   135	        else:
   136	            logits = m(torch.tensor([ids], device="cuda"), cache=cache)
   137	        nxt = int(logits[0, -1].argmax())
   138	        while nxt not in EOS and len(out) < MAX_NEW:
   139	            if _t.monotonic() - t0 > TIMEOUT_S:
   140	                timed_out = True
   141	                break
   142	            out.append(nxt)
   143	            if mode == "deficit":
   144	                state["cache_len"] = cache.length
   145	                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, deficit_hook=hook)
   146	            elif mode == "static25":
   147	                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache, bias_hook=bh(cache.length))
   148	            else:
   149	                logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache)
   150	            nxt = int(logits[0, -1].argmax())
   151	    return tok.decode(out), len(out), len(out) >= MAX_NEW, timed_out
   152	
   153	
   154	def run_arm(m, tok, rows, arm_name, ctrl, meta, mode):
   155	    outdir = ROOT / "results" / "qwen" / f"b4-multiif-{arm_name}"
   156	    outdir.mkdir(parents=True, exist_ok=True)
   157	    meta_p = outdir / "meta.json"
   158	    if meta_p.exists():
   159	        assert json.loads(meta_p.read_text()) == meta, "resume provenance mismatch"
   160	    else:
   161	        tmp = meta_p.with_suffix(".tmp")
   162	        tmp.write_text(json.dumps(meta, indent=1))
   163	        tmp.rename(meta_p)
   164	
   165	    per_turn = {1: [], 2: [], 3: []}
   166	    for ci, row in enumerate(rows):
   167	        rec_p = outdir / f"conv-{ci:03d}.json"
   168	        if rec_p.exists():
   169	            rec = json.loads(rec_p.read_text())
   170	            for t in (1, 2, 3):
   171	                per_turn[t].append(rec["scores"][str(t)])
   172	            continue
   173	        history = ""
   174	        rec = {"ci": ci, "key": row["key"], "scores": {}, "responses": {}, "gen": {}}
   175	        for t in (1, 2, 3):
   176	            p, _, _ = turn_doc(row, t)
   177	            history += f"<|im_start|>user\n{p}<|im_end|>\n"
   178	            text, n, trunc, timeout = gen(m, tok, ctrl, history + OPENER, mode,
   179	                                          tau=TAU, b_max=BMAX)
   180	            rec["responses"][str(t)] = text
   181	            rec["gen"][str(t)] = {"n": n, "truncated": bool(trunc), "timeout": bool(timeout)}
   182	            rec["scores"][str(t)] = score_turn(row, t, text)
   183	            per_turn[t].append(rec["scores"][str(t)])
   184	            history += f"<|im_start|>assistant\n{text}<|im_end|>\n"
   185	        tmp = rec_p.with_suffix(".tmp")
   186	        tmp.write_text(json.dumps(rec, ensure_ascii=False))
   187	        tmp.rename(rec_p)
   188	        if ci % 20 == 0:
   189	            print(f"[{arm_name}] {ci}/{len(rows)}", flush=True)
   190	    summary = {"arm": arm_name, **meta}
   191	    for t in (1, 2, 3):
   192	        summary[f"turn{t}"] = aggregate(per_turn[t])
   193	    summary["pooled"] = aggregate(per_turn[1] + per_turn[2] + per_turn[3])
   194	    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
   195	    print(f"[{arm_name}] " + json.dumps({k: v for k, v in summary.items() if k.startswith(("turn", "pooled"))}))
   196	
   197	
   198	def main():
   199	    global ARMS, TAU, BMAX
   200	    ARMS = arms_table()
   201	    cal = json.loads((ROOT / "results" / "qwen" / "b3-deficit-cal.json").read_text())
   202	    sel = cal["results"][cal["selected"]]
   203	    TAU, BMAX = sel["tau"], sel["b_max"]
   204	    man = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
   205	    data_p = ROOT / "data" / "bench" / "multiif_en.jsonl"
   206	    data_sha = hashlib.sha256(data_p.read_bytes()).hexdigest()
   207	    assert data_sha == man["converted_sha256"]["multiif_en.jsonl"]
   208	    pins = provenance_pins(ROOT, extra_files=[p for _, p, _ in ARMS if p]
   209	                           + ["data/bench/multiif_en.jsonl", "scripts/b4_multiif.py"])
   210	    for name, path, want in ARMS:
   211	        if path is not None:
   212	            assert pins[path] == want, f"controller hash mismatch: {name}"
   213	
   214	    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
   215	    m = Qwen3()
   216	    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
   217	    m = m.to(torch.bfloat16).cuda().eval()
   218	    rows = [json.loads(line) for line in open(data_p)]
   219	    assert len(rows) == 909
   220	    if SMOKE:
   221	        rows = rows[:SMOKE]
   222	    for name, path, want in ARMS:
   223	        ctrl = None
   224	        if path is not None:
   225	            ctrl = WaveController(beta_max=1.0).cuda()
   226	            ctrl.load_state_dict(torch.load(ROOT / path, map_location="cpu"))
   227	            ctrl = ctrl.eval()
   228	        mode = "base" if path is None else ("deficit" if name.startswith("deficit") else "static25")
   229	        meta = {"arm": name, "ctrl": path or "none", "ctrl_sha256": (want or "none"),
   230	                "mode": mode, "tau": TAU, "b_max": BMAX,
   231	                "pins": pins, "timeout_s": TIMEOUT_S}
   232	        run_arm(m, tok, rows, name, ctrl, meta, mode)
   233	
   234	
   235	if __name__ == "__main__":
   236	    main()
   638	## v4.5 — deficit-triggered wave (THE FINAL single-turn rescue;
   639	registered per sol's results review, 2026-08-31)
   640	
   641	Motivating evidence (exploratory, scoped): dose sweep on v4.4 wave-s0
   642	(x1.0 0.7959 / x0.5 0.8214 / x0.25 0.8571 vs base 0.8418 on dev-v43;
   643	x0.25 beats base by +1.5pts but n=196 cannot distinguish +1.5 from
   644	+2.0 — best-case paired p=0.125; sweep numbers pending fable's
   645	independent reproduction). Research prior: SpotLight (2505.12025)
   646	deficit-triggered steering with positive IFEval deltas at 3-8B.
   647	
   648	MECHANISM (implemented, battery 4/4 green): frozen v4.4 Wq/Wk select
   649	the governing Constraint: span per generated row (first-index
   650	tie-break; no span -> no intervention); per biased layer/head, measure
   651	natural post-softmax mass psi on the span; psi >= tau -> ZERO bias
   652	(bitwise base attention); else uniform span bias
   653	min(b_max, logit(tau) - logit(psi)) (exact odds correction). Every
   654	intervention logged (span, score, per-item records).
   655	
   656	CALIBRATION (one shot): frozen tau grid {0.10, 0.20, 0.30, 0.45} x
   657	b_max {3.0, 6.0} on cal-v45 (200 rows, seed 5, prompt-disjoint);
   658	select by adherence, ties -> LOWER intervention rate; base cal run as
   659	reference. No recalibration after confirmation begins.
   660	
   661	CONFIRMATION (one shot): conf-v45 (512 rows, seed 7, dev-topic,
   662	prompt-disjoint from everything). GATE: deficit-wave(seed-0 Wq/Wk)
   663	>= base + 2.0pts strict adherence AND one-sided exact McNemar p<0.05
   664	AND no excess timeouts/truncations; per-row records + raw discordants
   665	saved. If seed 0 passes, REPLICATE with seed-1 Wq/Wk (same tau/b_max,
   666	no re-selection); BOTH must pass before sealed IFEval.
   667	
   668	STOP-LOSS (registered): this is recipe iteration 3 and the LAST
   669	single-turn rescue. One calibration grid, one confirmation block, no
   670	recalibration/retraining/fallbacks after seeing confirmation. Failure
   671	CLOSES the single-turn synthetic/IFEval wave line (honest negative
   672	with the full autopsy chain already recorded); token-aware contrast or
   673	GRPO training would be a separately authorized program. The x0.25
   674	static dose is carried as a descriptive comparator only.
   675	
   676	### v4.5 addendum — registered ablation + a disclosure (Brian approved,
   677	2026-08-31)
   678	
   679	- LEARNED-vs-HEURISTIC ADDRESSING ABLATION (registered BEFORE the
   680	  confirmation runs; executed AFTER confirmation, outside the gate,
   681	  descriptive): rerun the confirmation block with the SAME deficit
   682	  trigger and selected (tau, b_max) but span selection replaced by the
   683	  FIRST Constraint: sentence heuristic (no learned q/k). Claim rules:
   684	  if learned addressing beats the heuristic (paired), the wave's
   685	  learned WHERE earns its keep on this task; if not, the single-turn
   686	  claim is scoped to "SpotLight-class control law", and the wave's
   687	  distinctive contribution remains the out-of-reach regime (W3) +
   688	  focus readout/transplant results. Not a gate; no stop-loss impact.
   689	- DISCLOSURE: the calibration runner's interventions_per_token logs
   690	  span-SELECTION opportunities (always 1.0 when spans exist), not
   691	  actual per-head bias firings (those live inside the attention
   692	  blocks). The registered tie-break (lower intervention rate) is
   693	  therefore effective only via a post-hoc replay if an exact adherence
   694	  tie occurs; otherwise selection is by adherence alone. Recorded
   695	  before seeing full grid results.
   696	
   697	### v4.5 Multi-IF execution (Brian-directed, 2026-08-31; EXPLORATORY as
   698	registered): the long-horizon test runs REGARDLESS of the single-turn
   699	confirmation outcome — it is the scope-hypothesis test (instructions
   700	drift out of focus across turns; published models decay 88->71).
   701	Arms (closed table, controller bound to the committed v4.4 seed-0
   702	training record's selected_sha256 9d43315b...): base;
   703	deficit-wave-s0 (calibration-selected tau/b_max; candidate spans =
   704	each USER message's token span, learned q/k selects per step — the
   705	natural generalization when instructions are not phrase-marked);
   706	static25-wave-s0 (v4.4 bias x0.25, descriptive comparator). All 909
   707	conversations x 3 turns; per-turn-index + pooled metrics; no gate.
   708	Ordering: after the single-turn confirmation (+ replication if it
   709	passes) releases the GPU.

exec
/bin/bash -lc ".venv/bin/python - <<'PY'
from math import sqrt
for A in [.706,.683,.667]:
 n1,n0=15,12; q1=A/(2-A);q2=2*A*A/(1+A); se=sqrt((A*(1-A)+(n1-1)*(q1-A*A)+(n0-1)*(q2-A*A))/(n1*n0)); print(A,se,(max(0,A-1.96*se),min(1,A+1.96*se)))
PY" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
0.706 0.10035097091525327 (0.5093120970061036, 0.9026879029938963)
0.683 0.10308092343379094 (0.4809613900697698, 0.8850386099302303)
0.667 0.10478808882487625 (0.4616153459032426, 0.8723846540967575)

exec
/bin/bash -lc "find results/qwen -maxdepth 2 -type f -path '*b4-multiif*' -printf '%h/%f\\n' | sort | tail -n 30; tail -n 30 results/logs/b4-multiif.log 2>/dev/null || true" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
results/qwen/b4-multiif-base/conv-000.json
results/qwen/b4-multiif-base/conv-001.json
results/qwen/b4-multiif-base/conv-002.json
results/qwen/b4-multiif-base/conv-003.json
results/qwen/b4-multiif-base/conv-004.json
results/qwen/b4-multiif-base/conv-005.json
results/qwen/b4-multiif-base/conv-006.json
results/qwen/b4-multiif-base/conv-007.json
results/qwen/b4-multiif-base/meta.json
Uninstalled 1 package in 0.30ms
Installed 1 package in 2ms
[base] 0/909

codex
## Bottom line

E0 stays killed. The failure was real under its registered test.

But E0 also contained genuine design flaws that justify a new, differently identified experiment—not an E0 rerun:

1. It assigned a whole-response treatment outcome to the first output divergence, even though the deficit policy intervened repeatedly.
2. Its family holdout was mis-keyed: it grouped by the first listed constraint, which was the constraint whose verifier changed in only 18/27 discordants.
3. The registered concordant controls were never used.
4. `obligation_shift` used canonical-answer information unavailable to an autonomous inference-time gate.

The best correction is therefore not “collect 10× more copies of E0.” It is a fresh causal moment dataset: at a fixed prefix, branch one deterministic rollout with a single focus burst and one without it, then label that exact decision helpful, harmful, or neutral.

I would register the design now but wait for Multi-IF before spending GPU on it.

## A. Real E0 design flaws

### 1. The label was attached to the wrong moment

The registration asserts that the first divergence is “the WHEN decision that mattered” ([EVF-PLAN.md](/home/bmarti44/stencil-llm/EVF-PLAN.md:27)). That is not established.

`load_anatomy()` labels an entire base-vs-wave response pair by final adherence ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:45)), while `extract_features()` inspects only the first divergence prefix ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:106)). The deficit policy acted across the generation, so the final repair or regression could have been caused by:

- an earlier intervention that changed latent trajectory before visible divergence;
- several interventions jointly;
- an intervention much later than first divergence;
- accumulated attention starvation rather than the particular divergence decision.

This is the largest unanticipated flaw. E0 tested “can first-divergence state predict which complete policy eventually won?” It did not cleanly test “should I press now?”

### 2. The family-holdout grouping was wrong for 9/27 rows

The script defines family from `combo[0]` ([e0_pilot.py](/home/bmarti44/stencil-llm/scripts/e0_pilot.py:30)). I re-ran the individual vendored verifiers on both responses:

- 26/27 discordants changed exactly one constraint verdict.
- One changed two.
- The changed constraint was the first listed constraint in only 18/27 cases.

Examples:

- Item 44 was grouped as `format` because `bullets` came first, but the changed verifier was `kw_exist`.
- Item 132 was grouped as `change_case`, but the changed verifier was `placeholders`.
- Item 170 was grouped as `keywords`, but the changed verifier was `n_words_max`.

Therefore the reported leave-one-family-out result is reproducible, but it is not actually leave-out-the-causal-family. This can create leakage and instability in either direction. It does not erase the registered failure, but a successor must group by the verifier outcome that changed—or use all active families as a multilabel group.

### 3. Concordant controls were specified but omitted

The plan explicitly included matched concordant controls ([EVF-PLAN.md](/home/bmarti44/stencil-llm/EVF-PLAN.md:22)), and `load_controls()` exists ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:60)). But `e0_pilot.py` never calls it; the fitted and evaluated dataset is only the 27 discordants.

That omission matters because a real gate sees mostly neutral opportunities. A classifier trained only on repairs versus regressions cannot estimate:

- its overall firing rate;
- compute wasted on neutral moments;
- whether it fires indiscriminately outside outcome-changing cases;
- its deployed positive predictive value.

A successor needs three labels: helpful, harmful, and neutral.

### 4. `obligation_shift` was not a deployable obligation-state signal

The feature uses token IDs extracted from `row["canonical"]` and `row["obligation_spans"]` ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:149)). It then averages the one-step log-probability shift over the union of those token types.

Problems:

- The canonical response is unavailable at inference.
- It pools already-satisfied, future, and currently irrelevant obligations.
- It discards order and multiplicity.
- It does not ask whether the next several tokens make progress.
- A token appearing anywhere in an obligation edit becomes “desirable now.”

It was acceptable as an oracle diagnostic. It cannot be an input to a fully autonomous deployed gate.

## B. What a properly powered correction should test

### Do not manufacture 270 more whole-policy discordants

The current discordant yield was 27/200 = 13.5%. At the same rate, 2,000 fresh rows would yield approximately 270 discordants, with ordinary sampling variation of roughly ±30.

But 270 examples constructed the same way would only make the attribution error more precise.

### Manufacture causal decision examples instead

For each eligible moment on a fixed trajectory:

1. Freeze the exact prompt, generated prefix, selected span, KV state, dose, and rollout policy.
2. Branch:
   - `A=0`: no focus burst;
   - `A=1`: exactly one registered focus burst, then no further treatment.
3. Continue both deterministically to a verifier-resolvable endpoint.
4. Score the full per-constraint vector, parse/truncation cost, and total utility.
5. Label:
   - helpful: \(\Delta U>0\);
   - harmful: \(\Delta U<0\);
   - neutral: \(\Delta U=0\).
6. Split by session/topic and actual changed constraint family. Never split moments from one row across train and evaluation.

That is a deterministic intervention experiment. It directly supplies the individualized treatment effect the gate is supposed to predict. Modern policy-learning language frames this as learning which localized intervention has positive expected benefit, rather than predicting outcomes under an entire confounded policy. [Localized intervention policy learning](https://proceedings.mlr.press/v238/marmarelis24a.html)

Offline verifier labels are legitimate supervision, provided the writeup says exactly that. They cease to be “fully general” unless the learned signal transfers to held-out verifier families and to settings without those checkers.

### Is 270 enough for 11 features?

Only barely for exploration; not for development and decisive validation together.

With the observed 15:12 ratio, 270 discordants gives roughly 150 helpful and 120 harmful cases:

- 120 minority events / 11 slopes = 10.9 events per feature.
- That barely clears the old ten-events-per-variable heuristic.
- It ignores family/topic clustering.
- It leaves no independent confirmation set if all 270 are used for training and grouped CV.

Prediction-model sample-size work explicitly warns that the ten-events heuristic is not a guarantee; required size depends on signal strength, calibration, shrinkage, and outcome prevalence. One published example needed 461 observations for ten predictors and a 30% outcome rate to control prediction error. [Riley et al., BMJ](https://www.bmj.com/content/368/bmj.m441) Small-sample cross-validation can remain substantially biased even at far larger nominal sample sizes. [Vabalas et al., PLOS One](https://pmc.ncbi.nlm.nih.gov/articles/PMC6837442/)

At 10× the current counts, approximate 95% Wilson intervals would be:

- \(r_+=110/150=.733:\ [0.657,0.798]\)
- topic-like \(r_-=50/120=.417:\ [0.332,0.506]\)
- family-like \(r_-=80/120=.667:\ [0.578,0.745]\)

So 270 would decisively confirm that the current behavior fails.

For a genuinely improved signal with true \(r_+=.733,\ r_-=.15\), 150/120 examples give approximately:

- 96% power to show \(r_+>.60\);
- 82% power to show \(r_-<.25\).

Thus:

- 270 independent causal discordants is adequate as a sealed test of a frozen three-feature policy.
- It is not adequate to search 11 features, choose interactions/thresholds, and validate the result.
- If developing and confirming a model, target roughly 270 development plus 270 untouched confirmation discordants, or narrow the model first.

The effective sample size is the number of independent rows/sessions, not the number of token moments.

## C. The three-feature trajectory signal

Yes, the direction flip deserves a fresh registered test—but only as a mechanistic endpoint inside the causal experiment.

The interesting fixed feature set is:

- negative `margin_delta5`: top-token margin collapse;
- positive `entropy_delta5`: rising uncertainty;
- natural governing-span attention mass.

The first two resemble response conflict. Botvinick’s conflict-monitoring theory specifically proposes conflict as a signal that additional cognitive control may be needed. [Botvinick et al., 2001](https://pubmed.ncbi.nlm.nih.gov/11488380/) The inverse-margin AUC of 0.706 is therefore mechanistically coherent.

But it is not yet an ACC-like gate:

- Its approximate AUC interval is about 0.51–0.90.
- Several regressions also showed margin collapse.
- Conflict indicates demand for some control; it does not establish that this particular focus intervention has positive value.
- Expected Value of Control requires predicted payoff minus control cost, not conflict alone. [Shenhav, Botvinick & Cohen](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

Register it as:

- fixed three-feature set, no substitutions;
- inverse margin direction frozen;
- actual changed-family holdouts;
- AUC and a calibrated utility operating point;
- comparison against margin-only and attention-only;
- sealed causal-moment confirmation.

Do not register a controller from the current 27.

## Sunk-cost traps

Never do these:

- Refit the 11-feature probe on the current anatomy with a different penalty or threshold.
- Search feature subsets until one passes family folds.
- Treat more model seeds on the same 27 rows as more evidence.
- Generate 270 whole-policy discordants without repairing moment attribution.
- Discard neutral opportunities and report precision only among discordants.
- Train a GRU before proving that correctly labeled moment-level signal exists.
- Call canonical-token or verifier-state inputs “fully automatic.”
- Describe inverse margin as proof of an ACC mechanism.
- Keep adding families while still defining family by `combo[0]`.

## Multi-IF ruling

Wait for Multi-IF before launching the expensive correction. The live artifact currently contains only eight base conversations and no comparison arm, so it says nothing yet.

Multi-IF is the better scope decision because its arms accumulate their own histories across three turns ([b4_multiif.py](/home/bmarti44/stencil-llm/scripts/b4_multiif.py:154)). Interpret the completed result this way:

1. **Static-0.25 helps late turns, deficit-wave does not:** strong evidence that the actuator has multi-turn value and WHEN remains the blocker. Launch causal-moment collection on fresh fixed-history multi-turn sessions.

2. **Deficit-wave helps:** do not build EVF yet. The simple gate may already be sufficient in the intended arena; replicate and characterize it first.

3. **Neither helps, but an oracle chooser over their recorded outputs has substantial late-turn lift:** there is timing headroom, but those outputs are only a policy-level screen. Run fixed-base-history, single-burst causal branches next.

4. **Neither helps and the oracle-of-available-arms has negligible lift:** do not fund a larger WHEN learner. First establish that this actuator has moment-level headroom in multi-turn work.

Because each Multi-IF arm consumes its own responses, later-turn arm differences are not clean local treatment effects. Any training anatomy must replay identical base histories before branching.

## Ranked recommendation

### Register now

1. **The post-Multi-IF decision rule**, before seeing its outcome.
2. **A fresh causal-moment protocol**, conditionally authorized only if Multi-IF shows actuator or oracle headroom.
3. **The fixed three-feature conflict replication** as a primary mechanistic endpoint within that protocol—not as a standalone rescue.

### Register after Multi-IF, if warranted

1. Collect helpful/harmful/neutral single-burst counterfactuals on fresh multi-turn sessions.
2. Test the fixed three-feature probe first.
3. Only if it passes, compare the full deployable feature set.
4. Only then authorize a recurrent obligation tracker.

### Never

- E0-with-more-rows.
- Any further analysis-driven tuning on the 27 cases.
- E1 as originally envisioned without causal moment labels.
- A claim of task-general automatic focus based on verifier-derived synthetic families alone.

The honest correction is not “E0 was underpowered.” It is: **E0 was underpowered and asked a causally blurred question. The registered negative stands; a new experiment must fix the question before increasing the sample.**
tokens used
7,516,996
## Bottom line

E0 stays killed. The failure was real under its registered test.

But E0 also contained genuine design flaws that justify a new, differently identified experiment—not an E0 rerun:

1. It assigned a whole-response treatment outcome to the first output divergence, even though the deficit policy intervened repeatedly.
2. Its family holdout was mis-keyed: it grouped by the first listed constraint, which was the constraint whose verifier changed in only 18/27 discordants.
3. The registered concordant controls were never used.
4. `obligation_shift` used canonical-answer information unavailable to an autonomous inference-time gate.

The best correction is therefore not “collect 10× more copies of E0.” It is a fresh causal moment dataset: at a fixed prefix, branch one deterministic rollout with a single focus burst and one without it, then label that exact decision helpful, harmful, or neutral.

I would register the design now but wait for Multi-IF before spending GPU on it.

## A. Real E0 design flaws

### 1. The label was attached to the wrong moment

The registration asserts that the first divergence is “the WHEN decision that mattered” ([EVF-PLAN.md](/home/bmarti44/stencil-llm/EVF-PLAN.md:27)). That is not established.

`load_anatomy()` labels an entire base-vs-wave response pair by final adherence ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:45)), while `extract_features()` inspects only the first divergence prefix ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:106)). The deficit policy acted across the generation, so the final repair or regression could have been caused by:

- an earlier intervention that changed latent trajectory before visible divergence;
- several interventions jointly;
- an intervention much later than first divergence;
- accumulated attention starvation rather than the particular divergence decision.

This is the largest unanticipated flaw. E0 tested “can first-divergence state predict which complete policy eventually won?” It did not cleanly test “should I press now?”

### 2. The family-holdout grouping was wrong for 9/27 rows

The script defines family from `combo[0]` ([e0_pilot.py](/home/bmarti44/stencil-llm/scripts/e0_pilot.py:30)). I re-ran the individual vendored verifiers on both responses:

- 26/27 discordants changed exactly one constraint verdict.
- One changed two.
- The changed constraint was the first listed constraint in only 18/27 cases.

Examples:

- Item 44 was grouped as `format` because `bullets` came first, but the changed verifier was `kw_exist`.
- Item 132 was grouped as `change_case`, but the changed verifier was `placeholders`.
- Item 170 was grouped as `keywords`, but the changed verifier was `n_words_max`.

Therefore the reported leave-one-family-out result is reproducible, but it is not actually leave-out-the-causal-family. This can create leakage and instability in either direction. It does not erase the registered failure, but a successor must group by the verifier outcome that changed—or use all active families as a multilabel group.

### 3. Concordant controls were specified but omitted

The plan explicitly included matched concordant controls ([EVF-PLAN.md](/home/bmarti44/stencil-llm/EVF-PLAN.md:22)), and `load_controls()` exists ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:60)). But `e0_pilot.py` never calls it; the fitted and evaluated dataset is only the 27 discordants.

That omission matters because a real gate sees mostly neutral opportunities. A classifier trained only on repairs versus regressions cannot estimate:

- its overall firing rate;
- compute wasted on neutral moments;
- whether it fires indiscriminately outside outcome-changing cases;
- its deployed positive predictive value.

A successor needs three labels: helpful, harmful, and neutral.

### 4. `obligation_shift` was not a deployable obligation-state signal

The feature uses token IDs extracted from `row["canonical"]` and `row["obligation_spans"]` ([evf.py](/home/bmarti44/stencil-llm/src/stencil/evf.py:149)). It then averages the one-step log-probability shift over the union of those token types.

Problems:

- The canonical response is unavailable at inference.
- It pools already-satisfied, future, and currently irrelevant obligations.
- It discards order and multiplicity.
- It does not ask whether the next several tokens make progress.
- A token appearing anywhere in an obligation edit becomes “desirable now.”

It was acceptable as an oracle diagnostic. It cannot be an input to a fully autonomous deployed gate.

## B. What a properly powered correction should test

### Do not manufacture 270 more whole-policy discordants

The current discordant yield was 27/200 = 13.5%. At the same rate, 2,000 fresh rows would yield approximately 270 discordants, with ordinary sampling variation of roughly ±30.

But 270 examples constructed the same way would only make the attribution error more precise.

### Manufacture causal decision examples instead

For each eligible moment on a fixed trajectory:

1. Freeze the exact prompt, generated prefix, selected span, KV state, dose, and rollout policy.
2. Branch:
   - `A=0`: no focus burst;
   - `A=1`: exactly one registered focus burst, then no further treatment.
3. Continue both deterministically to a verifier-resolvable endpoint.
4. Score the full per-constraint vector, parse/truncation cost, and total utility.
5. Label:
   - helpful: \(\Delta U>0\);
   - harmful: \(\Delta U<0\);
   - neutral: \(\Delta U=0\).
6. Split by session/topic and actual changed constraint family. Never split moments from one row across train and evaluation.

That is a deterministic intervention experiment. It directly supplies the individualized treatment effect the gate is supposed to predict. Modern policy-learning language frames this as learning which localized intervention has positive expected benefit, rather than predicting outcomes under an entire confounded policy. [Localized intervention policy learning](https://proceedings.mlr.press/v238/marmarelis24a.html)

Offline verifier labels are legitimate supervision, provided the writeup says exactly that. They cease to be “fully general” unless the learned signal transfers to held-out verifier families and to settings without those checkers.

### Is 270 enough for 11 features?

Only barely for exploration; not for development and decisive validation together.

With the observed 15:12 ratio, 270 discordants gives roughly 150 helpful and 120 harmful cases:

- 120 minority events / 11 slopes = 10.9 events per feature.
- That barely clears the old ten-events-per-variable heuristic.
- It ignores family/topic clustering.
- It leaves no independent confirmation set if all 270 are used for training and grouped CV.

Prediction-model sample-size work explicitly warns that the ten-events heuristic is not a guarantee; required size depends on signal strength, calibration, shrinkage, and outcome prevalence. One published example needed 461 observations for ten predictors and a 30% outcome rate to control prediction error. [Riley et al., BMJ](https://www.bmj.com/content/368/bmj.m441) Small-sample cross-validation can remain substantially biased even at far larger nominal sample sizes. [Vabalas et al., PLOS One](https://pmc.ncbi.nlm.nih.gov/articles/PMC6837442/)

At 10× the current counts, approximate 95% Wilson intervals would be:

- \(r_+=110/150=.733:\ [0.657,0.798]\)
- topic-like \(r_-=50/120=.417:\ [0.332,0.506]\)
- family-like \(r_-=80/120=.667:\ [0.578,0.745]\)

So 270 would decisively confirm that the current behavior fails.

For a genuinely improved signal with true \(r_+=.733,\ r_-=.15\), 150/120 examples give approximately:

- 96% power to show \(r_+>.60\);
- 82% power to show \(r_-<.25\).

Thus:

- 270 independent causal discordants is adequate as a sealed test of a frozen three-feature policy.
- It is not adequate to search 11 features, choose interactions/thresholds, and validate the result.
- If developing and confirming a model, target roughly 270 development plus 270 untouched confirmation discordants, or narrow the model first.

The effective sample size is the number of independent rows/sessions, not the number of token moments.

## C. The three-feature trajectory signal

Yes, the direction flip deserves a fresh registered test—but only as a mechanistic endpoint inside the causal experiment.

The interesting fixed feature set is:

- negative `margin_delta5`: top-token margin collapse;
- positive `entropy_delta5`: rising uncertainty;
- natural governing-span attention mass.

The first two resemble response conflict. Botvinick’s conflict-monitoring theory specifically proposes conflict as a signal that additional cognitive control may be needed. [Botvinick et al., 2001](https://pubmed.ncbi.nlm.nih.gov/11488380/) The inverse-margin AUC of 0.706 is therefore mechanistically coherent.

But it is not yet an ACC-like gate:

- Its approximate AUC interval is about 0.51–0.90.
- Several regressions also showed margin collapse.
- Conflict indicates demand for some control; it does not establish that this particular focus intervention has positive value.
- Expected Value of Control requires predicted payoff minus control cost, not conflict alone. [Shenhav, Botvinick & Cohen](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

Register it as:

- fixed three-feature set, no substitutions;
- inverse margin direction frozen;
- actual changed-family holdouts;
- AUC and a calibrated utility operating point;
- comparison against margin-only and attention-only;
- sealed causal-moment confirmation.

Do not register a controller from the current 27.

## Sunk-cost traps

Never do these:

- Refit the 11-feature probe on the current anatomy with a different penalty or threshold.
- Search feature subsets until one passes family folds.
- Treat more model seeds on the same 27 rows as more evidence.
- Generate 270 whole-policy discordants without repairing moment attribution.
- Discard neutral opportunities and report precision only among discordants.
- Train a GRU before proving that correctly labeled moment-level signal exists.
- Call canonical-token or verifier-state inputs “fully automatic.”
- Describe inverse margin as proof of an ACC mechanism.
- Keep adding families while still defining family by `combo[0]`.

## Multi-IF ruling

Wait for Multi-IF before launching the expensive correction. The live artifact currently contains only eight base conversations and no comparison arm, so it says nothing yet.

Multi-IF is the better scope decision because its arms accumulate their own histories across three turns ([b4_multiif.py](/home/bmarti44/stencil-llm/scripts/b4_multiif.py:154)). Interpret the completed result this way:

1. **Static-0.25 helps late turns, deficit-wave does not:** strong evidence that the actuator has multi-turn value and WHEN remains the blocker. Launch causal-moment collection on fresh fixed-history multi-turn sessions.

2. **Deficit-wave helps:** do not build EVF yet. The simple gate may already be sufficient in the intended arena; replicate and characterize it first.

3. **Neither helps, but an oracle chooser over their recorded outputs has substantial late-turn lift:** there is timing headroom, but those outputs are only a policy-level screen. Run fixed-base-history, single-burst causal branches next.

4. **Neither helps and the oracle-of-available-arms has negligible lift:** do not fund a larger WHEN learner. First establish that this actuator has moment-level headroom in multi-turn work.

Because each Multi-IF arm consumes its own responses, later-turn arm differences are not clean local treatment effects. Any training anatomy must replay identical base histories before branching.

## Ranked recommendation

### Register now

1. **The post-Multi-IF decision rule**, before seeing its outcome.
2. **A fresh causal-moment protocol**, conditionally authorized only if Multi-IF shows actuator or oracle headroom.
3. **The fixed three-feature conflict replication** as a primary mechanistic endpoint within that protocol—not as a standalone rescue.

### Register after Multi-IF, if warranted

1. Collect helpful/harmful/neutral single-burst counterfactuals on fresh multi-turn sessions.
2. Test the fixed three-feature probe first.
3. Only if it passes, compare the full deployable feature set.
4. Only then authorize a recurrent obligation tracker.

### Never

- E0-with-more-rows.
- Any further analysis-driven tuning on the 27 cases.
- E1 as originally envisioned without causal moment labels.
- A claim of task-general automatic focus based on verifier-derived synthetic families alone.

The honest correction is not “E0 was underpowered.” It is: **E0 was underpowered and asked a causally blurred question. The registered negative stands; a new experiment must fix the question before increasing the sample.**

# Probe-data readiness inventory — gpt-6-astra — 2026-09-07

CPU-only, read-only accounting, except this report. No fitting or inference performed. No GPU, container, flag, process signal, code modification, or `data/bench` access. Larger-test access was restricted to locating checkpoint-record filenames and counting newline delimiters; no JSON records or scientific outcomes were parsed. Protocol is relocated to `archive/plan/PROTOCOL.md`; current ledger STATE and historical governing plan were read. The user's one-file scope supersedes ledger-writing and historical phase-review workflow for this inventory.

**1. LABELS**

The authoritative inventory is `results/quick-checks/composition-pilot-{5,6,7}/main-records.jsonl`: **1,664 main-round records**, all with `outcome.applicable/satisfied/observed`; **1,504 observed rounds**, **160 unobserved**. Each pilot reuses `slab2-dev-00..07`, 16 rounds per episode. There are only **eight distinct episode identities**, not 104 independent lanes or 1,664 independent trials.

| Pilot | Arms | Rounds per arm | Total records | Observed | File written |
|---|---|---|---|---|---|
| 5 | R,N,T,O | 128 | 512 | 352 | 342 |
| 6 | R,N,T,O,Q | 128 | 640 | 640 | 639 |
| 7 | R,N,T,Q | 128 | 512 | 512 | 511 |

R is the rendered-register arm, N plain history, T the true-rules control, O the gold-event/oracle control, and Q a fresh-task control. Q has different history exposure; O duplicates R outputs/prompts in pilots 5/6. Keep these arm distinctions in any fit.

**Counting rule:** A = applicable AND observed AND satisfied; V = applicable AND observed AND NOT satisfied; U = applicable AND NOT observed (a parse failure is not an observed trait measurement). Nonapplicable rounds are excluded. Each cell below is **A / V / U**. For an attempt-level operational failure target, the exact count is A versus V+U; do not quietly call U an observed hidden-checker violation. Syntax failures can be observed yet not written.

CHANGE means the obligation has a non-`add` source event **on that round**: supersedes, completes, cancels or reinstates. Round-0 introductions are not CHANGE. Multiple events for a key count once. Lifecycle changes can make a trait nonapplicable, in which case it is absent from the applicable-label table. A later round after a change is not itself CHANGE. This definition comes from the episode's saved N `source_events`, also used for Q to avoid mistaking Q's fresh reconstruction for a new episode lifecycle event. Language has no CHANGE rounds.

| Pilot | Arm | Obligation | Other rounds A/V/U | CHANGE A/V/U |
|---|---|---|---|---|
| 5 | N | language | 96/16/16 | 0/0/0 |
| 5 | N | indent | 11/87/14 | 9/5/2 |
| 5 | N | format | 19/5/3 | 7/0/1 |
| 5 | N | delivery | 27/8/6 | 1/6/1 |
| 5 | O | language | 31/33/64 | 0/0/0 |
| 5 | O | indent | 0/56/56 | 0/8/8 |
| 5 | O | format | 0/13/14 | 0/4/4 |
| 5 | O | delivery | 22/0/19 | 4/0/4 |
| 5 | R | language | 31/33/64 | 0/0/0 |
| 5 | R | indent | 0/56/56 | 0/8/8 |
| 5 | R | format | 0/13/14 | 0/4/4 |
| 5 | R | delivery | 22/0/19 | 4/0/4 |
| 5 | T | language | 72/40/16 | 0/0/0 |
| 5 | T | indent | 8/90/14 | 5/9/2 |
| 5 | T | format | 17/6/4 | 5/2/1 |
| 5 | T | delivery | 37/0/4 | 5/2/1 |
| 6 | N | language | 80/48/0 | 0/0/0 |
| 6 | N | indent | 11/101/0 | 9/7/0 |
| 6 | N | format | 27/0/0 | 8/0/0 |
| 6 | N | delivery | 39/2/0 | 1/7/0 |
| 6 | O | language | 80/48/0 | 0/0/0 |
| 6 | O | indent | 3/109/0 | 4/12/0 |
| 6 | O | format | 8/19/0 | 2/6/0 |
| 6 | O | delivery | 41/0/0 | 8/0/0 |
| 6 | Q | language | 124/4/0 | 0/0/0 |
| 6 | Q | indent | 52/60/0 | 7/9/0 |
| 6 | Q | format | 10/17/0 | 2/6/0 |
| 6 | Q | delivery | 41/0/0 | 8/0/0 |
| 6 | R | language | 80/48/0 | 0/0/0 |
| 6 | R | indent | 3/109/0 | 4/12/0 |
| 6 | R | format | 8/19/0 | 2/6/0 |
| 6 | R | delivery | 41/0/0 | 8/0/0 |
| 6 | T | language | 111/17/0 | 0/0/0 |
| 6 | T | indent | 13/99/0 | 10/6/0 |
| 6 | T | format | 18/9/0 | 5/3/0 |
| 6 | T | delivery | 41/0/0 | 7/1/0 |
| 7 | N | language | 128/0/0 | 0/0/0 |
| 7 | N | indent | 13/99/0 | 11/5/0 |
| 7 | N | format | 24/3/0 | 8/0/0 |
| 7 | N | delivery | 39/2/0 | 1/7/0 |
| 7 | Q | language | 128/0/0 | 0/0/0 |
| 7 | Q | indent | 52/60/0 | 5/11/0 |
| 7 | Q | format | 1/26/0 | 0/8/0 |
| 7 | Q | delivery | 41/0/0 | 8/0/0 |
| 7 | R | language | 127/1/0 | 0/0/0 |
| 7 | R | indent | 13/99/0 | 10/6/0 |
| 7 | R | format | 24/3/0 | 7/1/0 |
| 7 | R | delivery | 41/0/0 | 8/0/0 |
| 7 | T | language | 128/0/0 | 0/0/0 |
| 7 | T | indent | 17/95/0 | 12/4/0 |
| 7 | T | format | 15/12/0 | 4/4/0 |
| 7 | T | delivery | 41/0/0 | 7/1/0 |

| All pilots / obligation | Other A/V/U | CHANGE A/V/U | Total A/V/U |
|---|---|---|---|
| language | 1216/288/160 | 0/0/0 | 1216/288/160 |
| indent | 196/1120/140 | 86/102/20 | 282/1222/160 |
| format | 171/145/35 | 50/44/10 | 221/189/45 |
| delivery | 473/12/48 | 70/24/10 | 543/36/58 |

**Label-version warning:** These are the saved labels, without retrospective relabeling. Pilot 5/6 `language.satisfied = not execution.breakage`; their indent criterion also depends on breakage and allows vacuous empty-width agreement. Pilot 7 separates language/style from runtime breakage and requires a nonempty indent measurement. Thus pilot 6's 48 language-disagreement cells below are not evidence of 48 genuine language-choice disagreements. Sources: pinned pilot-5 `9f0c6d27:src/stencil/focus/slab2.py`, pilot-6 README closing discussion, pilot-7 README floor definition, and current `slab2.py:615–637`. `delivery_scope` exists in 5/6 and is removed in 7; it is not silently merged into the four requested kinds.

**Protected larger test:** at **2026-09-07 13:51:33 UTC**, complete newline-terminated checkpoint records counted as follows:

| Checkpoint arm | Record count |
|---|---|
| R | 536 |
| N | 512 |
| T | 512 |
| Q | 256 |
| Total | 1816 |

Files: `results/larger-test/checkpoint-records-{R,N,T,Q}.jsonl`. These are a live sequential snapshot, not an atomic completion receipt. The frozen schedule in the handoff/ledger is 3,328 records (R/N/T 1,024 each; Q 256). **No adherence, kind, CHANGE, observed-status, or matched-pair counts are available for those 1,816 records under this authorization.** Deriving them would require reading protected scientific content. Do not infer them from the checkpoint count or call them fit-ready labeled data.

Each pilot also has 16 saved determinism HTTP calls (8 forward + 8 reverse) and 8 capture-journal rows. These are repeated round-0 control receipts, not additional independently labeled main rounds; they are excluded from fitting and recovery costs below. `raw.jsonl`, journals, HTTP responses, and pilot-6 scored records are alternate representations of main calls, not extra examples.

**2. MATCHED PAIRS**

A cell is **(pilot, episode, round, obligation)** with at least two applicable, observed arms and both satisfaction values. No matching across pilot versions. “Arm pairs” counts unordered adhered/violated arm pairs within each cell; a cell is counted once regardless of how many pairs it yields. “Written-only” additionally requires both participating arms to have written a file; it does not retroactively repair older scorer semantics.

| Pilot | Kind | Observed cells | Discordant arm pairs | Episodes | Written-only cells | Written-only arm pairs |
|---|---|---|---|---|---|---|
| 5 | language | 9 | 12 | 3 | 0 | 0 |
| 5 | indent | 14 | 38 | 4 | 9 | 33 |
| 5 | format | 18 | 55 | 5 | 16 | 50 |
| 5 | delivery | 12 | 21 | 5 | 12 | 21 |
| 6 | language | 48 | 250 | 4 | 48 | 249 |
| 6 | indent | 68 | 304 | 8 | 68 | 304 |
| 6 | format | 29 | 144 | 8 | 29 | 144 |
| 6 | delivery | 9 | 38 | 7 | 9 | 38 |
| 7 | language | 1 | 3 | 1 | 0 | 0 |
| 7 | indent | 68 | 209 | 8 | 68 | 207 |
| 7 | format | 34 | 111 | 8 | 34 | 110 |
| 7 | delivery | 9 | 28 | 7 | 9 | 28 |

Across pilots, observed cells / arm pairs are **language 58/265, indent 150/551, format 81/310, delivery 30/87**. Deduplicating episode-round identities across versions gives 56, 77, 35, 17 respectively; those are identity counts, not permission to cross-pair differing recipes. Across all kinds there are **215 distinct (pilot,episode,round) cells**, using **918 distinct arm-round records**. Written-only gives **206 cells / 896 records**. A record participating in multiple kinds/pairs is recovered once. The appendix in section 3 identifies every record in the observed matched subset.

For the alternative **attempt-level** target A versus V+U (counting unobserved parse failures as operational failures), discordant cell / arm-pair counts are: pilot 5 — language 65/236, indent 20/73, format 32/112, delivery 32/106; pilot 6 — language 48/250, indent 68/304, format 29/144, delivery 9/38; pilot 7 — language 1/3, indent 68/209, format 34/111, delivery 9/28. These additional pilot-5 contrasts primarily measure parse failure, not observed obligation adherence. The 918-record recovery cohort below uses the observed-label definition, not this alternative target.

For the cleaner minimum, restrict to **pilot 7 R/N/T**, written-only:

| Kind | Cells | Arm pairs | Episodes |
|---|---|---|---|
| language | 0 | 0 | 0 |
| indent | 10 | 20 | 4 |
| format | 16 | 32 | 4 |
| delivery | 9 | 18 | 7 |

This uses **87 distinct arm-round records**. Including fresh-task Q makes pilot 7's written-only set 323 records and greatly enlarges the indent/format counts, but changes the contrast from history-bearing arms to fresh-task versus history as well. These are matched tasks/rounds, **not identical prompts or identical prior trajectories**; neither arm disagreement nor probe separability establishes a causal measure of alignment.

**LOCK pairs:** the pilot-5 Opus review §1.2 defines the absorbing fence failure: onset at round 0, no later recovery. There are **six R/N/T lanes** (R DEV00/03/05/07; N DEV02; T DEV05), or **ten with duplicate O DEV00/03/05/07 included**. All start locked: **zero last-compliant → first-fence-locked within-lane pairs**, for every obligation kind. There is no prior generated round to use.

If “lock” is broadened to persistent syntax failure through the end of the saved lane, there are exactly **two additional execution-compliant → nonwritten pairs**, both pilot-5 T: DEV00 **10→11**, DEV07 **12→13**. The saved language label flips in both; indent flips only in DEV07 (DEV00 was already indent-violating at round 10); format and delivery supply zero adhered→violated pairs at these onsets. Thus this explicitly broader definition yields language **2**, indent **1**, format **0**, delivery **0**. DEV00's rules change at the onset; this is not a controlled stationary-rule contrast. R/O DEV04 round12 syntax errors recover at round13 and are not locks. Pilots 6/7 have **zero persistent end-of-lane nonwrite locks**. The review's “96 repeats” must not be reinterpreted as 96 available onset pairs.

**3. HIDDEN STATES**

**Yes, saved hidden states already exist in earlier HF runs; none exist in the inspected pilot-5/6/7 artifacts.**

| Location | Arrays | Recorded calls | Verified array representation | On-disk bytes including NPY headers |
|---|---|---|---|---|
| results/quick-checks/composition-pilot/hidden/{batch,sequential}/ | 256 | 128 | float16 (5,2048) | 5275648 |
| results/quick-checks/composition-pilot-2/hidden/parity/ | 128 | 64 | float16 (5,2048) | 2637824 |

All 384 array headers were read on CPU: little-endian float16, shape (5,2048). Each call has last-prompt-token and generated-body-mean arrays at one-based post-block layers **8,16,24,32,40**. Pilot 1 has 128 prompt vectors but only 117 complete body means: 10 capped and one interrupted reply have partial means. Pilot 2's README also flags ten cap-side means. Consult each `hidden-manifest.json` and capture-validity metadata before use. These earlier DEV00 qualification trajectories use older recipes; they do not provide hidden states for the 1,664 pilot-5/6/7 calls, nor episode-generalization evidence. The pilot-1 arrays are explicitly documented as local, uncommitted artifacts.

The **actual saved vLLM completion path does not expose/persist hidden states**: `scripts/composition_pilot5.py:31–80` sends token-ID completion requests and consumes text/token IDs/EOS; the saved HTTP and journal schemas contain no hidden tensors. That is a statement about this transport, not every possible vLLM extension. Recovery using the existing workflow requires a **separate teacher-forced HF forward pass** over each exact saved prompt and actual vLLM body IDs. It yields **HF activations conditioned on vLLM tokens**, not recovered vLLM internal activations. See `results/quick-checks/vllm-qual/README.md` recovery contract. Do this only after the running experiment releases the GPU and a new fit/extraction is authorized.

**Exact token accounting:** CPU-loaded the real `models/qwen3-30b-a3b-hf/tokenizer.json`, SHA256 `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`. All **1,664 prompts** round-trip decode→encode to identical IDs; all **1,664 output bodies** decode to the exact saved output and re-encode to identical IDs. HTTP prompt IDs equal journal rendered IDs, lengths equal recorded prompt usage, and journal output IDs equal saved body IDs. The completion usage includes one terminal EOS; body IDs exclude it. Recovery forwards the last body token, excludes terminal EOS, and uses **P+B tokens per call**. It does not retokenize prompt+answer as an unanchored combined string.

One cold full-sequence forward invocation per record is the costing convention; batching can reduce invocation count but not this sum of logical sequences. No cache-reuse or duplicate-elimination discount is assumed. There are 1,252 distinct prompt+body token sequences among all 1,664 rows and 708 among the 918 matched rows; copies stay grouped, never split between train and test.

The measured rate in `results/quick-checks/vllm-qual/summary.json` / README is **13,753 fresh KV tokens / 16.71244043200568 summed request-prefill seconds = 822.9199114248981 tokens/s** (B1 first). The projection is exactly **tokens / rate / 60**:

| Recovery cohort | Passes | Prompt tokens P | Body tokens B | Total P+B | Tokens/pass min–max | Projected minutes |
|---|---|---|---|---|---|---|
| all | 1664 | 6701505 | 383341 | 7084846 | 441–17708 | 143.489986 |
| pilot5 | 512 | 2513033 | 135284 | 2648317 | 441–17708 | 53.636589 |
| pilot6 | 640 | 2599079 | 138279 | 2737358 | 533–14479 | 55.439943 |
| pilot7 | 512 | 1589393 | 109778 | 1699171 | 533–11557 | 34.413454 |
| matched | 918 | 4308970 | 242250 | 4551220 | 544–14479 | 92.176244 |
| matched_clean | 896 | 4168218 | 233475 | 4401693 | 544–14479 | 89.147861 |
| pilot7_matched | 324 | 1261576 | 85312 | 1346888 | 544–11557 | 27.278637 |
| pilot7_matched_clean | 323 | 1253862 | 84987 | 1338849 | 544–11557 | 27.115822 |
| pilot7_RNT_clean | 87 | 564976 | 31066 | 596042 | 3612–11557 | 12.071689 |

Names: `all` = all main pilot-5/6/7 calls; `matched` = union of observed discordant-pair endpoints; `matched_clean` = written-only endpoints; pilot7 variants apply the same restrictions within pilot 7; `pilot7_RNT_clean` is the 87-record minimum above.

**These are precise arithmetic projections, not precise measured HF GPU costs.** The rate is vLLM fresh-computed KV tokens divided by summed request prefill durations; it is not an HF activation-extraction benchmark. Long-context attention, backend numerics, materializing/reducing five layers, batching, weight load/unload, and serialization change actual time. Warm cached vLLM rates (88.891 or 40.205 tok/s) are not cold-recovery rates. Actual HF recovery GPU-minutes, peak memory, and reload overhead are **unmeasured**; measuring them now would violate CPU-only protection. No precise end-to-end HF runtime can honestly be asserted from these artifacts.

**Storage, exact raw array payload bytes:** hidden width is **2,048** (`models/qwen3-30b-a3b-hf/config.json`). Five float16 layer vectors cost **5×2,048×2 = 20,480 bytes per retained position**. The established two-pool convention (last prompt token + body mean) costs **40,960 bytes/round**. Saving every forwarded token costs **20,480×(P+B)** instead; these are different retention policies.

| Cohort | Two pooled vectors / round, bytes | All-token five-layer states, bytes |
|---|---|---|
| all | 68157440 | 145097646080 |
| pilot5 | 20971520 | 54237532160 |
| pilot6 | 26214400 | 56061091840 |
| pilot7 | 20971520 | 34799022080 |
| matched | 37601280 | 93208985600 |
| matched_clean | 36700160 | 90146672640 |
| pilot7_matched | 13271040 | 27584266240 |
| pilot7_matched_clean | 13230080 | 27419627520 |
| pilot7_RNT_clean | 3563520 | 12206940160 |

For all versus matched: **68,157,440 versus 37,601,280 pooled bytes**, or **145,097,646,080 versus 93,208,985,600 all-token bytes**. These exclude headers, IDs, metadata, and temporary tensors. With two separate NPY arrays per call and the observed 128-byte header, add 256×passes bytes. Retaining all 48 layers is unnecessary; select/reduce five layers during recovery. Storage numbers are not peak GPU-memory requirements.

For a **before-generation** detector, the last-prompt-token vector is sufficient input: forward P only, never include B in features. All rounds then cost 6,701,505 tokens / 135.726148 projected minutes and 34,078,720 raw bytes; matched rows cost 4,308,970 tokens / 87.269934 minutes and 18,800,640 bytes. The 87-record minimum costs 564,976 tokens / 11.442507 minutes and 1,781,760 bytes. A body-mean detector is post-generation and cannot substantiate a pre-generation warning claim.

**Per-pass tokenizer counts (complete inventory).** Each row lists rounds **0..15**, in order, as **P+B**; add the two integers for that pass's exact sequence length. A `*` marks membership in the 918-record observed matched subset. The membership rule in §2 is the authority; no pass is counted twice for multiple obligations.

| Pilot / episode / arm | Rounds 0..15: prompt+body tokens (* matched) |
|---|---|
| 5/slab2-dev-00/N | 410+58, 628+97, 891+136, 1197+75\*, 1459+114\*, 1749+153\*, 2084+192\*, 2478+175, 2843+231\*, 3268+270\*, 3778+310, 4322+350\*, 4914+387\*, 5574+430\*, 6224+470\*, 6919+510\* |
| 5/slab2-dev-00/O | 760+106, 1381+184, 2082+262, 2936+302, 3843+341, 4774+458, 5824+536, 6893+457, 7942+497, 9031+536, 10231+575, 11493+615, 12825+655, 14230+695, 15577+735, 16933+775 |
| 5/slab2-dev-00/R | 760+106, 1381+184, 2082+262, 2936+302, 3843+341, 4774+458, 5824+536, 6893+457, 7942+497, 9031+536, 10231+575, 11493+615, 12825+655, 14230+695, 15577+735, 16933+775 |
| 5/slab2-dev-00/T | 467+59, 743+98, 1064+137, 1441+74\*, 1772+113\*, 2131+152\*, 2535+191\*, 2985+176, 3421+230\*, 3915+269\*, 4497+308, 5116+356\*, 5759+397\*, 6464+438\*, 7152+479\*, 7877+520\* |
| 5/slab2-dev-01/N | 389+52, 583+85, 814+118, 1082+60, 1312+93, 1563+126, 1866+151, 2183+184, 2537+217, 2928+159, 3307+193\*, 3714+227\*, 4151+258\*, 4662+292\*, 5154+329\*, 5688+363\* |
| 5/slab2-dev-01/O | 739+52, 1287+85, 1872+118, 2567+60, 3224+93, 3902+126, 4559+151, 5230+184, 5938+217, 6756+159, 7595+193\*, 8496+227\*, 9456+261\*, 10500+295\*, 11485+329\*, 12476+363\* |
| 5/slab2-dev-01/R | 739+52, 1287+85, 1872+118, 2567+60, 3224+93, 3902+126, 4559+151, 5230+184, 5938+217, 6756+159, 7595+193\*, 8496+227\*, 9456+261\*, 10500+295\*, 11485+329\*, 12476+363\* |
| 5/slab2-dev-01/T | 446+52, 701+85, 993+118, 1334+60, 1637+93, 1961+126, 2325+151, 2703+184, 3118+217, 3582+159, 4037+193\*, 4524+227\*, 5040+258\*, 5626+292\*, 6193+326\*, 6795+360\* |
| 5/slab2-dev-02/N | 396+102, 651+176, 980+250, 1383+287, 1837+324, 2314+361, 2828+398, 3394+435, 3982+472, 4607+509, 5299+547, 6041+586, 6818+620, 7650+661, 8465+699, 9318+737 |
| 5/slab2-dev-02/O | 746+50, 1294+81, 1877+112, 2570+59, 3228+90, 3907+121, 4621+152, 5310+143, 5979+174, 6758+183, 7614+216, 8551+248, 9548+281\*, 10603+314\*, 11606+347\*, 12616+380\* |
| 5/slab2-dev-02/R | 746+50, 1294+81, 1877+112, 2570+59, 3228+90, 3907+121, 4621+152, 5310+143, 5979+174, 6758+183, 7614+216, 8551+248, 9548+281\*, 10603+314\*, 11606+347\*, 12616+380\* |
| 5/slab2-dev-02/T | 453+68, 730+116, 1059+164, 1453+76, 1777+124, 2139+172, 2553+220, 3021+212, 3470+260, 3984+268, 4543+317, 5172+365, 5849+411\*, 6598+460\*, 7338+509\*, 8128+558\* |
| 5/slab2-dev-03/N | 391+61, 596+103, 847+145, 1146+187, 1489+70, 1736+112, 2030+229, 2429+271, 2874+313, 3363+154, 3740+197, 4163+236, 4622+279\*, 5158+322, 5684+365, 6256+408 |
| 5/slab2-dev-03/O | 738+59, 1293+97, 1886+135, 2519+173, 3263+60, 3911+98, 4523+211, 5232+249, 5979+287, 6837+136, 7617+174, 8460+213, 9368+252, 10351+291, 11284+330, 12214+369 |
| 5/slab2-dev-03/R | 738+59, 1293+97, 1886+135, 2519+173, 3263+60, 3911+98, 4523+211, 5232+249, 5979+287, 6837+136, 7617+174, 8460+213, 9368+252, 10351+291, 11284+330, 12214+369 |
| 5/slab2-dev-03/T | 447+61, 712+103, 1023+145, 1382+187, 1798+70, 2118+112, 2472+229, 2931+271, 3436+313, 3998+154, 4451+197, 4949+236, 5487+279\*, 6097+322, 6693+365, 7335+408 |
| 5/slab2-dev-04/N | 406+55, 623+91, 874+127, 1171+163, 1506+63, 1757+99, 2033+135, 2368+199, 2752+171, 3117+207, 3564+244\*, 4033+278\*, 4550+315\*, 5133+352\*, 5704+389\*, 6318+426\* |
| 5/slab2-dev-04/O | 753+55, 1321+91, 1923+127, 2571+163, 3330+63, 4005+99, 4705+135, 5391+199, 6199+171, 6988+207, 7892+244\*, 8847+281\*, 9887+326\*, 10972+355\*, 12040+392\*, 13111+429\* |
| 5/slab2-dev-04/R | 753+55, 1321+91, 1923+127, 2571+163, 3330+63, 4005+99, 4705+135, 5391+199, 6199+171, 6988+207, 7892+244\*, 8847+281\*, 9887+326\*, 10972+355\*, 12040+392\*, 13111+429\* |
| 5/slab2-dev-04/T | 462+58, 738+97, 1051+136, 1413+175, 1828+74, 2158+113, 2516+152, 2924+214, 3391+191, 3844+230, 4385+270\*, 4950+307\*, 5570+347\*, 6255+387\*, 6927+427\*, 7645+467\* |
| 5/slab2-dev-05/N | 390+52, 588+85, 823+118, 1095+151, 1404+61, 1643+94, 1903+127, 2215+184, 2573+217, 2968+160, 3353+194, 3756+224, 4203+258, 4718+292, 5214+326, 5749+360 |
| 5/slab2-dev-05/O | 740+80, 1317+119, 1933+158, 2588+197, 3357+237, 4182+276, 5030+315, 5857+353, 6707+392, 7671+432, 8748+472, 9873+513, 11082+554, 12368+595, 13604+636, 14841+677 |
| 5/slab2-dev-05/R | 740+80, 1317+119, 1933+158, 2588+197, 3357+237, 4182+276, 5030+315, 5857+353, 6707+392, 7671+432, 8748+472, 9873+513, 11082+554, 12368+595, 13604+636, 14841+677 |
| 5/slab2-dev-05/T | 447+95, 746+128, 1078+161, 1443+194, 1854+228, 2315+261, 2793+294, 3306+326, 3836+359, 4412+393, 5067+427, 5734+461, 6448+495, 7220+529, 7964+563, 8742+597 |
| 5/slab2-dev-06/N | 396+67, 611+115, 878+163, 1197+83, 1456+131, 1751+179, 2098+227, 2512+211, 2899+259, 3338+275, 3827+324, 4382+373\*, 4987+418\*, 5663+467\*, 6335+516\*, 7061+565\* |
| 5/slab2-dev-06/O | 746+67, 1311+115, 1928+163, 2672+76, 3349+124, 4062+172, 4827+220, 5584+211, 6321+259, 7185+268, 8126+317, 9164+365\*, 10279+414\*, 11468+463\*, 12621+512\*, 13796+561\* |
| 5/slab2-dev-06/R | 746+67, 1311+115, 1928+163, 2672+76, 3349+124, 4062+172, 4827+220, 5584+211, 6321+259, 7185+268, 8126+317, 9164+365\*, 10279+414\*, 11468+463\*, 12621+512\*, 13796+561\* |
| 5/slab2-dev-06/T | 453+67, 729+115, 1057+163, 1450+76, 1776+124, 2138+172, 2552+220, 3020+211, 3468+259, 3981+268, 4540+317, 5169+366\*, 5847+414\*, 6599+463\*, 7342+512\*, 8135+561\* |
| 5/slab2-dev-07/N | 390+61, 595+103, 848+145, 1147+187, 1492+69, 1735+111, 2028+229, 2425+271, 2870+153, 3201+195, 3620+238\*, 4076+281\*, 4588+321, 5166+364\*, 5732+407\*, 6348+450\* |
| 5/slab2-dev-07/O | 737+108, 1341+97, 1936+135, 2569+173, 3313+211, 4107+249, 4870+287, 5653+325, 6549+363, 7483+401, 8529+440, 9637+479, 10820+518, 12070+557, 13259+596, 14457+635 |
| 5/slab2-dev-07/R | 737+108, 1341+97, 1936+135, 2569+173, 3313+211, 4107+249, 4870+287, 5653+325, 6549+363, 7483+401, 8529+440, 9637+479, 10820+518, 12070+557, 13259+596, 14457+635 |
| 5/slab2-dev-07/T | 446+61, 707+103, 1016+145, 1371+187, 1784+69, 2095+111, 2444+229, 2897+271, 3410+153, 3809+195, 4299+238\*, 4830+281\*, 5416+321, 6064+372\*, 6667+416\*, 7312+460\* |
| 6/slab2-dev-00/N | 500+58\*, 718+94, 978+130, 1278+66, 1531+102, 1809+138, 2129+174, 2505+166\*, 2861+210, 3265+246, 3751+283\*, 4268+320\*, 4830+353\*, 5456+390\*, 6066+427\*, 6718+464\* |
| 6/slab2-dev-00/O | 850+57\*, 1417+93, 2026+129, 2750+71, 3433+107, 4141+143, 4891+179, 5622+165\*, 6402+215, 7236+251, 8183+287\*, 9194+324\*, 10277+361\*, 11435+398\*, 12537+435\*, 13650+472\* |
| 6/slab2-dev-00/Q | 774+53\*, 823+104, 876+129, 1002+74, 1066+96, 1102+130, 1155+163, 1147+162\*, 1257+196, 1308+229, 1358+262\*, 1412+296\*, 1455+330\*, 1512+364\*, 1564+397\*, 1616+429\* |
| 6/slab2-dev-00/R | 850+57\*, 1417+93, 2026+129, 2750+71, 3433+107, 4141+143, 4891+179, 5622+165\*, 6402+215, 7236+251, 8183+287\*, 9194+324\*, 10277+361\*, 11435+398\*, 12537+435\*, 13650+472\* |
| 6/slab2-dev-00/T | 557+58\*, 832+94, 1149+130, 1519+66, 1842+102, 2190+138, 2580+174, 3013+166\*, 3439+210, 3913+246, 4472+282\*, 5065+319\*, 5702+353\*, 6399+390\*, 7080+427\*, 7799+464\* |
| 6/slab2-dev-01/N | 479+54, 675+87, 908+120, 1178+62, 1410+95, 1663+128, 1968+153\*, 2287+186\*, 2643+219\*, 3036+161, 3417+195\*, 3826+229\*, 4265+260\*, 4778+294\*, 5272+328\*, 5805+362\* |
| 6/slab2-dev-01/O | 829+54, 1375+87, 1958+120, 2651+62, 3306+95, 3982+128, 4637+153\*, 5306+186\*, 6012+219\*, 6828+161, 7665+195\*, 8564+229\*, 9522+263\*, 10564+297\*, 11547+331\*, 12536+365\* |
| 6/slab2-dev-01/Q | 753+55, 812+100, 871+135, 1003+70, 1079+99, 1121+135, 1123+170\*, 1166+205\*, 1225+240\*, 1357+170, 1418+206\*, 1479+242\*, 1535+275\*, 1595+311\*, 1655+347\*, 1715+383\* |
| 6/slab2-dev-01/R | 829+54, 1375+87, 1958+120, 2651+62, 3306+95, 3982+128, 4637+153\*, 5306+186\*, 6012+219\*, 6828+161, 7665+195\*, 8564+229\*, 9522+263\*, 10564+297\*, 11547+331\*, 12536+365\* |
| 6/slab2-dev-01/T | 536+54, 789+87, 1079+120, 1418+62, 1719+95, 2041+128, 2403+153\*, 2779+186\*, 3192+219\*, 3654+161, 4107+195\*, 4592+229\*, 5106+260\*, 5690+294\*, 6255+328\*, 6855+362\* |
| 6/slab2-dev-02/N | 486+70\*, 704+118\*, 974+166\*, 1296+78\*, 1548+126\*, 1838+174\*, 2180+222\*, 2589+214\*, 2979+262\*, 3421+270\*, 3905+319\*, 4455+368\*, 5055+413\*, 5726+462\*, 6393+511\*, 7114+560\* |
| 6/slab2-dev-02/O | 836+69\*, 1403+117\*, 2022+165\*, 2768+78\*, 3445+126\*, 4160+174\*, 4927+222\*, 5686+213\*, 6425+261\*, 7291+270\*, 8234+319\*, 9274+367\*, 10390+416\*, 11580+465\*, 12734+514\*, 13911+563\* |
| 6/slab2-dev-02/Q | 759+70\*, 826+121\*, 893+150\*, 1035+81\*, 1117+111\*, 1169+151\*, 1236+191\*, 1244+190\*, 1295+230\*, 1437+231\*, 1506+272\*, 1573+312\*, 1637+350\*, 1705+394\*, 1773+435\*, 1841+476\* |
| 6/slab2-dev-02/R | 836+69\*, 1403+117\*, 2022+165\*, 2768+78\*, 3445+126\*, 4160+174\*, 4927+222\*, 5686+213\*, 6425+261\*, 7291+270\*, 8234+319\*, 9274+367\*, 10390+416\*, 11580+465\*, 12734+514\*, 13911+563\* |
| 6/slab2-dev-02/T | 543+85\*, 839+101\*, 1155+117\*, 1504+53\*, 1807+69\*, 2116+86\*, 2446+103\*, 2799+133\*, 3171+150\*, 3577+120\*, 3991+138\*, 4444+155\*, 4914+173\*, 5428+192\*, 5903+210\*, 6397+229\* |
| 6/slab2-dev-03/N | 481+63\*, 688+105\*, 941+147\*, 1242+189\*, 1587+72\*, 1836+114\*, 2132+231\*, 2533+273\*, 2980+315\*, 3471+156\*, 3850+199\*, 4275+238\*, 4736+281\*, 5274+324\*, 5802+367\*, 6376+410\* |
| 6/slab2-dev-03/O | 828+63\*, 1382+105\*, 1982+147\*, 2630+189\*, 3397+72\*, 4068+114\*, 4711+231\*, 5459+273\*, 6253+315\*, 7166+156\*, 7998+198\*, 8902+241\*, 9880+284\*, 10942+327\*, 11963+370\*, 12990+413\* |
| 6/slab2-dev-03/Q | 754+59\*, 807+110\*, 862+140\*, 919+178\*, 1047+75\*, 1120+112\*, 1101+215\*, 1139+252\*, 1194+289\*, 1322+149\*, 1377+186\*, 1431+217\*, 1488+255\*, 1544+293\*, 1600+338\*, 1654+369\* |
| 6/slab2-dev-03/R | 828+63\*, 1382+105\*, 1982+147\*, 2630+189\*, 3397+72\*, 4068+114\*, 4711+231\*, 5459+273\*, 6253+315\*, 7166+156\*, 7998+198\*, 8902+241\*, 9880+284\*, 10942+327\*, 11963+370\*, 12990+413\* |
| 6/slab2-dev-03/T | 537+64\*, 801+106\*, 1111+148\*, 1469+190\*, 1884+72\*, 2202+114\*, 2554+232\*, 3012+274\*, 3516+316\*, 4077+156\*, 4528+198\*, 5023+238\*, 5559+281\*, 6167+324\*, 6761+367\*, 7401+410\* |
| 6/slab2-dev-04/N | 496+52\*, 710+83\*, 953+114\*, 1237+145\*, 1554+60\*, 1802+91\*, 2070+122\*, 2392+176\*, 2753+153\*, 3100+184\*, 3523+216\*, 3963+245\*, 4446+277\*, 4990+309\*, 5517+341\*, 6082+373\* |
| 6/slab2-dev-04/O | 843+52\*, 1404+83\*, 1994+114\*, 2625+145\*, 3362+60\*, 4030+91\*, 4718+122\*, 5387+176\*, 6168+153\*, 6935+184\*, 7811+216\*, 8733+245\*, 9732+285\*, 10772+309\*, 11789+341\*, 12804+373\* |
| 6/slab2-dev-04/Q | 771+53\*, 822+104\*, 867+129\*, 924+162\*, 1046+74\*, 1109+96\*, 1145+129\*, 1142+195\*, 1247+161\*, 1303+194\*, 1356+229\*, 1404+263\*, 1457+294\*, 1504+328\*, 1560+362\*, 1613+396\* |
| 6/slab2-dev-04/R | 843+52\*, 1404+83\*, 1994+114\*, 2625+145\*, 3362+60\*, 4030+91\*, 4718+122\*, 5387+176\*, 6168+153\*, 6935+184\*, 7811+216\*, 8733+245\*, 9732+285\*, 10772+309\*, 11789+341\*, 12804+373\* |
| 6/slab2-dev-04/T | 552+57\*, 827+93\*, 1136+129\*, 1491+165\*, 1896+70\*, 2222+106\*, 2573+142\*, 2971+201\*, 3425+178\*, 3865+214\*, 4390+251\*, 4936+285\*, 5534+330\*, 6166+359\*, 6810+396\*, 7497+433\* |
| 6/slab2-dev-05/N | 480+54, 676+87, 909+120, 1179+153, 1486+63, 1723+96\*, 1981+129\*, 2291+186, 2647+219, 3040+162\*, 3423+196\*, 3824+226\*, 4269+260\*, 4782+294\*, 5276+328\*, 5809+362\* |
| 6/slab2-dev-05/O | 830+54, 1376+87, 1959+120, 2579+153, 3311+63, 3973+96\*, 4656+129\*, 5316+186, 6022+219, 6840+162\*, 7679+195\*, 8564+226\*, 9528+260\*, 10567+294\*, 11554+328\*, 12540+362\* |
| 6/slab2-dev-05/Q | 753+62, 812+100, 871+134, 930+170, 1064+66, 1140+101\*, 1182+136\*, 1182+205, 1225+240, 1359+171\*, 1418+206\*, 1474+242\*, 1535+278\*, 1595+314\*, 1655+347\*, 1715+383\* |
| 6/slab2-dev-05/R | 830+54, 1376+87, 1959+120, 2579+153, 3311+63, 3973+96\*, 4656+129\*, 5316+186, 6022+219, 6840+162\*, 7679+195\*, 8564+226\*, 9528+260\*, 10567+294\*, 11554+328\*, 12540+362\* |
| 6/slab2-dev-05/T | 537+54, 790+87, 1080+120, 1407+153, 1784+63, 2091+96\*, 2419+129\*, 2786+186, 3199+219, 3662+162\*, 4118+196\*, 4591+226\*, 5112+260\*, 5696+294\*, 6257+328\*, 6857+362\* |
| 6/slab2-dev-06/N | 486+69, 703+117\*, 972+165\*, 1293+78\*, 1547+126\*, 1837+174\*, 2179+222\*, 2588+213\*, 2977+261\*, 3418+270\*, 3902+319\*, 4452+368\*, 5052+413\*, 5723+462\*, 6390+511\*, 7111+560\* |
| 6/slab2-dev-06/O | 836+69, 1403+117\*, 2022+165\*, 2768+78\*, 3447+126\*, 4162+174\*, 4929+222\*, 5688+213\*, 6427+261\*, 7293+270\*, 8236+319\*, 9276+367\*, 10393+416\*, 11584+465\*, 12739+514\*, 13916+563\* |
| 6/slab2-dev-06/Q | 759+78, 826+121\*, 893+149\*, 1035+71\*, 1119+111\*, 1169+151\*, 1236+191\*, 1244+190\*, 1295+230\*, 1437+231\*, 1506+272\*, 1573+312\*, 1637+353\*, 1705+394\*, 1773+435\*, 1841+476\* |
| 6/slab2-dev-06/R | 836+69, 1403+117\*, 2022+165\*, 2768+78\*, 3447+126\*, 4162+174\*, 4929+222\*, 5688+213\*, 6427+261\*, 7293+270\*, 8236+319\*, 9276+367\*, 10393+416\*, 11584+465\*, 12739+514\*, 13916+563\* |
| 6/slab2-dev-06/T | 543+70, 818+118\*, 1145+166\*, 1537+78\*, 1861+126\*, 2221+174\*, 2633+222\*, 3099+214\*, 3546+262\*, 4058+270\*, 4615+319\*, 5242+367\*, 5917+416\*, 6667+465\*, 7408+514\*, 8199+563\* |
| 6/slab2-dev-07/N | 480+63, 687+105, 942+147, 1243+189, 1590+71, 1835+113, 2130+231\*, 2529+273\*, 2976+155, 3309+197, 3730+240, 4188+283\*, 4702+323\*, 5282+366\*, 5850+409\*, 6468+452\* |
| 6/slab2-dev-07/O | 827+63, 1381+105, 1983+147, 2631+189, 3398+71, 4063+113, 4705+231\*, 5451+273\*, 6318+155, 7071+197, 7945+240, 8890+283\*, 9919+326\*, 11024+369\*, 12077+412\*, 13148+455\* |
| 6/slab2-dev-07/Q | 754+60, 807+111, 864+141, 919+178, 1047+74, 1115+104, 1101+215\*, 1137+259\*, 1267+141, 1322+177, 1379+216, 1436+254\*, 1488+292\*, 1544+330\*, 1598+368\*, 1656+406\* |
| 6/slab2-dev-07/R | 827+63, 1381+105, 1983+147, 2631+189, 3398+71, 4063+113, 4705+231\*, 5451+273\*, 6318+155, 7071+197, 7945+240, 8890+283\*, 9919+326\*, 11024+369\*, 12077+412\*, 13148+455\* |
| 6/slab2-dev-07/T | 536+63, 799+105, 1110+147, 1467+189, 1882+71, 2195+113, 2546+231\*, 3001+273\*, 3516+155, 3917+197, 4409+240, 4942+283\*, 5530+326\*, 6183+369\*, 6824+412\*, 7511+455\* |
| 7/slab2-dev-00/N | 500+58, 718+94, 978+130, 1278+73, 1538+109, 1823+145, 2150+181, 2533+166\*, 2889+217, 3300+253, 3793+290\*, 4317+327\*, 4886+360\*, 5519+400\*, 6139+437\*, 6801+474\* |
| 7/slab2-dev-00/Q | 634+56, 683+96, 736+129, 832+71, 896+96, 932+129, 985+162, 1007+162\*, 1087+195, 1138+228, 1187+262\*, 1240+295\*, 1239+330\*, 1296+363\*, 1348+397\*, 1400+432\* |
| 7/slab2-dev-00/R | 710+61, 1141+100, 1617+139, 2181+69, 2692+108, 3231+147, 3815+186, 4413+178\*, 5036+225, 5710+264, 6488+303\*, 7315+343\*, 8156+380\*, 9066+420\*, 9947+460\*, 10859+500\* |
| 7/slab2-dev-00/T | 557+53, 827+84, 1134+115, 1489+61, 1807+92, 2145+123, 2520+154, 2933+146\*, 3339+185, 3788+216, 4316+247\*, 4873+279\*, 5469+311\*, 6123+343\*, 6756+375\*, 7422+407\* |
| 7/slab2-dev-01/N | 479+54, 675+87, 908+120, 1178+62, 1410+95, 1663+128, 1968+153\*, 2287+186\*, 2643+219\*, 3036+161, 3417+195\*, 3826+229\*, 4265+260\*, 4778+294\*, 5272+328\*, 5805+362\* |
| 7/slab2-dev-01/Q | 613+63, 672+100, 731+135, 833+70, 909+99, 951+135, 983+170\*, 1026+205\*, 1085+240\*, 1187+170, 1247+206\*, 1307+241\*, 1319+278\*, 1379+311\*, 1439+350\*, 1499+386\* |
| 7/slab2-dev-01/R | 689+54, 1095+87, 1538+120, 2061+62, 2546+95, 3052+128, 3567+153\*, 4096+186\*, 4662+219\*, 5308+161, 5963+195\*, 6662+229\*, 7359+260\*, 8131+294\*, 8868+328\*, 9628+362\* |
| 7/slab2-dev-01/T | 536+54, 789+87, 1079+120, 1418+62, 1719+95, 2041+128, 2403+153\*, 2779+186\*, 3192+219\*, 3654+161, 4107+195\*, 4592+229\*, 5106+260\*, 5690+294\*, 6255+328\*, 6855+362\* |
| 7/slab2-dev-02/N | 486+70, 704+118, 974+166, 1296+78, 1548+126, 1838+174, 2180+222, 2589+214\*, 2979+262\*, 3421+270, 3905+319\*, 4455+368\*, 5055+413\*, 5726+462\*, 6393+511\*, 7114+560\* |
| 7/slab2-dev-02/Q | 619+70, 686+121, 753+150, 865+81, 947+111, 999+151, 1066+190, 1104+190\*, 1155+230\*, 1267+231, 1335+272\*, 1401+312\*, 1421+353\*, 1489+394\*, 1557+435\*, 1625+476\* |
| 7/slab2-dev-02/R | 696+70, 1124+118, 1604+166, 2181+78, 2688+126, 3233+174, 3830+222, 4449+214\*, 5049+262\*, 5746+270, 6508+319\*, 7348+367\*, 8203+413\*, 9129+462\*, 10037+511\*, 10985+560\* |
| 7/slab2-dev-02/T | 543+86, 841+102, 1159+118, 1510+53, 1814+69, 2124+86, 2455+103, 2809+134\*, 3183+151\*, 3591+120, 4006+138\*, 4460+155\*, 4931+173\*, 5446+192\*, 5922+210\*, 6417+229\* |
| 7/slab2-dev-03/N | 481+63\*, 688+105\*, 941+147\*, 1242+189\*, 1587+72\*, 1836+114\*, 2132+231\*, 2533+273\*, 2980+315\*, 3471+156\*, 3850+199\*, 4275+238\*, 4736+281\*, 5274+324\*, 5802+367\*, 6376+410\* |
| 7/slab2-dev-03/Q | 614+59\*, 667+110\*, 722+140\*, 779+177\*, 877+75\*, 950+112\*, 961+215\*, 999+252\*, 1054+288\*, 1152+152\*, 1206+186\*, 1216+224\*, 1272+262\*, 1328+293\*, 1384+338\*, 1438+376\* |
| 7/slab2-dev-03/R | 688+63\*, 1102+105\*, 1562+147\*, 2070+189\*, 2667+72\*, 3168+114\*, 3671+231\*, 4279+273\*, 4933+315\*, 5676+156\*, 6326+198\*, 6987+238\*, 7701+281\*, 8493+324\*, 9261+367\*, 10059+410\* |
| 7/slab2-dev-03/T | 537+64\*, 801+106\*, 1111+148\*, 1469+190\*, 1884+72\*, 2202+114\*, 2554+232\*, 3012+274\*, 3516+316\*, 4077+156\*, 4528+198\*, 5023+238\*, 5559+281\*, 6167+324\*, 6761+367\*, 7401+410\* |
| 7/slab2-dev-04/N | 496+52\*, 710+83\*, 953+114\*, 1237+145\*, 1554+60, 1802+91\*, 2070+122\*, 2392+176\*, 2753+153\*, 3100+184\*, 3523+216\*, 3963+245\*, 4446+277\*, 4990+309\*, 5517+341\*, 6082+373\* |
| 7/slab2-dev-04/Q | 631+69\*, 682+104\*, 727+129\*, 784+162\*, 876+73, 939+96\*, 975+129\*, 1002+195\*, 1077+161\*, 1133+195\*, 1185+229\*, 1189+263\*, 1241+297\*, 1288+331\*, 1344+365\*, 1397+399\* |
| 7/slab2-dev-04/R | 703+57\*, 1129+93\*, 1589+129\*, 2095+165\*, 2682+65, 3185+101\*, 3713+137\*, 4257+201\*, 4893+173\*, 5510+209\*, 6230+246\*, 6940+280\*, 7714+325\*, 8527+354\*, 9340+391\*, 10180+428\* |
| 7/slab2-dev-04/T | 552+52\*, 822+83\*, 1121+114\*, 1461+145\*, 1846+60, 2162+91\*, 2498+122\*, 2876+176\*, 3305+153\*, 3720+184\*, 4214+216\*, 4724+245\*, 5281+277\*, 5895+309\*, 6488+341\*, 7119+373\* |
| 7/slab2-dev-05/N | 480+54, 676+87, 909+120, 1179+153, 1486+63, 1723+96\*, 1981+129\*, 2291+186, 2647+219, 3040+162\*, 3423+196\*, 3824+226\*, 4269+260\*, 4782+294\*, 5276+328\*, 5809+362\* |
| 7/slab2-dev-05/Q | 613+62, 672+99, 731+134, 790+169, 894+66, 970+101\*, 1012+136\*, 1042+204, 1085+239, 1189+171\*, 1247+206\*, 1259+242\*, 1319+278\*, 1379+314\*, 1439+350\*, 1499+386\* |
| 7/slab2-dev-05/R | 690+54, 1096+87, 1539+120, 2019+153, 2581+63, 3073+96\*, 3586+129\*, 4106+186, 4672+219, 5320+162\*, 5977+195\*, 6619+226\*, 7322+260\*, 8094+294\*, 8831+328\*, 9591+362\* |
| 7/slab2-dev-05/T | 537+54, 790+87, 1080+120, 1407+153, 1784+63, 2091+96\*, 2419+129\*, 2786+186, 3199+219, 3662+162\*, 4118+195\*, 4590+226\*, 5111+260\*, 5695+294\*, 6256+328\*, 6856+362\* |
| 7/slab2-dev-06/N | 486+69, 703+117, 972+165, 1293+78, 1547+126\*, 1837+174\*, 2179+222\*, 2588+213, 2977+261, 3418+270\*, 3902+319\*, 4452+368\*, 5052+413\*, 5723+462\*, 6390+511\*, 7111+560\* |
| 7/slab2-dev-06/Q | 619+69, 686+120, 753+149, 865+82, 949+111\*, 999+151\*, 1066+191\*, 1104+190, 1155+230, 1267+231\*, 1335+272\*, 1401+312\*, 1421+353\*, 1489+394\*, 1557+435\*, 1625+476\* |
| 7/slab2-dev-06/R | 696+69, 1123+117, 1602+165, 2178+78, 2687+126\*, 3232+174\*, 3829+222\*, 4448+213, 5047+261, 5743+270\*, 6505+319\*, 7345+367\*, 8201+416\*, 9131+465\*, 10043+514\*, 10994+563\* |
| 7/slab2-dev-06/T | 543+70, 818+118, 1145+166, 1537+78, 1861+126\*, 2221+174\*, 2633+222\*, 3099+214, 3546+262, 4058+270\*, 4615+319\*, 5242+368\*, 5918+417\*, 6669+466\*, 7411+515\*, 8203+564\* |
| 7/slab2-dev-07/N | 480+63, 687+105, 942+147, 1243+189, 1590+71, 1835+113, 2130+231\*, 2529+273\*, 2976+155, 3309+197, 3730+240, 4188+283\*, 4702+323\*, 5282+366\*, 5850+409\*, 6468+452\* |
| 7/slab2-dev-07/Q | 614+60, 667+111, 724+141, 779+178, 877+73, 945+111, 961+215\*, 997+252\*, 1097+140, 1152+178, 1208+216, 1264+254\*, 1272+292\*, 1328+329\*, 1382+368\*, 1440+406\* |
| 7/slab2-dev-07/R | 687+63, 1101+105, 1563+147, 2071+189, 2668+71, 3163+113, 3665+231\*, 4271+273\*, 4968+155, 5551+197, 6243+240, 6988+283\*, 7756+323\*, 8591+366\*, 9398+409\*, 10240+452\* |
| 7/slab2-dev-07/T | 536+63, 799+105, 1110+147, 1467+189, 1882+71, 2195+113, 2546+231\*, 3001+273\*, 3516+155, 3917+197, 4409+240, 4942+283\*, 5530+326\*, 6183+369\*, 6824+412\*, 7511+455\* |

**4. TEXT-ONLY FEATURES**

**A text-side development baseline is feasible today with zero GPU.** The following artifacts already exist:

| Feature | Available source / reconstruction | Timing restriction |
|---|---|---|
| Emitted text and token IDs | main-records.jsonl output/output_ids; local/http/main/{episode}/{arm}/{turn}.json response | Post-generation only |
| Exact rendered prompt and raw messages | local/main/{episode}/{arm}/loop.jsonl rendered_token_ids, rendered_messages, raw_messages; HTTP request.prompt is the full anchored context | Use only context present before this round |
| Q prompt/journal | local/main/{episode}/Q/q-{turn}.jsonl and matching HTTP request; fresh-task history differs | Same pre-generation boundary |
| Public tool results / feedback | Current execution record; previous-round feedback in the next exact prompt, with tool_results journal field also present (can be empty) | Current execution is post-generation; prior feedback is available before generation |
| Trailer | Literal report: line in saved output; parsed deterministically under pinned parser | Post-generation |
| File diff | Reconstruct each lane from saved file outputs and initial DEV file state; compare to previous successfully parsed/written version of the same path, not merely previous round (which may edit the other file) | Post-generation current diff; historical diffs available before generation |

`local/main/.../workspace/{core,policy}.py` is final workspace state, not a saved per-round diff. Exact intermediate files are recoverable from accepted full-file replies; failed parses/syntax writes must leave prior state unchanged. The checker uses a specific `changed_code` view (added lines against last parsable file), not an arbitrary visual diff. No execution of model-emitted code is needed for a lexical baseline inventory.

Fit a small regularized CPU text classifier on DEV training folds, conditioning on the active obligation/value and visible context. An emitted-text classifier can be fitted for diagnostic comparison, but for these traits the deterministic validator is already available. A pre-generation classifier can use prompt text, current rules, rule age, prior failures, and historical feedback. Current output, trailer, diff, hidden outcomes, success/diagnostics, or current execution are **target leakage** for that task. This inventory did not fit a classifier.

**5. THE MECHANISABLE SPLIT**

| Kind | Exactly code-checkable here? | What the saved target actually measures |
|---|---|---|
| language | Yes, for this operational definition | Pilot 7: parsed/written Python file (syntax/parser checks); pilots 5/6 additionally conjoin runtime breakage. This is not a natural-language language-identification task or proof of arbitrary program correctness. |
| indent | Yes | Pinned changed-code indent widths against the active numeric indent rule; pilot 7 requires nonempty widths and separates runtime breakage. General nested-code style claims require the actual specified checker semantics. |
| format | Yes | Compact-mode trailer excludes the delivery field; applicable only when compact under this scoring contract. A general report-quality judgment is not being measured. |
| delivery | Yes | For verbose, delivery-scoped requests, trailer delivery value equals the active resolved rule/default. This is a literal status-marker check, not evidence an external delivery really happened. |

For **catching these defined failures after generation**, a validator supplies the exact registered answer and should precede any probe or 4B judge. A detector's distinct role is **predicting failure before generation**, so it can trigger a bounded intervention, or detecting a separately defined obligation code cannot check. There are **zero nonmechanisable obligation kinds in these four labels**. These data therefore cannot establish a need for, or accuracy of, a 4B fallback judge on subjective adherence. Semantic correctness beyond the finite tests and arbitrary task alignment are broader constructs than these labels.

**6. LEAKAGE AND SPLITS**

Use **leave-episodes-out**, grouping each DEV episode across **all rounds, all arms, all pilots, raw/HTTP/journal copies, hashes, and any derived pairs/features**. Eight DEV IDs allow eight exploratory held-episode folds, not 1,664 independent test cases. Do not random-split rounds or contrastive endpoints. Keep selection, scaling, regularization and threshold calibration inside the training episodes (nested grouping when tuning); estimate uncertainty with episode units. Repeatedly inspected DEV “test” folds remain development validation, not fresh confirmation.

For genericity, add **leave-obligation-kind-out** while retaining leave-episode-out: e.g. fit on selected kinds in training episodes, then test a held-out kind in held-out episodes. Removing one label column is insufficient if its outputs, failures, features, or related examples were used for fitting/selection. Bind the target rule explicitly, and audit simultaneous obligations and format/delivery coupling. Language's constant-positive pilot-7 written-only target cannot support a binary genericity claim. Three usable kinds and eight repeatedly exposed episodes make this a diagnostic, not a strong universality test.

The documented handoff exposure table (`results/HANDOFF-astra.md`, “Exposure table and successor lineage,” correction 7) reports:

| Bank / episodes | Documented exposure and permitted role |
|---|---|
| Admission1 338 messages / 218 spans; Admission2 330/207 | Historical evaluation/reviews and error-informed development; exposed diagnostics, not fresh confirmation. |
| Admission3 357/385 | 44c/46 audits and pass3 convention feedback; development/diagnostic only. |
| Admission4 320/349 | No check48 model evaluation, but heldout3/4 annotation feedback fed training preparation; retire as pristine confirmation for that recipe. |
| Relations1 594 rows | Historical CPU evaluation and later operating-policy/development feedback; exposed diagnostic. |
| Relations2 357 rows | GPU/v2/v3 evaluation and error analysis; 90 Astra2 evaluation-derived relatives; v2 seed0 DEV includes all90, seeds1/2 fit30 each. Quarantine all90 and relatives from clean fits. |
| Relations3 448 rows | v3/46 audits, pass3 conventions, reported frozen-v2 replay; exposed diagnostic. |
| Relations4 320 rows | No check48 model evaluation, but pass3 heldout3/4 feedback reached training preparation; retire as pristine confirmation. |
| SLAB DEV slab2-dev-00..07 | Pilots1–7/reviews, repeated model looks and harness/scorer/renderer repairs; development/frozen replay only. Earlier SLAB pilot DEV00 uses the older slab-dev naming/recipe. |
| SLAB evaluation 64 frozen authored episodes | Pre-freeze IDs/hashes/manifest documented; running owner's one-shot instantiation and registered R/N/T64,Q16. No outcomes read here. Preserve frozen evaluation; retire as pristine after exposure. Tags alone do not prove family withholding. |
| Check49/51 families | Check51 source overrun exposed four evaluation-generator branches; exclude all four from fresh successor confirmation. |

Bank names expand to `data/classifier/heldout/fable-{admission,relations}-heldout{,-2,-3,-4}.jsonl`; **none were opened for this report**. Likewise, the 64 evaluation episode contents were not opened and their exact individual IDs were not enumerated here. Historical exposure is reported from the handoff, not inferred to be absent where records are incomplete. The handoff additionally warns that missing scenario IDs and different authors/domains do not establish paraphrase independence; quarantine `data/classifier/relations/astra-enrich-2.jsonl`'s 90 evaluation-derived rows and relatives.

**Future fit data-lineage line (fill fold IDs before fitting):**

> fit-on = saved pilot-7 authored SLAB DEV training-episode IDs only, frozen observed/written eligibility and obligation-specific labels; development/calibration-on = disjoint DEV episode IDs, all arms/rounds/versions/duplicates grouped; diagnostic-evaluated-on = held-out DEV episode IDs (historically exposed, not pristine confirmation), with separately registered leave-obligation-kind-out folds; confirmatory-evaluated-on = a future unopened, independently authored/family-audited bank, never used for fit, calibration, selection, examples or recipe design; excluded = running 64-episode SLAB evaluation prompts, responses, labels and derivatives, all benchmark prompts/responses, exposed evaluation-derived relatives; hidden features = frozen-model HF teacher forcing of saved DEV token IDs, extraction only after GPU release and authorization.

For this inventory itself: **fit-on none; development-accounted-on saved pilots 5/6/7 and earlier hidden-array metadata; larger-test checkpoint count only; no evaluation-content or benchmark reads.**

Fitting/tuning on the larger test's checkpoint labels, selecting episodes/thresholds/interventions from its emerging results, teacher-forcing its prompts for fit features, or using its outputs as contrastive examples would contaminate its evaluation bank. Changing its model, code, renderer, admission policy, container, flags or resource conditions would also disturb the running experiment. Waiting until completion does **not** convert its evaluation records into clean training data: any later repurposing must retire the bank and require a new confirmation set. Benchmark prompts **and recorded model responses** remain excluded from fit, selection and tuning.

**7. VERDICT**

**A small exploratory contrastive fit is feasible from existing DEV data; a validated generic alignment probe is not yet supported.** No probe fitting can run in this CPU-only task, and hidden-state extraction must wait for GPU release. The minimum useful version is a **CPU pre-generation text baseline first**, using pilot-7 episode-grouped folds; a post-generation validator already answers these four adherence questions exactly.

For a subsequent hidden-state diagnostic, use pilot-7 R/N/T written-only contrasts: **87 distinct records; indent 10 cells across 4 episodes, format 16 across 4, delivery 9 across 7; no binary language contrast**. One last-prompt vector at five layers costs **1,781,760 raw bytes** and **11.442507 projected prefill minutes**; retaining both prompt and body pools costs **3,563,520 bytes**, **596,042 forwarded tokens / 87 passes / 12.071689 projected minutes**. Actual HF extraction time and reload overhead remain unmeasured. Fit a regularized linear classifier on CPU after extraction; do not present the projection as the runtime of training plus extraction. Pair-enriched data change prevalence: calibration and evaluation need all eligible held-out rounds, not only disagreement cells, so a proper held-episode assessment may require the full pilot-7 extraction (512 passes; 34.413454 projected minutes for prompt+body).

Using all pilots would cost **1,664 passes / 143.489986 projected minutes**, versus **918 / 92.176244** for observed matched endpoints only. More rows here do not cure the eight-episode limitation, repeated-arm duplicates, different histories, or changed label definitions. Start with pilot 7 rather than silently pooling the old targets.

**We need not wait for the larger test to prepare or fit a DEV diagnostic. We should wait for its frozen completion and authorized audit before making claims based on its outcomes; its records must not become this fit's training set.** A credible generalization claim still needs a prospective untouched evaluation bank and measured extraction cost. The 4B judge fallback is not justified by these mechanically checkable labels; reserve that question for separately labeled nonmechanisable obligations.

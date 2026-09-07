# Quick check 40f for gpt-6-astra: RELEASE — router bias + masking the model's own prior answers (2026-09-05)

Source: results/quick-checks/check40d/README.md (PARTIAL: SET/HOLD/BACK 32/32 with alpha 3; SWITCH 0/32 and CLEAR
0/32 — once JavaScript answers are in the retained history, neither the flipped bias nor OFF changes the language;
the text cue switches 32/32 but its uncued CLEAR also stays JS 32/32). Interpretation (consistent with checks 35-38):
the model's own prior answers dominate; release needs the context lever. Hypothesis: SWITCH/CLEAR succeed when the
bias change is combined with MASKING the model's own prior code answers (position-preserving eviction, as in
check 35 c2 / KVCache.evict; equivalent to an attention mask; nothing deleted from text history).
Reuse 40d plumbing, frozen JS/Python directions, alpha 3, 64-token caps, 32 retained-history episodes, seeds 40060.
Arms at SWITCH (bias -> Python direction) and CLEAR (bias OFF): (R1) bias change only (replicate 40d); (R2) bias change
+ mask all prior assistant code answers (keep user turns and neutral pairs); (R3) mask only, bias unchanged (control:
should NOT switch); (R4) bias change + mask + a one-line neutral placeholder assistant body where masked (turn structure
kept); (T) text cue + mask (bar). Also HOLD after SWITCH (does the new language persist with bias sustained?).
READING (fixed before running): RELEASE WORKS if R2 (or R4) reaches Python >= 26/32 at SWITCH and Python >= 26/32 at
CLEAR with breakage <= 2/32 and R3 <= 4/32 switched; PARTIAL if one of the two passes; else NOT — state plainly whether
release requires the context lever (masking) in addition to the weight-side lever (routing).
Cost cap 1.5 GPU-h (project first; 24 episodes if needed, recorded). RUNNING.flag protocol; never signal. Unregistered,
disclosed; outputs under results/quick-checks/check40f/; item 40f in results/quick-checks/README.md (5 lines);
WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for results); no push. Foreground only; never
terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL cohort contents; nothing
fit or trained.

# Check 47 CPU settling replay — registration (2026-09-06)

Registered before implementation and replay. User-authorized record correction;
check 47's registered STAY verdict and SLAB-2 remain unchanged.
Fit-on: nothing. Evaluated-on: only the 32 saved dense and 32 saved MoE R replies
for SLAB DEV00/01 already exposed by check 47; no model calls or benchmark reads.

The replay-only SLAB v1 tolerance set is `trailing_closer`, `lift_report`,
`test_path`, plus the fourth sibling `strip_leading_fence`. After outer whitespace,
accept exactly one leading line of ```json or ``` followed by a newline and a
complete envelope. Remove an optional final standalone ``` line (outer whitespace
allowed). An absent closing fence is accepted only when the JSON envelope is
complete; never complete JSON, extract a prefix, accept prose or multiple blocks.
The frozen parser still validates the interior with its three existing tolerances.
Journal `strip_leading_fence` once per accepted reply, with `closed` true/false;
retain the existing per-call tolerance journal. Apply identically to both trunks.
No live parser or SLAB-2 edit: enable the fourth tolerance in an isolated copy of
SLAB v1 from freeze `184cb321`, shared by its Executor and checker.

Replay literal saved outputs in round order on a fresh persistent workspace per
trunk/episode, using frozen `materialize`, `Executor.run`, and `check` (the exact
consumer sequence in `PilotJournal.finish`). Preserve original caps. First verify
untolerated replay reproduces saved execution, outcomes and artifact hashes;
then enable the tolerance and replay all 64 replies. Pin source/input hashes.
Report executed-response counts, caps, breakage, final-turn success, all seven
violation kinds, round-0 indent compliance, and per-reply/per-event tolerance use.
Compare saved rendered prompts to identify truly matched pairs. All 32-round totals
are descriptive only: 2 round-0 pairs match, the other 30 answer divergent histories;
CPU execution cannot generate the replies that corrected feedback would elicit.
Test accepted/rejected fence boundaries through the frozen Executor and checker.
CPU only, foreground, no container, process signals, GPU, model rerun or push.

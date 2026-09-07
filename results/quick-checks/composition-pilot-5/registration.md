# Pilot 5 execution registration — before GPU

User brief governs this DEV-only run over later CPU defaults. Fit/train none;
evaluate authored DEV00–07 only; no evaluation bank or data/bench reads.
Pinned clean source: 9f0c6d27f32815010c81a02d3959102459c55e8f in
/tmp/stencil-pilot5-pinned. H1–H3/M4–M7 and N1/N2 fixes already committed.
Runtime-only amendment: cap 1024 and matching system wording (user instruction;
fable H2 explicitly permits registering this bet); no Q, no external API.
Execution gate means parsed trailer AND file written: exclude syntax/parse-depth
failures even though legacy Executor.executed calls these attempts executed.
Per-arm >=90%, cap <=2%; no pooled gate substitution. Floor fixed from all128 T
rounds before success scoring; only substitution traits indent/style and
delivery/process count toward >=2 kinds with denominators in >=2 episodes.
R final >=5/8. Report every other floor trait and descriptive relapse denominator.

Schedule: eight round-zero R DEV prompts, C4 groups00–03 then04–07, repeat reverse
07–04 then03–00; token IDs including EOS, text, stop/cap must match all8 or stop.
Then same-arm fixed groups of four episodes00–03 and04–07, independent dependent-
round lanes, T then R then N (T first freezes floor before success);16 rounds.
Optional O only if measured R arm wall x1.25 fits remaining time plus180s; DEV O
is gold R; absent O uses explicitly labelled R-cost proxy (no direct O claim).
No Q cost charged: user's registered run is R/N x64 + O/T x16.
Projection = (measured startup + 1.25*[64*(mean R+mean N)+16*(mean O+mean T)])/3600.
Lane allocations = same-arm group wall/4, plus equal share of GPU-held main
non-group overhead. Same C4 grouping required in larger run. Prior pilot spend
excluded by user; pre-run replay is development overhead, disclosed separately.
If projection is(12,15]h, report12-round proportional estimate and attempt fresh
complete frozen12-round R/N/T only if remaining budget permits; otherwise fallback
UNVALIDATED/INELIGIBLE. >15h stops, no arm/episode shrinking.

5400s includes startup, replay, all inference, cleanup. Stop new calls with180s
left; HTTP timeout <=remaining minus60s; only this task's Docker stop/rm permitted.
One qualified image/flags, no startup remedies. Own flag acquired under review lock;
wait for other flags/compute; never signal host processes. Raw per-round records,
output/prompt hashes, tolerances, timings and HTTP files written same-run. Raw HTTP
and loop journals stay out of git with SHA256 manifest. Explicit commits, no push.

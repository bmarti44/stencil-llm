# Saved-artifact verification

The diagnostic runner and tests froze before setup in commit6041e2d7. The
post-run observer scripts do no model inference and cannot change arm records.

1. Runner audit replays C/C' register updates from saved classifier outputs,
   reconstructs oracle events, recomputes v3 endpoint counts, checks scores and
   verifies each arm/probe prompt uses exactly the original arm history. It
   recomputes token/text/semantic and score changes for every probe.
2. Independent observer `scripts/audit_focus3_diag.py` reconstructs O/N/T live
   sets, raw rendered requests, full prompts, assistant pair closure and token
   decoding; verifies raw-logit softmax probabilities, no masks, trace/record
   identity, record counts and post-O resource selection. Both operate on saved
   evidence only. This is a separate calculation in the same agent session,
   not an independent author/model review.
3. Each false-admission case has original and O/N/T answers at all subsequent
   turns, exact rendered exposure, later row statuses and linked probe records.
   Probe effects are conditional current-recap effects, not the total causal
   effect of avoiding admission or purging earlier polluted answer history.
4. Source/checkpoint hashes, registration prefix and final tracked artifact
   membership are verified; no prior diagnostic or gate artifact is overwritten.

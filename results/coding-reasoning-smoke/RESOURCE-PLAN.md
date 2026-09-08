# Thinking compatibility resource plan — prospective

Two render calls and two nonstreaming generations, at most2048 output tokens
each, thinking budget512 per call; no retries. These are technical limits, not
claims of sufficient semantic reasoning or evidence about automatic focus.

The completed run-01 effective completion rate is18.812468347567442 tokens/second
including its HTTP/prefill cost. Linear output projection4096/rate=217.72794108
seconds. Reserve600startup+60cleanup+120other/uncertainty=780seconds, giving an
illustrative997.72794108seconds. A hard1200second owned reservation contains the
whole check, leaving202.27205892seconds beyond that estimate. The effective rate
and allowance are not worst-case guarantees; timeout produces INCOMPLETE, with
partial receipts and owned cleanup, without relaunch or cap/prompt rescue.

This is below the existing3600second ceiling for a qualified quick check. No
larger run or expanded budget is authorized here. Its actual cost must be counted
in any later plan for this candidate; neither unused reservation nor early exit
creates a new budget. Current resource exclusivity and exact frozen source/data
bindings must be checked immediately before any launch.

Sol implementation commit181cdf70995affc1b0361d6bb1ac7b85c32b1259 passes20targeted
tests in1.68seconds plus Ruff, both help paths and a dry run. Root generated the
canonical CPU preview with zero model calls:
preview.json SHA 0cda62aaf01276ea694eff8ee6a9860590d49dd26b274c4cbcb3d98a391b91bc.
The launcher preservation correction is commit3c89fd111d6cdfc25789f457cc63f2527446c162;
its seven targeted launcher tests passed in0.70seconds after the new regression
failed before the fix. Ruff, help and dry-run passed. Only launcher/test source
bindings changed from preview-r1.json; request, fixture and resource fields are
identical. The initial resource snapshot is retained in RESOURCE-PLAN-r1.md.
It binds14code/tokenizer inputs and the embedded technical fixture; the launcher
additionally binds its reused ownership helper and existing trunk manifest.
The cold serialized request is353local tokens,2401including the output allowance.
This is explicitly not a native prompt count or a guarantee about later generated
history. Exact server-native rendering must pass before either decode; a later
capacity failure ends the check without shortening its actual history.

Execution requires independent scored Astra readiness review and must freeze
the accepted review, this plan, brief, preview and all code/tokenizer/trunk inputs
after root independently checks the final review's score and open findings.
No inference or semantic-bank access occurred during preparation.

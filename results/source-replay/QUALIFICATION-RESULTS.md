# Original-source replay: technical qualification

2026-09-08. Technical delivery succeeded on the single registered mechanical
fixture. Independent result review is pending; this is not a coding utility
comparison or proof of generalized automatic focus.

The unchanged original Qwen3-30B-A3B completed one IDs-only selector call and one
coding-worker call. The selector chose the sole eligible original message m01;
the renderer copied it exactly as historical evidence. The worker's function
replacement was accepted and passed all three fixture checks. These observations
do not test difficult source selection, changed requirements, or superiority to
ordinary history/manual reminders.

| Measurement | Observed |
| --- | ---: |
| Whole lifecycle, including cleanup | 439.667978465 seconds |
| Through positive terminal publication | 439.674058504 seconds |
| Launch to driver start | 432.781308174 seconds |
| Driver execution | 3.725712025 seconds |
| Selector prompt / completion tokens | 379 / 10 |
| Worker prompt / completion tokens | 447 / 46 |
| Selector render / generation HTTP time | 0.011698221 / 1.516775452 seconds |
| Worker render / generation HTTP time | 0.006676103 / 1.993496948 seconds |

Both calls finished with stop, below their unchanged 128/1024 caps. Total usage
was 826 prompt plus 56 completion tokens. The root reconciled all ten recorded
raw HTTP/body representations against hashes, byte lengths, base64 and parsed
JSON; render and generation used identical request bytes, rendered prompt IDs
matched generated-response prompt IDs, and reported token counts matched IDs.
The response usage's optional null prompt_tokens_details is retained in raw
responses; the consumer's normalized usage retains the three numeric totals.
An initial root audit assertion incorrectly equated those object shapes; it was
corrected to compare numeric fields, without altering any run artifact or result.

The launcher and driver exited zero. Cleanup logs, stop and remove commands all
exited zero. The running flag is absent; post-run Docker and GPU process queries
were empty. Exec session7129 is terminal and must not be repolled or restarted.
The machine terminal is ELIGIBLE. The frozen fixture, code, prompt, cap and
preflight bytes were unchanged during the run. No retries or runtime repairs
occurred. Root revalidated the exact freeze before subsequent review append.

The measured slowest render time for the prospective screen formula is
r=0.011698220972903073 seconds. The later gate still uses the registered
2041.199447651-second historical generation estimate, 600-second startup
allowance, actual project check count C and maximum CPU check time q. Short
fixture throughput does not replace that estimate. No four-project data exists
yet, so full-screen affordability has not been evaluated or claimed.

The next permitted stage is fresh four-project preparation and the paired H/S/R
consumer under the existing accepted specification. A useful result there would
only justify preparing the larger untouched evaluation required by the goal.
Automating useful manual reminders remains a meaningful benefit; no prose-
superiority or perfect-selector prerequisite is introduced.

Evidence: qualification-run-01/ contains original calls, workspace states,
checks, lifecycle and cleanup receipts. qualification-root-audit.json binds its
artifacts. qualification-freeze.json SHA
903f8382d12ebaafd15515e2828bdad510f08fc28e282b3ae8771bba8a70c54b
binds the launch-time canonical Round4 review SHA
f9a082a7d80222165b781ecd139910c628578a51bcbeb3a491136b0fb57ae165
archived in commit260bbca0 (also present in launch commit6ec12be8). Later review
rounds are append-only; the historical launch review is recoverable from those
commits and is not silently replaced in the frozen run.

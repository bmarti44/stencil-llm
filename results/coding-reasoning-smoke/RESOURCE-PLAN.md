# Thinking compatibility resource plan — prospective draft

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

Readiness is pending implementation, CPU preview and independent Astra xhigh
review. The final preview must bind the embedded technical fixture, exact code,
existing tokenizer/trunk and real local prompt sizes, without inference or
semantic-bank access. Server-native render remains authoritative per call.

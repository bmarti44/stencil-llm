#!/usr/bin/env bash
set -u
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
OUT=/home/bmarti44/stencil-llm/data/classifier/kimi-scope
mkdir -p "$OUT"
DOMAINS=(
"software-engineering-pair-programming" "customer-support-chat" "travel-and-booking-agent" "personal-assistant-scheduling"
"creative-writing-collaboration" "academic-tutoring" "data-analysis-with-tools" "devops-incident-response"
"legal-document-drafting" "medical-intake-and-triage" "recipe-and-meal-planning" "home-renovation-planning"
"sales-crm-agent-with-tools" "email-drafting-and-etiquette" "language-learning-practice" "financial-planning-chat"
"game-master-roleplay" "research-literature-review" "hr-and-recruiting" "shell-and-file-operations-agent"
"web-browsing-agent" "children-story-writing" "fitness-coaching" "translation-and-localization"
"product-management-specs" "scientific-code-and-notebooks" "smart-home-control-agent" "event-planning"
"journalism-and-fact-checking" "therapy-style-supportive-chat" "ecommerce-order-management-tools" "system-prompt-personas"
"multilingual-mixed-casual" "long-agentic-task-with-many-tool-calls" "negotiation-and-procurement" "teaching-assistant-grading"
"newsletter-and-blog-writing" "technical-documentation" "slide-deck-and-report-writing" "poetry-and-lyrics"
)
i=0
for d in "${DOMAINS[@]}"; do
  f="$OUT/$d-scope.jsonl"
  [ -s "$f" ] && continue
  python3 "$S/kimi_gen_scope.py" "$d" 90 "$((9000 + i))" "$f" >> "$S/gen_scope.log" 2>&1 &
  i=$((i + 1))
  while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 5; done
done
wait
echo "GEN_SCOPE_DONE $(cat "$OUT"/*.jsonl | wc -l) rows" >> "$S/gen_scope.log"

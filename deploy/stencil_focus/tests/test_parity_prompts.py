"""Parity gate, prompt half (CPU): the package renders byte-identical prompts to the
research runtime on every LONG item (both flag states). Needs the research repo."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ITEMS = REPO / "results" / "memorycode-long" / "items.json"


@pytest.fixture(scope="module")
def research():
    if not ITEMS.exists() or not (REPO / "vendor" / "memorycode").exists():
        pytest.skip("research repo artifacts not present")
    sys.path.insert(0, str(REPO / "src"))
    from tokenizers import Tokenizer
    from transformers import AutoTokenizer

    from stencil import memorycode as mc

    return (
        mc,
        Tokenizer.from_file(str(REPO / "models/qwen3-1.7b-hf/tokenizer.json")),
        AutoTokenizer.from_pretrained(str(REPO / "models/qwen3-1.7b-hf")),
    )


@pytest.mark.repo
def test_prompt_parity_all_long_items(research):
    from stencil_focus import Session

    mc, rtok, htok = research
    items = [
        it for it in json.loads(ITEMS.read_text())["items"] if it["split"] != "reserve"
    ]
    assert len(items) == 144
    mismatches = []
    for item in items:
        dialogue = mc.load_dialogue(item["dialogue"])
        s, query = item["session"], item["queries"][0]
        head, sep, request = mc.long_request(dialogue, query)
        # research: base and focus (role_evicted) prompts
        base = mc.build_long_prompt(dialogue, s, query, rtok, "")
        prefix = base["prompt"].index(":\n") + 2
        kept_thread = base["prompt"][prefix : base["prompt"].index(" \nBased on")]
        evicted = mc.evicted_mentor_sentences(dialogue, s, kept_thread)
        kept, _ = mc.pack_long(evicted, rtok)
        focus = mc.build_long_prompt(
            dialogue, s, query, rtok, mc.render_long_reminder(kept)
        )
        for flag, expected in ((False, base["prompt"]), (True, focus["prompt"])):
            session = Session(htok, focus=flag)
            for role, text, rendered in mc.focus_session_messages(dialogue, s):
                session.add_message(role, text, rendered=rendered)
            got = session.build_prompt(request, head=head, separator=sep)
            if got != expected:
                mismatches.append((item["id"], flag))
    assert mismatches == []

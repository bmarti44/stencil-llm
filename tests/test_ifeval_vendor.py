# ruff: noqa: E501
"""B0.2 vendored-verifier goldens: a POSITIVE and a TARGETED-NEGATIVE
fixture for every one of the 25 instruction classes present in the 541
(registered requirement). langdetect's internal randomness is pinned
here exactly as the runner will pin it. Fixture lesson: language checks
need realistic-length text (2-word all-caps reads as Somali)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))
import langdetect
langdetect.DetectorFactory.seed = 0  # the runner's pin, mirrored

from ifeval import instructions_registry  # noqa: E402

EN = ("The weather report for today indicates sunshine across the valley "
      "with a gentle breeze arriving before the afternoon begins.")
EN2 = "Here is a second complete English sentence about gardens and rivers."

# (instruction_id, kwargs, passing_response, failing_response)
GOLDENS = [
    ("change_case:capital_word_frequency", {"capital_relation": "less than", "capital_frequency": 3},
     f"{EN} Only ONE capital word here.", "MANY FULLY CAPITAL WORDS APPEAR HERE TODAY."),
    ("change_case:english_capital", {},
     "THE WEATHER REPORT FOR TODAY INDICATES SUNSHINE ACROSS THE VALLEY WITH A GENTLE BREEZE ARRIVING BEFORE THE AFTERNOON BEGINS.", EN),
    ("change_case:english_lowercase", {},
     EN.lower(), EN),
    ("combination:repeat_prompt", {"prompt_to_repeat": "Write a poem about rain."},
     f"Write a poem about rain. {EN}", f"{EN} A poem follows."),
    ("combination:two_responses", {},
     f"{EN}\n******\n{EN2}", EN),
    ("detectable_content:number_placeholders", {"num_placeholders": 2},
     f"Dear [name], meet me at [address]. {EN}", f"Dear [name], hello. {EN}"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."},
     f"{EN}\nP.S. Bring an umbrella.", EN),
    ("detectable_format:constrained_response", {},
     "My answer is yes.", EN),
    ("detectable_format:json_format", {},
     '{"weather": "sunny", "wind": "gentle"}', EN),
    ("detectable_format:multiple_sections", {"section_spliter": "SECTION", "num_sections": 2},
     f"SECTION 1\n{EN}\nSECTION 2\n{EN2}", EN),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2},
     "* first item about weather\n* second item about wind", f"* only one item\n{EN}"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2},
     f"*sunny valley* and *gentle breeze* {EN}", EN),
    ("detectable_format:title", {},
     f"<<Weather Notes>> {EN}", EN),
    ("keywords:existence", {"keywords": ["sunshine", "breeze"]},
     EN, EN2),
    ("keywords:forbidden_words", {"forbidden_words": ["sunshine"]},
     EN2, EN),
    ("keywords:frequency", {"relation": "at least", "keyword": "garden", "frequency": 2},
     f"The garden grows; another garden rests. {EN2}", EN2),
    ("keywords:letter_frequency", {"let_relation": "at least", "letter": "z", "let_frequency": 3},
     f"Zigzagging zebras zoomed. {EN}", EN),
    ("language:response_language", {"language": "en"},
     EN, "El clima de hoy es soleado en todo el valle con una brisa suave."),
    ("length_constraints:nth_paragraph_first_word", {"first_word": "weekend", "num_paragraphs": 2, "nth_paragraph": 1},
     f"weekend plans begin early.\n\n{EN}", f"{EN}\n\n{EN2}"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2},
     f"{EN}\n***\n{EN2}", EN),
    ("length_constraints:number_sentences", {"relation": "less than", "num_sentences": 3},
     EN, f"{EN} {EN2} A third sentence. A fourth sentence follows here."),
    ("length_constraints:number_words", {"relation": "at least", "num_words": 30},
     f"{EN} {EN2} Extra words extend this response beyond the requested threshold easily.", "Too short."),
    ("punctuation:no_comma", {},
     EN.replace(",", ""), f"First, {EN}"),
    ("startend:end_checker", {"end_phrase": "That is all."},
     f"{EN} That is all.", EN),
    ("startend:quotation", {},
     f'"{EN}"', EN),
]


def _check(iid, kwargs, response):
    cls = instructions_registry.INSTRUCTION_DICT[iid]
    inst = cls(iid)
    inst.build_description(**kwargs)
    return inst.check_following(response)


def test_every_class_has_goldens():
    import json
    rows = [json.loads(line) for line in open(Path(__file__).resolve().parent.parent / "data" / "bench" / "ifeval_input_data.jsonl")]
    present = {i for r in rows for i in r["instruction_id_list"]}
    covered = {iid for iid, *_ in GOLDENS}
    assert covered == present, present ^ covered


def test_positive_goldens_pass():
    for iid, kwargs, pos, _ in GOLDENS:
        assert _check(iid, kwargs, pos), f"positive golden failed: {iid}"


def test_negative_goldens_fail():
    for iid, kwargs, _, neg in GOLDENS:
        assert not _check(iid, kwargs, neg), f"negative golden passed: {iid}"

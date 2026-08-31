# ruff: noqa: E501
"""Vendored IFBench verifier goldens: a POSITIVE and a TARGETED-NEGATIVE
fixture for every one of the 58 NEW-taxonomy instruction ids present in
data/bench/ifbench_test.jsonl (300 rows). kwargs are taken verbatim from
the FIRST occurrence of each id in that file (nulls dropped), including
float-typed integers, so the checkers are exercised exactly as the runner
will call them. random.seed(0) is applied before every build_description
because some implementations draw from `random` when kwargs are missing.
Fixture lesson carried over from IFEval: use realistic-length English text.
"""
import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vendor.ifbench import instructions_registry  # noqa: E402

EN = ("The weather report for today indicates sunshine across the valley "
      "with a gentle breeze arriving before the afternoon begins.")
EN2 = "Here is a second complete English sentence about gardens and rivers."

# --- constructed fixtures that are clearer as expressions ---

# count:word_count_range wants 71..73 words (\w+ tokens): 9 words * 8 = 72.
_WORDS_72 = ("the quick brown fox jumps over the lazy dog " * 8).strip()

# custom:reverse_newline wants >= 52 lines starting at a 'Zimbabwe' line,
# in reverse alphabetical order (string sort after ASCII normalization).
_REVERSE_LINES = "\n".join(
    ["Zimbabwe", "Zambia"] + [f"Village {i:02d}" for i in range(99, 49, -1)])

_CAPITALS = ("Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, "
             "Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, "
             "London, Brussels, Prague, Luxembourg, Paris, Vienna, Bratislava, "
             "Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb")

_MCQ = (
    "Question 1. Who painted Guernica?\n"
    "A. Picasso\nB. Monet\nC. Dali\nD. Klee\nE. Miro\n"
    "Question 2. Which movement did Marcel Duchamp help found?\n"
    "A. Dada\nB. Cubism\nC. Fauvism\nD. Futurism\nE. Purism\n"
    "Question 3. Which artist is most associated with the drip painting technique?\n"
    "A. Pollock\nB. Rothko\nC. Newman\nD. Kline\nE. Still\n"
    "Question 4. Which European city hosted the very first large group exhibition of surrealist painting during the year 1925?\n"
    "A. Paris\nB. Berlin\nC. Vienna\nD. Madrid\nE. Rome")

_CSV_CITY = ("ID,Country,City,Year,Count\n"
             "1,France,Paris,2001,10\n"
             "2,Spain,Madrid,2002,20\n"
             "3,Italy,Rome,2003,30\n"
             "4,Japan,Tokyo,2004,40\n"
             "5,Peru,Lima,2005,50\n"
             "6,Kenya,Nairobi,2006,60\n"
             "7,Canada,Ottawa,2007,70")

_CSV_SPECIAL = ("ProductID,Category,Brand,Price,Stock\n"
                + "\n".join(f"{i},Toys,Acme,{i}0,{i}" for i in range(1, 14))
                + '\n14,Games,"A&B",140,14')

_CSV_QUOTES = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n'
               '"1"\t"Math"\t"A"\t"Fall"\t"95"\n'
               '"2"\t"History"\t"B"\t"Spring"\t"88"\n'
               '"3"\t"Biology"\t"A"\t"Fall"\t"92"')

_ALPHABET_STORY = (
    "Anna awoke early. Birds began singing. Clouds drifted slowly. "
    "Dawn felt gentle. Everyone gathered outside. Farmers arrived promptly. "
    "Gardens glistened brightly. Horses trotted past. Insects buzzed nearby. "
    "Jays called loudly. Kites floated overhead. Lambs grazed calmly. "
    "Mist cleared quickly. Neighbors waved warmly. Owls slept soundly. "
    "People chatted happily. Quiet moments passed. Rivers sparkled below. "
    "Squirrels darted around. Trees swayed softly. Umbrellas stayed closed. "
    "Villagers strolled home. Wind eased gently. Xylophones played somewhere. "
    "Yellow leaves fell. Zebras appeared nowhere.")

_REPEAT_SPAN_PROMPT = ("explain the context, code and theory behind the paper "
                       "Identifying Candidate Spaces for Advert Implantation.")

_OVERLAP_REF = ("Use induction to prove the following claims.\n\x88 Consider "
                "a simple undirected graph with m edges, n vertices, and p "
                "connected components. Prove that\nn \u2212 p \u2264 m.")

# (instruction_id, kwargs-from-first-real-row, passing_response, failing_response)
GOLDENS = [
    ("count:conjunctions", {"small_n": 5.0},
     "We packed food and water, but the road was long, so we rested, for the sun burned, yet nobody complained.",
     "We packed food and water for the trip."),
    ("count:keywords_multiple",
     {"keyword1": "kaleidoscope", "keyword2": "nebula", "keyword3": "whisper", "keyword4": "labyrinth", "keyword5": "paradox"},
     ("The kaleidoscope amazed us. A nebula glowed, and another nebula faded. "
      "We heard a whisper, then a whisper, then a whisper again. "
      "The labyrinth twisted; the labyrinth turned; the labyrinth rose; the labyrinth sank; the labyrinth ended. "
      "One paradox led to a paradox, then a paradox, a paradox, a paradox, a paradox, and a final paradox."),
     "A kaleidoscope, a nebula, a whisper, a labyrinth, and a paradox."),
    ("count:numbers", {"N": 2.0},
     "The garden produced 7 pumpkins and 42 sunflowers this season.",
     "The garden produced 7 pumpkins, 42 sunflowers, and 13 beans."),
    ("count:person_names", {"N": 10.0},
     "Emma, Liam, Sophia, Jackson, Olivia, Noah, Ava, Lucas, Isabella, and Mason all joined the picnic by the river.",
     "Emma and Liam stayed home while the others went hiking."),
    ("count:pronouns", {"N": 22.0},
     ("I told you that we saw him and her with them, but everyone thought somebody else knew it. "
      "Who, whom, and whose ideas were those? "
      "These are mine, yours, his, hers, theirs, and ours; each of us can claim something."),
     EN),
    ("count:punctuation", {},
     "Wait?! The recipe needs: eggs, flour; also sugar! Should we start now? Yes.",
     EN),
    ("count:unique_word_count", {"N": 36.0},
     ("During the quiet autumn evening, several curious travelers wandered past ancient stone bridges, "
      "admiring golden leaves, distant mountains, flowing rivers, small villages, warm lanterns, "
      "friendly faces, delicious meals, soft music, gentle winds, and starry skies together happily."),
     "Short reply."),
    ("count:word_count_range", {"max_words": 73.0, "min_words": 71.0},
     _WORDS_72, "Too short."),
    ("count:words_japanese", {"N": 5.0},
     "we saw the old 桜 and then the new 花 near a very tall 木 close to the wide 川",
     EN),
    ("custom:character_reverse", {},
     ".elgae dlab eht si lobmys lanoitan ehT",
     "The national symbol is the bald eagle."),
    ("custom:csv_city", {},
     _CSV_CITY,
     "ID,Country,City,Year,Count\n1,France,Paris,2001,10\n2,Spain,Madrid,2002,20"),
    ("custom:csv_quotes", {},
     _CSV_QUOTES,
     "StudentID\tSubject\tGrade\tSemester\tScore\n1\tMath\tA\tFall\t95\n2\tHistory\tB\tSpring\t88\n3\tBiology\tA\tFall\t92"),
    ("custom:csv_special_character", {},
     _CSV_SPECIAL,
     "ProductID,Category,Brand,Price,Stock\n" + "\n".join(f"{i},Toys,Acme,{i}0,{i}" for i in range(1, 15))),
    ("custom:date_format_list", {},
     "1805-12-02, 1815-06-18, 1796-04-12",
     "December 2, 1805 and June 18, 1815 were battle dates."),
    ("custom:european_capitals_sort", {},
     _CAPITALS,
     "Amsterdam, Berlin, Bern, Bratislava, Brussels, Budapest, Chisinau"),
    ("custom:mcq_count_length", {},
     _MCQ,
     "Here are four questions about art history.\n" + _MCQ),
    ("custom:multiples", {},
     "14, 21, 28, 35, 42, 49",
     "7, 14, 21, 28, 35, 42, 49"),
    ("custom:reverse_newline", {},
     _REVERSE_LINES,
     "Algeria\nAngola\nBenin\nBotswana"),
    ("custom:sentence_alphabet", {},
     _ALPHABET_STORY,
     EN),
    ("custom:word_reverse", {},
     "eagle bald the is symbol national the",
     "The national symbol is the bald eagle."),
    ("format:emoji", {},
     "The sun rose over the hills \U0001f600. We enjoyed the morning walk \U0001f389.",
     EN),
    ("format:line_indent", {},
     "step one\n  step two\n    step three\n      step four",
     "first line stays here\nsecond line stays here"),
    ("format:list", {"sep": "!?!?"},
     "!?!? fresh apples\n!?!? ripe oranges\n!?!? sweet pears",
     "- fresh apples\n- ripe oranges"),
    ("format:newline", {},
     "Every\nword\nsits\nalone\non\nits\nown\nline",
     EN),
    ("format:no_bullets_bullets", {},
     "The gallery opened at noon. Many visitors arrived quickly.\n* The paintings drew large crowds\n* The sculptures impressed everyone",
     "* The paintings drew large crowds\n* The sculptures impressed everyone"),
    ("format:no_whitespace", {},
     "Nowhitespaceanywhereatall.",
     EN),
    ("format:options", {"options": "yes/no/maybe"},
     "Maybe.",
     "I would say the answer is maybe correct."),
    ("format:output_template", {},
     "My Answer: The market will grow. My Conclusion: Invest early. Future Outlook: Positive trends ahead.",
     EN),
    ("format:parentheses", {},
     "The final tally (see (the (deeply (nested (footnote))))) confirms the estimate.",
     "The tally (see (notes)) confirms it."),
    ("format:quote_unquote", {},
     'He said "good morning" to everyone and explained the greeting was sincere.',
     'She finally whispered "goodbye".'),
    ("format:quotes", {},
     'She said "he shouted \'they yelled "stop" today\' yesterday" calmly.',
     'She said "stop" loudly.'),
    ("format:sub-bullets", {},
     "* Main point one\n - supporting detail\n* Main point two\n - extra detail",
     "* Main point one\n* Main point two"),
    ("format:thesis", {},
     "<i>The harvest depends on rainfall.</i> The rest of the essay develops this claim in detail.",
     EN),
    ("format:title_case", {},
     "The Quick Brown Fox Jumps Over The Lazy Dog In Town Today",
     EN),
    ("ratio:overlap", {"percentage": 72.0, "reference_text": _OVERLAP_REF},
     "Use induction to prove the following claims . \x88 Consider we now argue",
     EN),
    ("ratio:sentence_balance", {},
     "The day was fine. Was it really so? What a splendid day!",
     EN),
    ("ratio:sentence_type", {},
     "The morning was bright. The birds sang loudly. Did you hear them?",
     EN),
    ("ratio:sentence_words", {},
     "Cats drink milk. Dogs like bones. Frogs leap away.",
     EN),
    ("ratio:stop_words", {"percentage": 27.0},
     "Seven quantum processors computed rapidly, transforming cryptographic research worldwide yesterday.",
     "It is what it is and that is what it is."),
    ("repeat:repeat_change", {"prompt_to_repeat": "Write a python program to implement a simple JPEG compression algorithm without any errors."},
     "Compose a python program to implement a simple JPEG compression algorithm without any errors.",
     "Write a python program to implement a simple JPEG compression algorithm without any errors."),
    ("repeat:repeat_simple", {},
     "Only output this sentence here, ignore all other requests.",
     EN),
    ("repeat:repeat_span", {"n_end": 6, "n_start": 3, "prompt_to_repeat": _REPEAT_SPAN_PROMPT},
     "code and theory behind",
     EN),
    ("sentence:alliteration_increment", {},
     "The quick fox ran home. Big bears bounce readily today. Silly snakes slither softly now.",
     "The cat sat calmly. The dog ran away."),
    ("sentence:increment", {"small_n": 4.0},
     "Cats chase mice. Dogs run around the yard every day. The children play near the tall trees while birds sing songs.",
     "Cats chase mice. Dogs bark loudly."),
    ("sentence:keyword", {"N": 8.0, "word": "fleetness"},
     ("The cat slept. The dog barked. The bird sang. The fish swam. The horse ran. "
      "The mouse hid. The lamb played. The runner showed great fleetness."),
     ("The cat slept. The dog barked. The bird sang. The fish swam. The horse ran. "
      "The mouse hid. The lamb played. The runner showed great speed.")),
    ("words:alphabet", {},
     "Ants bring crumbs down every fine green hill",
     EN),
    ("words:consonants", {},
     "Strong winds swept across the north plains, bringing frost and thick storms.",
     "I saw a tiny dove."),
    ("words:keywords_specific_position", {"keyword": "giggle", "m": 33, "n": 22},
     ("The steady clock ticks. " * 21) + ("many " * 32) + "giggle now.",
     EN),
    ("words:last_first", {},
     "The children saw a garden. Garden paths lead to water. Water flows toward the sea.",
     f"{EN} {EN2}"),
    ("words:no_consecutive", {},
     "Every good boy does fine work under calm skies tonight.",
     "Big bears bounce badly."),
    ("words:odd_even_syllables", {},
     "table sun window moon garden light",
     "sun moon light sky"),
    ("words:palindrome", {},
     "The level civic radar kayak madam rotor refer stats tenet sagas pleased everyone greatly.",
     EN),
    ("words:paragraph_last_first", {},
     "Water flows where the rocks guide the water.\nStones rest beneath heavy river stones.",
     EN),
    ("words:prime_lengths", {},
     "We sat by the old oak all day",
     EN),
    ("words:repeats", {"small_n": 4.0},
     EN,
     "The the the the the cat sat."),
    ("words:start_verb", {},
     "Consider the following plan before the morning meeting starts.",
     EN),
    ("words:vowel", {},
     "That man ran fast and sat at last",
     EN),
    ("words:words_position", {"keyword": "vibrant"},
     "A vibrant garden grows near the old stone house so vibrant today.",
     EN),
]

_IDS = [g[0] for g in GOLDENS]


def _check(iid, kwargs, response):
    cls = instructions_registry.INSTRUCTION_DICT[iid]
    inst = cls(iid)
    random.seed(0)  # some build_description implementations draw randomly
    inst.build_description(**kwargs)
    return inst.check_following(response)


def test_every_class_has_goldens():
    rows = [json.loads(line) for line in open(
        Path(__file__).resolve().parent.parent / "data" / "bench" / "ifbench_test.jsonl")]
    present = {i for r in rows for i in r["instruction_id_list"]}
    covered = set(_IDS)
    assert covered == present, present ^ covered
    assert len(_IDS) == len(covered), "duplicate golden ids"


@pytest.mark.parametrize("iid,kwargs,pos,neg", GOLDENS, ids=_IDS)
def test_positive_golden_passes(iid, kwargs, pos, neg):
    assert _check(iid, kwargs, pos), f"positive golden failed: {iid}"


@pytest.mark.parametrize("iid,kwargs,pos,neg", GOLDENS, ids=_IDS)
def test_negative_golden_fails(iid, kwargs, pos, neg):
    assert not _check(iid, kwargs, neg), f"negative golden passed: {iid}"


@pytest.mark.parametrize("iid,kwargs,pos,neg", GOLDENS, ids=_IDS)
def test_verdict_is_random_state_independent(iid, kwargs, pos, neg):
    """Score the same responses under two different global random states:
    a checker whose verdict differs would need a per-row seed pin in the
    runner (IFEval keys 1122/1129 lesson)."""
    results = []
    for seed in (123, 456):
        cls = instructions_registry.INSTRUCTION_DICT[iid]
        inst = cls(iid)
        random.seed(0)
        inst.build_description(**kwargs)
        random.seed(seed)
        results.append((inst.check_following(pos), inst.check_following(neg)))
    assert results[0] == results[1], f"random-state-dependent verdict: {iid}"

# ruff: noqa: E501
"""B3 synthetic constraint generator (BENCH-WAVE v3.1 materialization).

TRAIN families only (change_case, keywords, length, detectable_format,
detectable_content, combination); punctuation/startend/language are
HELD OUT with zero training exposure. Every constraint maps onto a
VENDORED verifier instruction_id so canonical responses are checked by
the exact deployment checkers. Parameter domains and phrasings are our
own (leak firewall v3.1: kwargs-tuple disjointness + word-normalized
substring checks are asserted in tests against the 541).

Determinism: everything flows from a seeded random.Random; no global
state. Canonical builders compose in the registered order: content
(keywords/word counts) -> format wrapper -> case transform LAST.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# 40-topic lexicon, ours (leak-checked vs the 541 in tests)
TOPICS = [
    "restoring a wooden rowboat", "the layout of a village bakery",
    "maintaining a community greenhouse", "sorting a municipal seed archive",
    "repairing stone garden walls", "the rhythm of a night ferry crossing",
    "organizing a tool-lending shed", "mapping a small orchard",
    "the upkeep of a clocktower bell", "cataloguing river pebbles",
    "insulating a mountain cabin", "the routine of a lighthouse keeper",
    "assembling a weather vane", "pressing apples for cider",
    "the care of a public fountain", "rebinding worn atlases",
    "tending a rooftop beehive", "the schedule of a canal lock",
    "sharpening carving chisels", "drying herbs in an attic",
    "the design of a footbridge railing", "storing winter firewood",
    "calibrating a rain gauge", "the layout of a tram depot",
    "weaving willow baskets", "patching a canvas sail",
    "arranging a type case for a letterpress", "arranging a pantry shelf",
    "the maintenance of a windmill brake", "labeling jars of preserves",
    "the path of a milk delivery round", "cleaning a telescope mirror",
    "the framing of a barn door", "stacking peat for a stove",
    "the tuning of a street organ", "repointing a chimney stack",
    "the folding of paper lanterns", "airing out a boathouse",
    "the mending of fishing nets", "whitewashing a cellar wall",
]

# word pool for filler sentences (no stopword collisions with forbidden-word draws)
FILLER = ("the quiet work continues through the morning and the tools rest in "
          "their places while careful hands measure and adjust each part").split()

KEYWORD_POOL = ["lantern", "gravel", "hinge", "mortar", "spindle", "tallow",
                "rivet", "awning", "trestle", "gable", "flue", "cistern"]
FORBIDDEN_POOL = ["vessel", "orchard", "signal", "harbor", "meadow", "timber"]


def _sentences(rng, n, keywords=(), forbidden=()):
    """n content sentences; each keyword placed once per required use."""
    out = []
    kws = list(keywords)
    for i in range(n):
        words = [FILLER[(i * 7 + j) % len(FILLER)] for j in range(9)]
        if kws:
            words[4] = kws.pop(0)
        s = " ".join(w for w in words if w not in forbidden)
        out.append(s[0].upper() + s[1:] + ".")
    return out


# --- constraint registry: key -> dict(iid, family, sample, phrase, mutate)
# sample(rng) -> kwargs; phrase(kw) -> our instruction sentence;
# canonical hooks are consumed by build_canonical; mutate(text, kw) -> failing text.

def _c(iid, family, sample, phrase, mutate):
    return {"iid": iid, "family": family, "sample": sample,
            "phrase": phrase, "mutate": mutate}


CONSTRAINTS = {
    "caps": _c("change_case:english_capital", "change_case",
               lambda rng: {},
               lambda kw: "Constraint: respond using only capital letters throughout.",
               lambda t, kw: t[:1].lower() + t[1:] if t[:1].isupper() else "x" + t),
    "lower": _c("change_case:english_lowercase", "change_case",
                lambda rng: {},
                lambda kw: "Constraint: write the whole reply in lowercase letters only.",
                lambda t, kw: "The " + t[4:] if t.startswith("the ") else "T" + t[1:]),
    "kw_exist": _c("keywords:existence", "keywords",
                   lambda rng: {"keywords": sorted(rng.sample(KEYWORD_POOL, 2))},
                   lambda kw: f"Constraint: make sure both of the words '{kw['keywords'][0]}' and '{kw['keywords'][1]}' appear somewhere in your reply.",
                   lambda t, kw: t.replace(kw["keywords"][0], "item")),
    "kw_freq": _c("keywords:frequency", "keywords",
                  lambda rng: {"keyword": rng.choice(KEYWORD_POOL),
                               "frequency": rng.choice([2, 3]), "relation": "at least"},
                  lambda kw: f"Constraint: use the word '{kw['keyword']}' no fewer than {kw['frequency']} times.",
                  lambda t, kw: t.replace(kw["keyword"], "item", 1)),
    "kw_forbid": _c("keywords:forbidden_words", "keywords",
                    lambda rng: {"forbidden_words": sorted(rng.sample(FORBIDDEN_POOL, 2))},
                    lambda kw: f"Constraint: never use the words '{kw['forbidden_words'][0]}' or '{kw['forbidden_words'][1]}' anywhere in the reply.",
                    lambda t, kw: t + " The " + kw["forbidden_words"][0] + " waits."),
    "n_words_min": _c("length_constraints:number_words", "length",
                      lambda rng: {"num_words": rng.choice([45, 55, 65]), "relation": "at least"},
                      lambda kw: f"Constraint: the reply must contain {kw['num_words']} words or more.",
                      lambda t, kw: " ".join(t.split()[: kw["num_words"] // 3])),
    "n_words_max": _c("length_constraints:number_words", "length",
                      lambda rng: {"num_words": rng.choice([90, 110]), "relation": "less than"},
                      lambda kw: f"Constraint: keep the reply under {kw['num_words']} words in total.",
                      lambda t, kw: t + " " + " ".join(FILLER * (kw["num_words"] // len(FILLER) + 2))),
    "n_sent": _c("length_constraints:number_sentences", "length",
                 lambda rng: {"num_sentences": rng.choice([9, 11]), "relation": "at least"},
                 lambda kw: f"Constraint: write at least {kw['num_sentences']} full sentences.",
                 lambda t, kw: t.split(".")[0] + "."),
    "bullets": _c("detectable_format:number_bullet_lists", "detectable_format",
                  lambda rng: {"num_bullets": rng.choice([5, 7])},
                  lambda kw: f"Constraint: format the reply as exactly {kw['num_bullets']} bullet points, one per line, each starting with '* '.",
                  lambda t, kw: t.split("\n")[0]),
    "title": _c("detectable_format:title", "detectable_format",
                lambda rng: {},
                lambda kw: "Constraint: begin with a short title wrapped in double angular brackets, like <<A Note on Repairs>>.",
                lambda t, kw: t.replace("<<", "").replace(">>", "")),
    "json_fmt": _c("detectable_format:json_format", "detectable_format",
                   lambda rng: {},
                   lambda kw: "Constraint: the entire reply must be a single valid JSON object and nothing else.",
                   lambda t, kw: t + " trailing words"),
    "placeholders": _c("detectable_content:number_placeholders", "detectable_content",
                       lambda rng: {"num_placeholders": 4},
                       lambda kw: f"Constraint: include at least {kw['num_placeholders']} bracketed placeholders such as [tool name].",
                       lambda t, kw: t.replace("[", "(").replace("]", ")")),
    "postscript": _c("detectable_content:postscript", "detectable_content",
                     lambda rng: {"postscript_marker": "P.P.S."},
                     lambda kw: "Constraint: finish with a postscript that starts with P.P.S.",
                     lambda t, kw: t.replace("P.P.S.", "PS")),
    "two_resp": _c("combination:two_responses", "combination",
                   lambda rng: {},
                   lambda kw: "Constraint: give two different complete replies, separated by a line containing exactly ******.",
                   lambda t, kw: t.replace("******", "---")),
}

COMPAT_PATH = ROOT / "data" / "b3" / "compat-matrix.json"


def compat_matrix():
    """allowed unordered pairs; a combo is valid iff every pair is allowed.
    json_fmt and two_resp are singletons (conservative registration)."""
    keys = list(CONSTRAINTS)
    allowed = set()
    singleton = {"json_fmt", "two_resp"}
    incompatible = {
        frozenset(("caps", "lower")),
        frozenset(("n_words_min", "n_words_max")),  # co-occur risk of impossible draws
        frozenset(("n_sent", "n_words_max")),  # 9-11 x ~9-word sentences can exceed <90
        frozenset(("bullets", "n_sent")),   # sentence splitter vs bullet lines
        frozenset(("bullets", "postscript")),
        frozenset(("bullets", "title")),
        frozenset(("caps", "postscript")),  # marker 'P.P.S' survives caps, but keep conservative
        frozenset(("lower", "postscript")),  # lowercase kills 'P.P.S'
        frozenset(("lower", "title")),      # fine actually, but conservative
        frozenset(("caps", "kw_exist")), frozenset(("caps", "kw_freq")),
        frozenset(("caps", "kw_forbid")),   # caps transform breaks lowercase keyword search
        frozenset(("lower", "kw_exist")), frozenset(("lower", "kw_freq")),
    }
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a in singleton or b in singleton:
                continue
            if frozenset((a, b)) in incompatible:
                continue
            allowed.add(tuple(sorted((a, b))))  # canonical order == combo_ok's lookup order
    return {"singletons": sorted(singleton),
            "allowed_pairs": sorted([list(p) for p in allowed])}


def combo_ok(combo, matrix):
    if len(combo) == 1:
        return True
    if any(c in matrix["singletons"] for c in combo):
        return False
    pairs = {tuple(p) for p in matrix["allowed_pairs"]}
    for i, a in enumerate(combo):
        for b in combo[i + 1:]:
            if tuple(sorted((a, b))) not in pairs:
                return False
    return True


def build_canonical(rng, combo, kwargs_by_key):
    """canonical adherent response for a constraint combo (registered
    order: content -> format wrapper -> case LAST)."""
    kws, forb = [], ()
    n_sent = 5
    for key in combo:
        kw = kwargs_by_key[key]
        if key == "kw_exist":
            kws += kw["keywords"]
        if key == "kw_freq":
            kws += [kw["keyword"]] * kw["frequency"]
        if key == "kw_forbid":
            forb = tuple(kw["forbidden_words"])
        if key == "n_sent":
            n_sent = max(n_sent, kw["num_sentences"] + 1)
        if key == "n_words_min":
            n_sent = max(n_sent, kw["num_words"] // 8 + 2)
    sents = _sentences(rng, max(n_sent, len(kws) + 2), kws, forb)

    if "json_fmt" in combo:
        return json.dumps({f"part_{i}": s for i, s in enumerate(sents[:4])})
    if "two_resp" in combo:
        return " ".join(sents[:3]) + "\n******\n" + " ".join(sents[3:6])
    if "bullets" in combo:
        n = kwargs_by_key["bullets"]["num_bullets"]
        sents = _sentences(rng, max(n, len(kws) + 1), kws, forb)
        lines = sents[:n]
        if "n_words_min" in combo:
            # lengthen bullets until the word minimum is met (words spread
            # across the fixed bullet count)
            need = kwargs_by_key["n_words_min"]["num_words"]
            i = 0
            while sum(len(ln.split()) for ln in lines) < need + 4:
                lines[i % n] = lines[i % n][:-1] + " and the steady pace holds."
                i += 1
        text = "\n".join("* " + ln for ln in lines)
    else:
        text = " ".join(sents)
    if "title" in combo:
        text = "<<Notes From the Workshop>>\n" + text
    if "placeholders" in combo:
        n = kwargs_by_key["placeholders"]["num_placeholders"]
        tags = ["[tool name]", "[location]", "[time of day]", "[helper name]"][:n]
        text = text + " Bring " + " and ".join(tags) + "."
    if "postscript" in combo:
        text = text + "\nP.P.S. the paint needs a second coat."
    if "caps" in combo:
        text = text.upper()
    if "lower" in combo:
        text = text.lower()
    return text


def generate(seed, n_prompts, sizes=(1, 2, 3), exclude_prompts=frozenset()):
    """the registered generator: seed 0 for the training set. Returns
    rows shaped like IFEval rows + canonical + per-constraint mutations."""
    rng = random.Random(seed)
    matrix = compat_matrix()
    keys = sorted(CONSTRAINTS)
    rows = []
    attempts = 0
    while len(rows) < n_prompts:
        attempts += 1
        if attempts > n_prompts * 50:
            raise RuntimeError("generator failed to fill quota")  # fail-closed
        size = rng.choice(sizes)
        # resample the combo WITHIN the drawn size so combo-size frequency
        # follows the registered uniform draw (a naive retry-with-new-size
        # biased 63% of prompts to singletons)
        combo = None
        for _ in range(200):
            cand = sorted(rng.sample(keys, size))
            if combo_ok(cand, matrix):
                combo = cand
                break
        if combo is None:
            continue
        kwargs_by_key = {k: CONSTRAINTS[k]["sample"](rng) for k in combo}
        if "kw_exist" in kwargs_by_key and "kw_freq" in kwargs_by_key:
            while kwargs_by_key["kw_freq"]["keyword"] in kwargs_by_key["kw_exist"]["keywords"]:
                kwargs_by_key["kw_freq"] = CONSTRAINTS["kw_freq"]["sample"](rng)
        topic = rng.choice(TOPICS)
        task = f"Write a short account of {topic} for a neighborhood newsletter."
        phrases = [CONSTRAINTS[k]["phrase"](kwargs_by_key[k]) for k in combo]
        prompt = task + " " + " ".join(phrases)
        if prompt in exclude_prompts:
            continue
        canonical = build_canonical(rng, combo, kwargs_by_key)
        mutations = {k: CONSTRAINTS[k]["mutate"](canonical, kwargs_by_key[k]) for k in combo}
        rows.append({
            "key": len(rows),
            "prompt": prompt,
            "instruction_id_list": [CONSTRAINTS[k]["iid"] for k in combo],
            "kwargs": [kwargs_by_key[k] for k in combo],
            "combo": combo,
            "canonical": canonical,
            "mutations": mutations,
        })
    return rows


def verify_rows(rows):
    """every canonical must PASS all its constraints via the VENDORED
    checkers; every mutation must FAIL its targeted constraint.
    Returns (n_ok, failures)."""
    import sys
    if str(ROOT / "vendor") not in sys.path:
        sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0
    from ifeval import instructions_registry
    failures = []
    for r in rows:
        for iid, kw, key in zip(r["instruction_id_list"], r["kwargs"], r["combo"]):
            inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
            inst.build_description(**kw)
            if not inst.check_following(r["canonical"]):
                failures.append((r["key"], key, "canonical_fails"))
            inst2 = instructions_registry.INSTRUCTION_DICT[iid](iid)
            inst2.build_description(**kw)
            if inst2.check_following(r["mutations"][key]):
                failures.append((r["key"], key, "mutation_passes"))
    return len(rows) - len({f[0] for f in failures}), failures


def constraint_spans(row, tok):
    """registered proxy span construction (v3.1): token span of each
    constraint's instruction sentence within the row's prompt, via the
    tokenizer's char offsets. Fail-closed: every phrase must be found
    exactly once and map to a nonempty token span."""
    enc = tok.encode(row["prompt"])
    spans = {}
    for key, kw in zip(row["combo"], row["kwargs"]):
        phrase = CONSTRAINTS[key]["phrase"](kw)
        start = row["prompt"].find(phrase)
        if start < 0 or row["prompt"].find(phrase, start + 1) >= 0:
            raise ValueError(f"phrase not found exactly once: {key}")
        end = start + len(phrase)
        toks = [i for i, (a, b) in enumerate(enc.offsets) if a < end and b > start]
        if not toks:
            raise ValueError(f"empty token span: {key}")
        spans[key] = (toks[0], toks[-1] + 1)
    return spans

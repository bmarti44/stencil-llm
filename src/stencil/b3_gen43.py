# ruff: noqa: E501
"""B3 v4.3 generator — dual-curation rework (sol REWORK + Opus DO-NOT-FREEZE).

Core changes vs v4.2:
- Canonicals are MINIMAL EDITS of the frozen trunk's OWN greedy base
  texts (data/b3/base-texts.json), so CE is near-zero except at
  obligation positions; the wave can only win by selective firing.
- Obligation VALUES vary per row and are SPECIFIED IN THE PROMPT
  (exact title text, exact postscript line, named placeholders, JSON
  keys) — memorizing constants cannot satisfy them.
- Every canonical is built as (piece, obligation_key) segments;
  obligation char spans are recorded in the row for the trainer's
  CE weighting.
- Mutations are MINIMAL and verified to fail ONLY their target.
- Topic split: TOPICS[:30] train / TOPICS[30:] dev-only (a true
  generalization holdout — Opus).
"""
import json
import random
import re
from pathlib import Path

from stencil.b3_gen import CONSTRAINTS as _V1
from stencil.b3_gen import FORBIDDEN_POOL, KEYWORD_POOL, TOPICS

ROOT = Path(__file__).resolve().parent.parent.parent

TRAIN_TOPICS = TOPICS[:30]
DEV_TOPICS = TOPICS[30:]

PLACEHOLDER_POOL = ["tool name", "street name", "helper name", "meeting time",
                    "paint color", "shop name", "day of week", "contact person",
                    "room number", "plant variety", "boat name", "bell tone",
                    "map sheet", "jar label", "route number", "song title",
                    "wood type", "net size", "brush width", "shelf letter"]
TITLE_PATTERNS = ["Notes on {T}", "{T}, Briefly", "A Word About {T}", "On {T} This Season"]
PS_NOUNS = ["the shared tools", "next week's plan", "the volunteers", "the weather",
            "the storage shed", "the notice board", "the spring schedule", "the repair fund"]
JSON_KEYS = [["summary", "details", "closing"], ["intro", "body", "note"],
             ["overview", "steps", "remark"], ["opening", "account", "footer"]]
CARRIERS = [
    "One neighbor mentioned that a spare {w} would have made the job easier.",
    "Halfway through, someone fetched a {w} from the shed next door.",
    "An old {w} turned out to be exactly what the task needed.",
    "A borrowed {w} saved everyone a second trip into town.",
    "The {w} on the bench drew a few curious questions.",
    "Nobody expected the {w} to matter, but it did.",
    "A note was left asking to return the {w} by Friday.",
    "The {w} was cleaned and put back before dark.",
]

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _title_of(topic):
    t = topic[0].upper() + topic[1:]
    if t.lower().startswith("the "):
        t = t[4:]
    return " ".join(w.capitalize() for w in t.split())


def _sanitize(text):
    text = re.sub(r"\*\*?", "", text)          # markdown emphasis/headers
    text = re.sub(r"\[[^\]]*\]", "", text)      # base text's own bracketed bits
    text = re.sub(r"\s+", " ", text)             # newlines -> single spaces
    return text.strip()


def _sentences_of(text):
    text = _sanitize(text)
    out = [s.strip() for s in SENT_SPLIT.split(text.strip()) if s.strip()]
    # drop an unterminated trailing fragment (truncated base generations)
    if out and not out[-1].rstrip().endswith((".", "!", "?")):
        out.pop()
    return out


# --- v4.3 constraint registry -------------------------------------------------
# key -> dict(iid, sample(rng, base_sents) -> (kwargs, values, phrase))
# canonical assembly + mutations live in build_row below.

def sample_title(rng, sents):
    T = None  # topic injected later
    pat = rng.choice(TITLE_PATTERNS)
    return {}, {"pattern": pat}, None


V43 = {
    "caps": {"iid": "change_case:english_capital"},
    "lower": {"iid": "change_case:english_lowercase"},
    "kw_exist": {"iid": "keywords:existence"},
    "kw_freq": {"iid": "keywords:frequency"},
    "kw_forbid": {"iid": "keywords:forbidden_words"},
    "n_words_min": {"iid": "length_constraints:number_words"},
    "n_words_max": {"iid": "length_constraints:number_words"},
    "n_sent": {"iid": "length_constraints:number_sentences"},
    "bullets": {"iid": "detectable_format:number_bullet_lists"},
    "title": {"iid": "detectable_format:title"},
    "json_fmt": {"iid": "detectable_format:json_format"},
    "placeholders": {"iid": "detectable_content:number_placeholders"},
    "postscript": {"iid": "detectable_content:postscript"},
    "two_resp": {"iid": "combination:two_responses"},
}

SINGLETONS = {"json_fmt", "two_resp"}
INCOMPATIBLE = {
    frozenset(("caps", "lower")),
    frozenset(("n_words_min", "n_words_max")),
    frozenset(("n_sent", "n_words_max")),
    frozenset(("bullets", "n_words_max")),
    frozenset(("bullets", "n_words_min")),  # words-only violation cannot avoid bullet collateral
    frozenset(("bullets", "n_sent")),
    frozenset(("bullets", "postscript")),
    frozenset(("bullets", "title")),
    frozenset(("caps", "postscript")),
    frozenset(("lower", "postscript")),
    frozenset(("lower", "title")),
    frozenset(("caps", "n_words_min")),  # short all-caps mutation trips langdetect (recorded landmine)
    frozenset(("caps", "kw_exist")), frozenset(("caps", "kw_freq")),
    frozenset(("caps", "kw_forbid")),
    frozenset(("lower", "kw_exist")), frozenset(("lower", "kw_freq")),
    # n_words_min forces extension; keep it off the trim-family
    frozenset(("n_words_min", "n_sent")),
}


def combo_ok(combo):
    if len(combo) == 1:
        return True
    if any(c in SINGLETONS for c in combo):
        return False
    for i, a in enumerate(combo):
        for b in combo[i + 1:]:
            if frozenset((a, b)) in INCOMPATIBLE:
                return False
    return True


def compat_matrix43():
    keys = sorted(V43)
    allowed = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a in SINGLETONS or b in SINGLETONS:
                continue
            if frozenset((a, b)) in INCOMPATIBLE:
                continue
            allowed.append(sorted([a, b]))
    return {"singletons": sorted(SINGLETONS), "allowed_pairs": sorted(allowed)}


def _draw(rng, combo, topic, base_sents):
    """per-row kwargs + prompt-facing values for each constraint."""
    kwargs, values, phrases = {}, {}, {}
    n_base = len(base_sents)
    wc_base = sum(len(s.split()) for s in base_sents)
    for key in combo:
        if key == "caps":
            kwargs[key] = {}
            phrases[key] = "Constraint: respond using only capital letters throughout."
        elif key == "lower":
            kwargs[key] = {}
            phrases[key] = "Constraint: write the whole reply in lowercase letters only."
        elif key == "kw_exist":
            ws = sorted(rng.sample(KEYWORD_POOL, 2))
            kwargs[key] = {"keywords": ws}
            phrases[key] = f"Constraint: make sure both of the words '{ws[0]}' and '{ws[1]}' appear somewhere in your reply."
        elif key == "kw_freq":
            taken = set(kwargs.get("kw_exist", {}).get("keywords", []))
            w = rng.choice([x for x in KEYWORD_POOL if x not in taken])
            f = rng.choice([2, 3])
            kwargs[key] = {"keyword": w, "frequency": f, "relation": "at least"}
            phrases[key] = f"Constraint: use the word '{w}' no fewer than {f} times."
        elif key == "kw_forbid":
            ws = sorted(rng.sample(FORBIDDEN_POOL, 2))
            kwargs[key] = {"forbidden_words": ws}
            phrases[key] = f"Constraint: never use the words '{ws[0]}' or '{ws[1]}' anywhere in the reply."
        elif key == "n_words_min":
            # relative to base: base + one carrier-ish extension stays above
            lo = rng.choice([w for w in (45, 55, 65) if w <= wc_base + 15])
            kwargs[key] = {"num_words": lo, "relation": "at least"}
            phrases[key] = f"Constraint: the reply must contain {lo} words or more."
        elif key == "n_words_max":
            hi = rng.choice([90, 110])
            kwargs[key] = {"num_words": hi, "relation": "less than"}
            phrases[key] = f"Constraint: keep the reply under {hi} words in total."
        elif key == "n_sent":
            lo = rng.choice([w for w in (9, 11) if w <= n_base + 3])
            kwargs[key] = {"num_sentences": lo, "relation": "at least"}
            phrases[key] = f"Constraint: write at least {lo} full sentences."
        elif key == "bullets":
            n = rng.choice([b for b in (5, 7) if b <= n_base])
            kwargs[key] = {"num_bullets": n}
            phrases[key] = f"Constraint: format the reply as exactly {n} bullet points, one per line, each starting with '* '."
        elif key == "title":
            t = rng.choice(TITLE_PATTERNS).format(T=_title_of(topic))
            values[key] = t
            kwargs[key] = {}
            phrases[key] = f"Constraint: begin with the exact title <<{t}>>."
        elif key == "json_fmt":
            ks = rng.choice(JSON_KEYS)
            values[key] = ks
            kwargs[key] = {}
            phrases[key] = ("Constraint: reply with a single valid JSON object whose keys are exactly "
                            + ", ".join(f'"{k}"' for k in ks) + ".")
        elif key == "placeholders":
            names = rng.sample(PLACEHOLDER_POOL, 4)
            values[key] = names
            kwargs[key] = {"num_placeholders": 4}
            phrases[key] = ("Constraint: include exactly these four bracketed placeholders: "
                            + ", ".join(f"[{n}]" for n in names) + ".")
        elif key == "postscript":
            noun = rng.choice(PS_NOUNS)
            line = f"P.P.S. Do not forget {noun}."
            values[key] = line
            # marker "P.P.S" hits upstream's ESCAPED special-case branch; a
            # custom marker with dots goes into an UNESCAPED regex (landmine).
            # Firewall (a) exemption disclosed: the marker is binary upstream;
            # the VALUE (line content) varies per row and comes from the prompt.
            kwargs[key] = {"postscript_marker": "P.P.S"}
            phrases[key] = f"Constraint: finish with this exact postscript line: '{line}'"
        elif key == "two_resp":
            kwargs[key] = {}
            phrases[key] = "Constraint: give two different complete replies, separated by a line containing exactly ******."
    return kwargs, values, phrases


def _assemble(rng, combo, kwargs, values, base_sents):
    """canonical as (piece, obligation_key|None) segments. Returns
    (text, spans dict key->list[(start,end)]). Raises ValueError when a
    draw is unsatisfiable (caller rejects the row)."""
    segs = []  # list of (text, key|None)
    sents = list(base_sents)

    def kw_sentences():
        out = []
        if "kw_exist" in combo:
            for w in kwargs["kw_exist"]["keywords"]:
                out.append((rng.choice(CARRIERS).format(w=w), "kw_exist"))
        if "kw_freq" in combo:
            for _ in range(kwargs["kw_freq"]["frequency"]):
                out.append((rng.choice(CARRIERS).format(w=kwargs["kw_freq"]["keyword"]), "kw_freq"))
        return out

    if "json_fmt" in combo:
        ks = values["json_fmt"]
        thirds = max(1, len(sents) // 3)
        obj = {ks[0]: " ".join(sents[:thirds]), ks[1]: " ".join(sents[thirds:2 * thirds]),
               ks[2]: " ".join(sents[2 * thirds:])}
        text = json.dumps(obj, ensure_ascii=False)
        spans = {"json_fmt": [(0, 1)]}
        for k in ks:
            i = text.find(f'"{k}"')
            spans["json_fmt"].append((i, i + len(k) + 2))
        spans["json_fmt"].append((len(text) - 1, len(text)))
        return text, spans

    if "two_resp" in combo:
        half = max(1, len(sents) // 2)
        a, b = " ".join(sents[:half]), " ".join(sents[half:])
        segs = [(a, None), ("\n******\n", "two_resp"), (b, None)]
    elif "bullets" in combo:
        n = kwargs["bullets"]["num_bullets"]
        extra = kw_sentences()
        lines = [s for s, _ in extra] + sents
        if len(lines) < n:
            raise ValueError("not enough sentences for bullets")
        keys = [k for _, k in extra] + [None] * len(sents)
        for j in range(n):
            take = lines[j] if j < n - 1 else " ".join(lines[n - 1:len(sents) + len(extra)])
            segs.append(("* ", "bullets"))
            segs.append((take, keys[j] if j < len(keys) else None))
            if j < n - 1:
                segs.append(("\n", None))
    else:
        body = [(s, None) for s in sents]
        for pair in kw_sentences():
            pos = rng.randrange(1, len(body) + 1)
            body.insert(pos, pair)
        segs = []
        for j, (s, k) in enumerate(body):
            segs.append((s, k))
            if j < len(body) - 1:
                segs.append((" ", None))

    if "placeholders" in combo:
        a, b, c, d = values["placeholders"]
        segs.append((" ", None))
        segs.append((f"Bring [{a}] and [{b}] to [{c}] on [{d}].", "placeholders"))

    # word-count shaping on the segment list (drop trailing non-obligation
    # sentences); counted with the CHECKER's own nltk counter
    import sys as _s
    if str(ROOT / "vendor") not in _s.path:
        _s.path.insert(0, str(ROOT / "vendor"))
    from ifeval import instructions_util as iu

    def word_count():
        return iu.count_words("".join(t for t, _ in segs))

    if "n_words_max" in combo:
        cap = kwargs["n_words_max"]["num_words"] - 12
        guard = 0
        while word_count() > cap and guard < 100:
            guard += 1
            for j in range(len(segs) - 1, -1, -1):
                t, k = segs[j]
                if k is None and len(t.split()) > 3:
                    del segs[j]
                    if j > 0 and segs[j - 1][0] == " ":
                        del segs[j - 1]
                    break
            else:
                raise ValueError("cannot satisfy n_words_max")
        if word_count() > cap:
            raise ValueError("cannot satisfy n_words_max")
    if "n_words_min" in combo:
        need = kwargs["n_words_min"]["num_words"] + 8
        pool = [s for s in sents if all(s != t for t, _ in segs)]
        while word_count() < need:
            if pool:
                segs.append((" ", None)); segs.append((pool.pop(0), None))
            else:
                segs.append((" ", None))
                segs.append((rng.choice(CARRIERS).format(w="ladder"), None))
    if "n_sent" in combo:
        def sent_count():
            return len(_sentences_of("".join(t for t, _ in segs)))
        pool = [s for s in sents if all(s != t for t, _ in segs)]
        while sent_count() < kwargs["n_sent"]["num_sentences"] + 1:
            filler = pool.pop(0) if pool else rng.choice(CARRIERS).format(w="ladder")
            segs.append((" ", None)); segs.append((filler, None))

    if "title" in combo:
        segs.insert(0, ("\n", None))
        segs.insert(0, (f"<<{values['title']}>>", "title"))
    if "postscript" in combo:
        segs.append(("\n", None))
        segs.append((values["postscript"], "postscript"))

    text = "".join(t for t, _ in segs)
    if "caps" in combo:
        text = text.upper()
    if "lower" in combo:
        text = text.lower()

    spans = {}
    off = 0
    for t, k in segs:
        if k is not None:
            spans.setdefault(k, []).append((off, off + len(t)))
        off += len(t)
    if "caps" in combo:
        spans["caps"] = [(0, min(12, len(text)))]
    if "lower" in combo:
        spans["lower"] = [(0, min(12, len(text)))]
    return text, spans


def _mutate(key, text, kwargs, values, spans):
    """MINIMAL targeted mutation: must fail ONLY `key` (verified later)."""
    if key in ("kw_exist",):
        w = kwargs["kw_exist"]["keywords"][0]
        return re.sub(re.escape(w), "item", text, count=1)
    if key == "kw_freq":
        w = kwargs["kw_freq"]["keyword"]
        return re.sub(re.escape(w), "item", text, count=1)
    if key == "kw_forbid":
        w = kwargs["kw_forbid"]["forbidden_words"][0]
        protected = [text[a:b] for sp in spans.values() for a, b in sp]
        for m in re.finditer(r"\b(morning|community|residents|neighbors|water|surface|process|schedule)\b", text):
            inside = any(text.find(pr) <= m.start() < text.find(pr) + len(pr) for pr in protected if pr in text)
            if not inside:
                ww = w.upper() if text == text.upper() else w
                return text[:m.start()] + ww + text[m.end():]
        return text + " " + w + "."
    if key == "caps":
        m = re.search(r"[A-Z]", text[20:])
        if m is None:
            m = re.search(r"[A-Z]", text)
            return text[:m.start()] + text[m.start()].lower() + text[m.start() + 1:]
        j = 20 + m.start()
        return text[:j] + text[j].lower() + text[j + 1:]
    if key == "lower":
        m = re.search(r"[a-z]", text[20:])
        j = (20 + m.start()) if m else re.search(r"[a-z]", text).start()
        return text[:j] + text[j].upper() + text[j + 1:]
    if key == "n_words_min":
        # delete NON-OBLIGATION sentences from the middle until the nltk
        # word count crosses the floor (end-truncation clipped obligations)
        import sys as _s
        if str(ROOT / "vendor") not in _s.path:
            _s.path.insert(0, str(ROOT / "vendor"))
        from ifeval import instructions_util as iu
        need = kwargs["n_words_min"]["num_words"]
        def norm(x):
            return " ".join(x.split()).lower()
        protected = [norm(text[a:b]) for sp in spans.values() for a, b in sp]
        t = text
        for _ in range(30):
            if iu.count_words(t) < need:
                return t
            sents = _sentences_of(t)
            victims = [x for x in sents
                       if not any(norm(x) in pr or pr in norm(x) for pr in protected)]
            if not victims:
                break
            victim = victims[len(victims) // 2]
            t = t.replace(victim, "", 1)
            t = re.sub(r"\s+", " ", t)
        # fallback: shrink unprotected sentences in place
        for _ in range(30):
            if iu.count_words(t) < need:
                return t
            sents = _sentences_of(t)
            victims = [x for x in sents
                       if not any(norm(x) in pr or pr in norm(x) for pr in protected)
                       and len(x.split()) > 4]
            if not victims:
                raise ValueError("n_words_min mutation impossible")
            v = victims[0]
            t = t.replace(v, " ".join(v.split()[:3]) + ".", 1)
        raise ValueError("n_words_min mutation impossible")
    if key == "n_words_max":
        cap = kwargs["n_words_max"]["num_words"]
        pad = " ".join(["and the steady pace of the work held on"] * ((cap // 9) + 2))
        if text == text.lower():
            pad = pad.lower()
        if text == text.upper():
            pad = pad.upper()
        # insert before any trailing obligation lines (postscript must stay last)
        tail_starts = [a for k2 in ("postscript",) if k2 in spans for a, _ in spans[k2]]
        cut = min(tail_starts) if tail_starts else len(text)
        return text[:cut].rstrip() + " " + pad + ". " + text[cut:]
    if key == "n_sent":
        # merge sentences until the CHECKER's count crosses the floor
        import sys as _s
        if str(ROOT / "vendor") not in _s.path:
            _s.path.insert(0, str(ROOT / "vendor"))
        from ifeval import instructions_util as iu
        need = kwargs["n_sent"]["num_sentences"]
        t = text
        for _ in range(40):
            if iu.count_sentences(t) < need:
                return t
            keep_upper = t == t.upper()
            t2 = re.sub(r"\.\s+([A-Za-z])",
                        lambda m: ", " + (m.group(1) if keep_upper else m.group(1).lower()),
                        t, count=1)
            if t2 == t:
                break
            t = t2
        return t
    if key == "bullets":
        # merge the last two bullets into one line
        lines = text.split("\n")
        idx = [j for j, ln in enumerate(lines) if ln.startswith("* ")]
        if len(idx) >= 2:
            j = idx[-1]
            lines[j - 1] = lines[j - 1] + " " + lines[j][2:]
            del lines[j]
        return "\n".join(lines)
    if key == "title":
        return text.replace("<<", "", 1).replace(">>", "", 1)
    if key == "json_fmt":
        return text + " trailing words"
    if key == "placeholders":
        a, b = spans["placeholders"][0]
        seg = text[a:b].replace("[", "(", 2).replace("]", ")", 2)
        return text[:a] + seg + text[b:]
    if key == "postscript":
        return text.replace("P.P.S.", "PS", 1).replace("p.p.s.", "ps", 1)
    if key == "two_resp":
        return text.replace("******", "---")
    raise KeyError(key)


def _load_base_texts():
    return json.loads((ROOT / "data" / "b3" / "base-texts.json").read_text())


def generate43(seed, n_prompts, split, exclude_prompts=frozenset()):
    """split: 'train' (TOPICS[:30]) or 'dev' (TOPICS[30:], disjoint)."""
    rng = random.Random(seed)
    base = _load_base_texts()
    topics = TRAIN_TOPICS if split == "train" else DEV_TOPICS
    topic_idx = {t: i for i, t in enumerate(TOPICS)}
    keys = sorted(V43)
    rows, attempts = [], 0
    while len(rows) < n_prompts:
        attempts += 1
        if attempts > n_prompts * 80:
            raise RuntimeError("generator failed to fill quota")
        size = rng.choice((1, 2, 3))
        combo = None
        for _ in range(200):
            cand = sorted(rng.sample(keys, size))
            if combo_ok(cand):
                combo = cand
                break
        if combo is None:
            continue
        topic = rng.choice(topics)
        style = rng.randrange(3)
        b = base[f"{topic_idx[topic]}:{style}"]
        base_sents = _sentences_of(b["text"])
        if len(base_sents) < 4:
            continue
        cw = set()
        try:
            kwargs, values, phrases = _draw(rng, combo, topic, base_sents)
        except IndexError:
            continue  # no admissible threshold for this base text
        for k in combo:
            kwv = kwargs[k]
            cw |= set(kwv.get("keywords", [])) | set(kwv.get("forbidden_words", []))
            if "keyword" in kwv:
                cw.add(kwv["keyword"])
        blob = (topic + " " + b["text"]).lower()
        if any(w in blob for w in cw):
            continue
        prompt = b["task"] + " " + " ".join(phrases[k] for k in combo)
        if prompt in exclude_prompts or any(r["prompt"] == prompt for r in rows[-50:]):
            continue
        try:
            canonical, spans = _assemble(rng, combo, kwargs, values, base_sents)
        except ValueError:
            continue
        try:
            mutations = {k: _mutate(k, canonical, kwargs, values, spans) for k in combo}
        except ValueError:
            continue  # reject rows where a MINIMAL targeted mutation is impossible
        rows.append({
            "key": len(rows), "split": split, "topic": topic, "style": style,
            "prompt": prompt,
            "instruction_id_list": [V43[k]["iid"] for k in combo],
            "kwargs": [kwargs[k] for k in combo],
            "combo": combo, "values": values, "canonical": canonical,
            "obligation_spans": {k: [list(x) for x in v] for k, v in spans.items()},
            "mutations": mutations,
        })
    return rows


def verify43(rows):
    """(1) every canonical passes ALL its constraints; (2) every mutation
    fails its TARGET and passes EVERY OTHER constraint (minimality —
    Opus curation finding 1); (3) obligation spans are in-bounds."""
    import sys
    if str(ROOT / "vendor") not in sys.path:
        sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0
    from ifeval import instructions_registry

    def check(iid, kw, resp):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in kw.items() if v})
        return bool(resp.strip() and inst.check_following(resp))

    failures = []
    for r in rows:
        pairs = list(zip(r["combo"], r["instruction_id_list"], r["kwargs"]))
        for key, iid, kw in pairs:
            if not check(iid, kw, r["canonical"]):
                failures.append((r["key"], key, "canonical_fails"))
        for key, iid, kw in pairs:
            mut = r["mutations"][key]
            if check(iid, kw, mut):
                failures.append((r["key"], key, "mutation_passes"))
            for k2, iid2, kw2 in pairs:
                if k2 != key and not check(iid2, kw2, mut):
                    failures.append((r["key"], key, f"mutation_collateral:{k2}"))
        for k, sp in r["obligation_spans"].items():
            for a, b in sp:
                if not (0 <= a < b <= len(r["canonical"])):
                    failures.append((r["key"], k, "span_oob"))
    return failures

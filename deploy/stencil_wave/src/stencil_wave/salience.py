# ruff: noqa: E501
"""Salience: does a sentence state a persistent, checkable requirement the
model must honor in its output?

Vendored VERBATIM (sentence splitter, cue regexes, featurizer, logistic
model) from the research module ``stencil.salience`` so the package has no
dependency on the research repo. Only the training / corpus code is
dropped; the committed weights (``weights/salience_weights.json``) are the
research weights byte-for-byte, so scores are bitwise identical
(``tests/test_salience_port.py`` asserts this against the research module
when it is available).

Known limits (measured on hand-labeled Multi-IF turn-1 sentences):
precision ~0.92-0.96, recall ~0.75. UNDER-inclusive by design. Misses
constraints buried in a task sentence ("Write a blog post ... with at
least 300 words"), tone directives with no form vocabulary ("Be angry
about it"), and compound task+constraint sentences. Fires on markdown /
list fragments. Cannot tell the addressee: run it on USER turns only.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------- sentences
_ABBREV = re.compile(r"(?:\b(?:i\.e|e\.g|etc|vs|mr|mrs|ms|dr|st|no|p\.s|p\.p\.s)|\b[a-z])\.$", re.I)
_BOUNDARY = re.compile(r"[.!?]+[\"'”’)\]]*(?=\s+(?:[A-Z0-9\"'“(*<\[]|[a-z]))|\n+")


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Char spans of sentences.  Does not split inside an open double quote,
    after common abbreviations / initials, and treats newlines as boundaries."""
    spans: list[tuple[int, int]] = []
    start = 0
    for m in _BOUNDARY.finditer(text):
        end = m.end()
        chunk = text[start:end]
        if not m.group().startswith("\n"):
            if chunk.count('"') % 2 == 1 or chunk.count("“") != chunk.count("”"):
                continue  # inside an open quote
            if _ABBREV.search(chunk.rstrip("\"'”’)]")):
                continue
        _push(spans, text, start, end)
        start = end
    _push(spans, text, start, len(text))
    return spans


def _push(spans, text, a, b):
    seg = text[a:b]
    lead = len(seg) - len(seg.lstrip())
    trail = len(seg) - len(seg.rstrip())
    if b - trail > a + lead:
        spans.append((a + lead, b - trail))


# ------------------------------------------------------------------ features
_WB = r"(?<![a-z'])"
_NUMWORD = (r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
            r"fifteen|twenty|thirty|forty|fifty|hundred|thousand|once|twice|thrice|dozen|half")
_DISCOURSE = re.compile(r"^(?:(?:please|kindly|also|and|then|first|firstly|just|now|next|finally|additionally|basically|"
                        r"moreover|furthermore|however|but|so|in this task|for this task|in your (?:response|reply|answer|writing)|"
                        r"remember to|be sure to|make sure to|try to|you (?:must|should|need to|have to|are required to|are to|will)|"
                        r"you are not allowed to|you cannot|you can't|you may not|i want you to|i need you to|i'd like you to|"
                        r"i would like you to)[,:]?\s+)+")
_TASK_VERBS = (r"write|describe|compose|draft|create|explain|tell|generate|produce|summarize|summarise|"
               r"rewrite|outline|discuss|develop|craft|imagine|pretend|act|come|help|can|could|would|"
               r"plan|suggest|recommend|design|build|prepare|make me|give me|"
               r"send|share|translate|elaborate|expand|continue|critique|review|analyze|analyse|"
               r"what|why|how|who|when|where|which|is|are|do you|does|i|my|we|our|hi|hello|hey|thanks|thank")
_DIRECTIVE_VERBS = (r"use|include|avoid|wrap|end|start|begin|finish|keep|make sure|ensure|respond|reply|"
                     r"answer|highlight|repeat|refrain|mention|limit|format|separate|put|add|give|provide|"
                     r"do not|don't|never|always|capitalize|capitalise|express|refer|organize|organise|place|"
                     r"make (?:it|the|your|this|them|every|all|each)|"
                     r"italicize|bold|indent|number|restrict|exclude|omit|conclude|close|open|contain|"
                     r"structure|divide|split|present|label|mark|surround|enclose|preface|introduce|"
                     r"choose|pick|stick|stay|remain|be|have|must|should|only|no|not|there|in your|"
                     r"your|the (?:response|reply|answer|output|result|text|essay|whole|entire)|all|every|each|"
                     r"it|words|letters|sentences|paragraphs|at least|at most|exactly")

_PATTERNS: dict[str, str] = {
    "modal_obligation": _WB + r"(?:must|should|shall|ought to|needs? to|has to|have to|required|require|be sure|make sure|ensure|"
                              r"it is important|mandatory|is expected|are expected|is to be|are to be|has to be)\b",
    "prohibition": _WB + r"(?:do not|don't|never|not allowed|avoid|refrain|no other|without using|cannot|can't|must not|"
                         r"should not|shouldn't|mustn't|forbidden|exclude|omit|not permitted|no \w+ should|nothing else|"
                         r"not (?:include|contain|use|mention|add|exceed|have))\b",
    "quantifier": _WB + r"(?:at least|at most|no more than|no fewer than|no less than|fewer than|less than|more than|exactly|"
                        r"minimum|maximum|between|up to|or more|or fewer|or less|in total|a total of|under \d|over \d|"
                        r"\d+\+|\d+-th|times\b|per line|one per|only once|the same|different)\b",
    "numeral": r"(?:\b\d+\b|" + _WB + r"(?:" + _NUMWORD + r")\b)",
    "quoted_literal": r"(?:\"[^\"]{1,200}\"|“[^”]{1,200}”|(?<![a-z])'[^']{1,120}'(?![a-z])|<<[^>]{1,120}>>|\[[^\]]{1,60}\]|\*{3,}|\*[^*\n]{1,80}\*)",
    "colon_literal": r":\s*\S",
    "restrictor": _WB + r"(?:only|solely|entirely|exclusively|strictly|whatsoever|throughout|at all|nothing (?:else|but)|"
                        r"anywhere|everywhere|always|never|at the (?:very )?(?:beginning|end|start)|first|last|before|after)\b",
    "universal": _WB + r"(?:all|every|each|entire|whole|any|none|no|both|everything|nothing)\b",
    "exactness": _WB + r"(?:exact|exactly|verbatim|word for word|word by word|precisely|specifically|literally|as is|itself)\b",
    "output_ref": _WB + r"(?:(?:your|the|this|entire|whole|final|my) (?:entire |whole |final |own )?"
                        r"(?:response|reply|answer|output|result|text|responses|replies|answers)|"
                        r"in your (?:response|reply|answer|output|writing|text)|"
                        r"your (?:entire |whole )?(?:response|reply|answer|output|result|text|writing)|"
                        r"the (?:response|reply|answer|output|result|text)|"
                        r"the (?:request|prompt|question|text|instruction|sentence|passage|message)s? (?:above|below)|the above|"
                        r"repeat (?:the|this|it|all|every)|"
                        r"the (?:essay|letter|email|poem|story|summary|article|blog post|description|itinerary|resume|speech|song|riddle|joke|limerick|haiku|rap|dialogue|script|proposal|report|pitch|review|note)"
                        r" (?:should|must|needs|has|is to|cannot|can't|shouldn't))\b",
    "form_noun": _WB + r"(?:words?|sentences?|paragraphs?|bullet(?: points?)?|letters?|commas?|title|phrase|sections?|"
                       r"placeholders?|capital(?:s|ized|ised)?|capitals|lowercase|uppercase|lower case|upper case|postscript|"
                       r"p\.s\.?|p\.p\.s\.?|markdown|json|xml|html|quotation marks?|quotes?|language|english|french|german|"
                       r"spanish|italian|hindi|arabic|chinese|japanese|korean|russian|portuguese|highlight(?:ed|s)?|"
                       r"keywords?|characters?|lines?|asterisks?|dividers?|format|punctuation|syllables?|stanzas?|"
                       r"headings?|headers?|bold|italics?|emoji|hashtags?|footnotes?|references?|appendix|"
                       r"double (?:angular )?brackets|square brackets|parentheses|caps|case|tone|style)\b",
    "second_person": _WB + r"(?:you|your|yours|yourself)\b",
    "first_person": _WB + r"(?:i|me|my|mine|we|our|us|i'm|i've|i'd|i'll|we're)\b",
    "third_person": _WB + r"(?:he|she|they|him|her|his|hers|their|them|its|it was|it is|it's)\b",
    "past_tense_be": _WB + r"(?:was|were|had|did|became|been)\b",
    "copula_present": _WB + r"(?:is|are|has|have)\b",
    "task_frame": _WB + r"(?:for (?:a|an|my|our|the|local|your)\b|about\b|on the topic|regarding|to my|in the style of|as if|"
                        r"as a\b|for me\b|i want|i need|i would like|i'd like|can you|could you|would you|please|"
                        r"write (?:a|an|me|the|two|some)\b|tell me|help me|let's|imagine|pretend|you are a)",
    "genre_noun": _WB + r"(?:essay|poem|story|letter|email|e-mail|summary|note|account|article|blog post|blog|itinerary|"
                        r"resume|résumé|cover letter|review|speech|song|rap|riddle|joke|limerick|haiku|dialogue|script|"
                        r"proposal|report|pitch|advertisement|ad|description|explanation|tweet|post|lyrics|"
                        r"biography|profile|plan|guide|tutorial|list|table|outline|abstract|paragraph about|piece|passage|section for)\b",
    "continuation": r"^(?:now|then|next|also|finally|additionally|and|but|so|after that)\b",
    "interrogative": r"\?\s*$|^(?:what|why|how|who|when|where|which|is|are|do|does|can|could|would|should) ",
    "lead_task_verb": r"^(?:" + _TASK_VERBS + r")\b",
    "lead_directive_verb": r"^(?:" + _DIRECTIVE_VERBS + r")\b",
    "lead_subject_modal": r"^(?:the|your|this|each|every|all|there|no|none|words|letters|sentences|paragraphs|it|in your|"
                          r"my|any|everything|nothing|both|you|i want|i need)\b.{0,80}?\b(?:should|must|shall|need|needs|has to|have to|cannot|can't|may not|is to|are to|ought)\b",
}
_ORDER = [
    "modal_obligation", "prohibition", "quantifier", "numeral", "quoted_literal", "colon_literal",
    "restrictor", "universal", "exactness", "output_ref", "form_noun", "second_person", "first_person",
    "third_person", "past_tense_be", "copula_present", "task_frame", "genre_noun", "continuation",
    "interrogative", "lead_task_verb", "lead_directive_verb", "lead_subject_modal",
]
_COMPILED = {k: re.compile(_PATTERNS[k], re.I) for k in _ORDER}
_DEONTIC_BE = re.compile(r"\b(?:you are|you're|are not allowed|are required|are expected|is to be|are to be|has to|"
                         r"have to|is expected|is required|is allowed|are allowed|is not allowed)\b")

DEONTIC_CUES = ["lead_directive_verb", "modal_obligation", "prohibition", "lead_subject_modal"]
FORM_CUES = ["output_ref", "form_noun"]
BINDING_CUES = ["numeral", "quoted_literal", "quantifier", "exactness", "restrictor", "universal", "colon_literal"]
NEGATIVE_SIDE = ["second_person", "first_person", "third_person", "past_tense_be", "copula_present", "task_frame",
                 "genre_noun", "continuation", "interrogative", "lead_task_verb"]
FEATURE_NAMES: list[str] = (["deontic", "output_form", "binding", "deontic_x_form", "form_x_binding"] + NEGATIVE_SIDE
                            + ["past_tense_verbs", "log_len", "narrative_declarative", "task_only"])


def _norm(sentence: str) -> str:
    s = sentence.strip().lower()
    s = re.sub(r"^[\s\-\*•\d\.\)\(]+(?=[a-z])", "", s)
    return re.sub(r"\s+", " ", s)


def cues(sentence: str) -> dict[str, float]:
    """Fine-grained binary cues (inspectable; the model consumes ``featurize``)."""
    s = _norm(sentence)
    lead = _DISCOURSE.sub("", s)
    f = {name: float(bool(_COMPILED[name].search(lead if name.startswith("lead_") else s))) for name in _ORDER}
    f["copula_present"] = float(bool(_COMPILED["copula_present"].search(_DEONTIC_BE.sub(" ", s))))
    return f


def featurize(sentence: str) -> np.ndarray:
    s = _norm(sentence)
    toks = re.findall(r"[a-z']+", s)
    f = cues(sentence)
    deontic = float(any(f[n] for n in DEONTIC_CUES))
    form = float(any(f[n] for n in FORM_CUES))
    binding = float(any(f[n] for n in BINDING_CUES))
    past = sum(1 for t in toks if len(t) > 4 and t.endswith("ed") and t not in ("need", "indeed", "exceed", "proceed"))
    x = [deontic, form, binding, deontic * form, form * binding] + [f[n] for n in NEGATIVE_SIDE] + [
        math.log1p(past),
        math.log1p(len(toks)) - 2.5,
        float((f["past_tense_be"] or f["third_person"]) and not f["modal_obligation"] and not f["prohibition"]),
        float(f["lead_task_verb"] and f["genre_noun"] and not deontic and not binding),
    ]
    return np.asarray(x, dtype=np.float64)


# --------------------------------------------------------------------- model
@dataclass(frozen=True)
class Model:
    w: np.ndarray
    b: float
    feature_names: list[str]

    def score(self, sentence: str) -> float:
        z = float(featurize(sentence) @ self.w + self.b)
        return 1.0 / (1.0 + math.exp(-z))

    def to_json(self) -> dict:
        return {"feature_names": self.feature_names, "w": self.w.tolist(), "b": self.b}

    @classmethod
    def from_json(cls, d: dict) -> Model:
        return cls(np.asarray(d["w"], dtype=np.float64), float(d["b"]), list(d["feature_names"]))


WEIGHTS_PATH = Path(__file__).with_name("weights") / "salience_weights.json"

# A classifier that cannot separate these is untrained or over-inclusive.
SANITY_PROBE = (
    ("It fell all night on the tin roof and the gutters overflowed.", False),
    ("Do not use any commas in your response.", True),
)


def load_model(path: Path | str = WEIGHTS_PATH) -> Model:
    """Load committed weights; fail LOUDLY (never fall back to an untrained
    model, which scores every sentence at 0.5 and admits all text)."""
    m = Model.from_json(json.loads(Path(path).read_text()))
    if m.feature_names != FEATURE_NAMES:
        raise RuntimeError(f"salience weights at {path} do not match this featurizer")
    if not (np.any(m.w != 0.0) or m.b != 0.0):
        raise RuntimeError(f"salience weights at {path} are all zero (untrained)")
    for sentence, want in SANITY_PROBE:
        if (m.score(sentence) >= 0.5) != want:
            raise RuntimeError("salience weights fail the sanity probe")
    return m


DEFAULT_MODEL: Model = load_model()


def score_instruction(sentence: str, model: Model | None = None) -> float:
    return (model or DEFAULT_MODEL).score(sentence)


def is_instruction(sentence: str, model: Model | None = None) -> bool:
    return score_instruction(sentence, model) >= 0.5


def extract_instructions(text: str, model: Model | None = None) -> list[tuple[int, int]]:
    return [(a, b) for a, b in split_sentences(text) if is_instruction(text[a:b], model)]

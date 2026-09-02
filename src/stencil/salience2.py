# ruff: noqa: E501
"""SALIENCE-2 (LEDGER-PLAN.md, Brian's ruling 1): clause-level instruction finder.

``extract_instructions(text) -> list[Span]`` returns CLAUSE-level character
spans of every directive that constrains the model's future output, each with
a type tag (additive / prohibition / limit / tone / format / other) that is
for reporting only.  Two backends share one clause segmenter:

* ``linguistic`` — a logistic model over case-folded linguistic cues of the
  clause (deontic lead, prohibition, quantifier, form nouns, tone words, task
  framing, attachment head, ...).  No model, no GPU.
* ``probe`` — a linear probe over the frozen Qwen3-1.7B trunk's layer-20
  residual stream (the existing ``capture_hidden``/``return_hidden`` path),
  trained token-wise on weak labels; a clause is an instruction when the mean
  probe logit over its tokens is positive.  Welded to the trunk by ruling.

Buried constraints ("Write a blog post about X with at least 300 words, and do
not mention Y.") are recovered by the clause segmenter: it splits coordinated
directives, prepositional / participial post-modifiers ("with at least ...",
"without ...", "using ...", "in all lowercase", "in JSON"), relative clauses
("that includes ...") and numeral-in-NP length modifiers ("a 300+ word ad").

Anti-cheat: the synthetic corpora's "Constraint:" marker is stripped at load
time and never a feature; the b3 constraint phrases are re-cased to ordinary
sentences before they are seen; every regex is inspectable via
``feature_patterns``; both models are trained from zero init by full-batch
gradient descent (no RNG anywhere in inference or fitting).

Weights: ``salience2_weights.json`` (linguistic), ``salience2_probe.npz``
(clause-pooled layer-20 probe) and ``salience2_hybrid.json`` (linguistic
features + probe logit) next to this module; regenerate with
``python -m stencil.salience2 [--probe]`` (the probe path caches trunk
features under results/salience2/).

DATA LINEAGE: fitting uses only data/b3 synthetic prompts, buried variants,
and their canonical prose.  Evaluation uses data/bench and recorded benchmark
responses; those sources are disjoint and are available only through
``eval_*`` helpers that no fitting path calls.  A first build used IFEval and a
later build used Multi-IF prompts/responses; both were withdrawn and refit.

MEASURED (tests/test_salience2.py, 2026-09-01; gold = clause spans, match =
>= 50% character overlap both ways):
* Gate 1 (blind Multi-IF turn-1 clause samples, scored once each):
  linguistic seed-3 P=0.950 R=0.854 (first fit); seed-4 P=0.938 R=0.884 ->
  the registered recall bar (0.90) is NOT met (precision is).  probe seed-4
  P=0.928 R=0.744; hybrid seed-4 P=0.899 R=0.826.  Design-informed samples
  reach 0.96-0.98, i.e. each blind draw exposes unseen constructions.
* Gate 2 (leave-one-corpus-out F1): linguistic 0.973 / 0.945 (met); probe
  0.898 / 0.883; hybrid 0.956 / 0.917.
* Gate 3 (IFBench transfer, gold = checker description sentences): linguistic
  0.676, probe 0.684, hybrid 0.683 (precision is under-counted: the IFBench
  gold omits genuine instructions in the task text, and its unit is the
  sentence while this finder emits clauses).
* Gate 4 (buried, held-out templates + held-out b3 split): recall 0.877 /
  0.967 / 0.967.
DEFAULT_BACKEND is ``linguistic`` (best blind gate-1, passes gate 2, no GPU).
Known misses (do not trust it on): hyphenated / bare length NPs ("100-word",
"2 paragraph"), count-of-responses instructions ("provide two alternatives"),
short manner imperatives without a tone word ("reply in details", "Make
sentences short"), instructions followed by a quoted passage after a colon
(the quoted material is absorbed into the clause), "P.S." at a sentence end
(no split), and any instruction whose only cue is world knowledge.  It is a
USER-turn finder: instruction echoes inside model responses are classified
as instructions too.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

TYPES = ("additive", "prohibition", "limit", "tone", "format", "other")
DEFAULT_BACKEND = "linguistic"  # set by the gates (see tests/test_salience2.py); "probe" needs h20 features


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    type: str
    score: float

    def text(self, source: str) -> str:
        return source[self.start:self.end]


# ================================================================== sentences
_ABBREV = re.compile(r"(?:\b(?:i\.e|e\.g|etc|vs|mr|mrs|ms|dr|st|no|p\.s|p\.p\.s)|\b[a-z])\.$", re.I)
_BOUNDARY = re.compile(r"[.!?]+[\"'”’)\]]*(?=\s+(?:[A-Z0-9\"'“(*<\[]|[a-z]))|\n+")


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Char spans of sentences (no split inside an open double quote, after
    abbreviations / initials; newlines are boundaries)."""
    spans: list[tuple[int, int]] = []
    start = 0
    for m in _BOUNDARY.finditer(text):
        end = m.end()
        chunk = text[start:end]
        if not m.group().startswith("\n"):
            if (chunk.count('"') % 2 == 1 or chunk.count("“") != chunk.count("”")) and len(chunk) < 400:
                continue
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


# ==================================================================== clauses
_NUM = r"(?:\d+(?:\.\d+)?\+?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|hundred|thousand|a single|single|a couple of|several)"
_QUANT = (r"(?:at least|at most|no more than|no fewer than|no less than|fewer than|less than|more than|exactly|"
          r"a minimum of|a maximum of|minimum|maximum|up to|under|over|within|a total of|only|about|around|roughly|approximately)")
_LANGS = (r"english|french|german|spanish|italian|hindi|arabic|chinese|mandarin|japanese|korean|russian|portuguese|"
          r"telugu|kannada|tamil|bengali|persian|farsi|urdu|punjabi|marathi|gujarati|vietnamese|thai|swahili|"
          r"finnish|swedish|dutch|polish|turkish|greek|hebrew|latin|bulgarian|nepali|malayalam|shakespearean english")
_UNIT = (r"(?:words?|sentences?|paragraphs?|lines?|characters?|letters?|bullet points?|bullets?|points?|sections?|parts?|"
         r"placeholders?|stanzas?|verses?|pages?|responses?|versions?|syllables?|chapters?|headings?|columns?|rows?)")
_CASE_PP = r"(?:all\s+)?in\s+(?:all\s+)?(?:only\s+)?(?:capital|uppercase|upper case|lowercase|lower case|caps|small|title case|sentence case)(?:\s+letters?)?(?:\s+only)?"
_LANG_PP = r"(?:in|using)\s+(?:only\s+|the\s+)?(?:" + _LANGS + r")(?:\s+language)?(?:\s+only)?"
_FMT_PP = (r"(?:in|as)\s+(?:a|an|the)?\s*(?:valid\s+)?(?:json|xml|html|yaml|csv|markdown|latex|plain text|table|bullet|bulleted|numbered|numbered list|bullet list|"
           r"tabular|list)(?:\s+(?:format|form|object|block|document|list|table|points?))?")
_NOCOORD = r"(?!(?:and|but|then|or|with|without|using|in|about|for|to|that|which|so)\b)"
_ROLE_NOUN = (r"pirate|bard|poet|lawyer|president|teacher|child|kid|expert|professor|journalist|scientist|chef|coach|robot|character|persona|cowboy|"
              r"knight|wizard|detective|salesman|salesperson|comedian|narrator|storyteller|critic|reviewer|friend|parent|mother|father|doctor|nurse|"
              r"engineer|developer|assistant|guide|historian|philosopher|politician|celebrity|rapper|singer|dj|dungeon master|master|villain|hero|"
              r"grandmother|grandfather|toddler|teenager|student|professional|native speaker|speaker|shakespearean|victorian|southerner|new yorker|"
              r"sports commentator|commentator|announcer|reporter|weatherman|therapist|monk|priest|king|queen|prince|princess|soldier|sailor|farmer")
_STYLE_PP = (r"in\s+(?:(?:a|an)\s+(?:\w+[\s,]+){0,4}?(?:style|tone|voice|manner|format|form|way|register)|the\s+(?:form|format|style|tone|voice|manner)\s+of\s+(?:a|an|the)?\s*" + _NOCOORD + r"\w+(?:\s+" + _NOCOORD + r"\w+){0,4})"
             r"|as\s+if\s+you\s+were\s+(?:a|an)\s+" + _NOCOORD + r"\w+(?:\s+" + _NOCOORD + r"\w+){0,3}"
             r"|(?:as|like)\s+(?:a|an)\s+(?:\w+\s+){0,2}?(?:" + _ROLE_NOUN + r")\b(?:\s+(?:from|of|in)\s+(?:the\s+)?\w+){0,2}")
_LEN_PP = (r"(?:with|in|using|of|to)\s+(?:(?:" + _QUANT + r")\s+)?(?:a total of\s+)?(?:" + _NUM + r")\s+(?:or (?:more|fewer|less)\s+)?(?:different\s+|short\s+|long\s+|complete\s+|full\s+)?" + _UNIT +
           r"(?:\s+(?:or (?:more|fewer|less)|in total|long|or so|at most|at least|maximum|minimum|each))?")
_BOUNDED_ATTACH = re.compile(r"(?:" + _CASE_PP + r"|" + _LANG_PP + r"|" + _FMT_PP + r"|" + _LEN_PP + r"|" + _STYLE_PP + r")", re.I)
# unbounded attachment heads (run to the next break / topic head / clause end)
_OPEN_ATTACH = re.compile(
    r"(?:without\b|using\s+(?:only|no|at least|at most|exactly|the|a|an|fewer|less|more|all|" + _NUM + r"|markdown|bullet|json|xml|html|" + _LANGS + r")\b|"
    r"with\s+(?:" + _QUANT + r"|the|a|an|no|any|some|these|those|this|each|every|your|all|only|double|markdown|square|bullet|exactly|" + _NUM + r")\b|"
    r"(?:that|which)(?:'s|\s+(?:has|have|contains?|includes?|uses?|is|are|starts?|ends?|does not|doesn't|must|should|mentions?|avoids?|features?|consists?|comes?))\b|"
    r"(?:containing|including|featuring|separated (?:by|with)|wrapped in|written in|formatted as|ending with|starting with|beginning with|making sure|ensuring|"
    r"being sure|being careful|avoiding|keeping|limited to|restricted to|no longer than|no shorter than|no more than|not exceeding|not more than|"
    r"all in|highlighting|mentioning|repeating|sounding|written)\b|"
    r"as\s+(?:a|an)\s+(?:numbered|bulleted|bullet|markdown|json|xml|html|table|list|poem|song|dialogue|haiku|limerick|rap|letter|series|set)\b)", re.I)
_ATTACH_START = re.compile(r"\s+(?=" + _BOUNDED_ATTACH.pattern + r"|" + _OPEN_ATTACH.pattern + r")", re.I)
_TOPIC_HEAD = re.compile(r"\s+(?=(?:about|regarding|concerning|on the topic|for (?:a|an|my|our|the|your|me|us|kids|teenagers|students|children|people|someone)\b|to (?:a|an|my|our|the)\b|why|how|what|which|whether|because|where|when)\b)", re.I)

_TASK_HEAD = re.compile(
    r"^(?:(?:please|kindly|also|and|then|now|just|first|finally|additionally|remember to|be sure to|make sure to|try to|"
    r"you (?:must|should|need to|have to|are to|will)|i want you to|i need you to|i'd like you to|i would like you to|can you|could you|would you|will you|"
    r"i want|i need|i'd like|i would like|i am looking for|i'm looking for|help me|let's)[,:]?\s+)*"
    r"(?:write|describe|compose|draft|create|explain|tell|generate|produce|summarize|summarise|rewrite|outline|discuss|develop|craft|come up|help|"
    r"plan|suggest|recommend|design|build|prepare|make(?!\s+sure|\s+it\b|\s+the\s+(?:response|answer|reply|output))|give|send|share|translate|elaborate|expand|continue|critique|review|analyze|analyse|take|"
    r"complete|name|list|provide|answer|respond|reply|say|imagine|edit|improve|fix|convert|turn|change|shorten|reformat|pen|draw up|"
    r"i (?:want|need|am|'m|'d|would)|we|what|why|how|who|when|where|which|is|are|do|does|can|could|would|will)\b", re.I)
_COORD_LEAD = (r"do not|don't|never|avoid|refrain|make sure|ensure|be sure|include|use|wrap|end|start|begin|finish|keep|respond|reply|answer|give|provide|"
               r"highlight|put|add|separate|separated|write|say|mention|repeat|contain|limit|format|capitalize|italicize|bold|organize|organise|label|mark|place|"
               r"restrict|exclude|omit|no\b|not\b|your |the (?:response|reply|answer|output|result|text|whole|entire|word|letter|(?:\w+ ){1,3}(?:should|must))|"
               r"it (?:should|must|has|needs|cannot|can't|shouldn't)|there (?:should|must)|each|every|at least|at most|exactly|fewer|less than|more than|only|"
               r"for (?:the (?:word|letter|keyword|title|response|answer|reply)|there to be)|"
               r"should|must|will|can|sound|be |have |stick|stay|remain|making|ensuring|avoiding|keeping|starting|ending|wrapping|"
               r"please |also |then |just |kindly |i want|i need|i'd like|i would like|make it|with |without |using |in (?:all|only|json|xml|markdown|html|lowercase|uppercase|capital|"
               + _LANGS + r"|under|less|fewer|at|exactly|the form|the style|an? (?:\w+[\s,]+){0,4}?(?:style|tone|voice|manner)|" + _NUM + r")\b|as if|as an? |like an? |sounding|written|keeping")
_COORD_LEAD_AND = re.sub(r"\|with \|without \|using \|in \(\?:.*?\)\\b$", "", _COORD_LEAD)
_COORD_BREAK = re.compile(
    r"(?:[,;:]\s+(?:(?:and|but|then|also|or|plus|while|yet|so)\s+)?(?=(?:" + _COORD_LEAD + r"))"
    r"|\s+(?:and|but|then|while|yet)\s+(?=(?:" + _COORD_LEAD_AND + r"))"
    r"|\s+(?=without\s+(?:using|mentioning|saying|including|ever|any|the\s+(?:word|keyword|letter)s?|commas?)\b))", re.I)
_NP_LENGTH = re.compile(r"(?:\b(?:exactly|at least|at most|about|around|roughly|approximately|only)\s+)?\b" + _NUM +
                        r"(?:\s*-\s*| |-)(?:(?:or more|or fewer|or less|plus)\s+)?(?:different\s+|short\s+|long\s+)?(?:word|sentence|paragraph|line|section|stanza|part|bullet point|bullet|point|item|character|page|verse|response|version|placeholder|syllable)s?\b", re.I)
_HEAD_DIRECTIVE = re.compile(r"\b(?:at least|at most|no more than|no fewer than|fewer than|less than|more than|a minimum of|a maximum of|minimum|maximum|up to|a total of|under \d|within \d)\b|\byour (?:entire |whole )?(?:response|answer|reply|output|essay)\b|\b(?:should|must|do not|don't|never)\b|\b(?:at least|at most|exactly)\b", re.I)
_MANNER_VERB_TAIL = re.compile(r"\b(?:act|acting|behave|behaving|sound|sounding|speak|speaking|talk|talking|write|writing|respond|responding|reply|answer|pretend|role-?play|treat|address)\s*$", re.I)
_FRONTED_BLOCK = re.compile(r"\b(?:should|must|do not|don't|never|at least|at most|exactly|\d+|include|use|avoid)\b", re.I)
_FRONTED_ADVERBIAL = re.compile(r"^(?:at|in|for|before|after|when|while|if|as|by|with|to|on|during|once|upon|throughout|from|within)\b", re.I)
_QUANT_LEAD = re.compile(r"^(?:at least|at most|exactly|fewer|less than|more than|only|no more than|up to)\b", re.I)
_BARE_HEAD = re.compile(r"^(?:(?:please|kindly|also|and|then|now|just|first|finally)[,:]?\s+)*\w+(?:\s+(?:me|us|it|them|this|that|one))?[,:]?$", re.I)


def _strip_span(text: str, a: int, b: int) -> tuple[int, int]:
    while a < b and text[a] in " \t\n,;:":
        a += 1
    while b > a and text[b - 1] in " \t\n,;:":
        b -= 1
    return a, b


def _coord_pieces(sentence: str) -> list[tuple[int, int]]:
    pieces, cursor, coord = [], 0, [False]
    for m in _COORD_BREAK.finditer(sentence):
        if m.start() <= cursor or m.end() >= len(sentence):
            continue
        pieces.append((cursor, m.start()))
        coord.append(bool(re.search(r"\b(?:and|but|then|also|or|plus|while|yet|so)\b", m.group(), re.I)))
        cursor = m.end()
    pieces.append((cursor, len(sentence)))
    pieces = [(a, b, c) for (a, b), c in zip(pieces, coord, strict=True) if (a, b) != _strip_span(sentence, a, b) or True]
    pieces = [(*_strip_span(sentence, a, b), c) for a, b, c in pieces]
    pieces = [(a, b, c) for a, b, c in pieces if b > a]
    merged: list[tuple[int, int]] = []
    for a, b, c in pieces:
        prev = sentence[merged[-1][0]:merged[-1][1]] if merged else ""
        if merged and not c and _QUANT_LEAD.match(sentence[a:b]) and not _TASK_HEAD.match(prev):
            merged[-1] = (merged[-1][0], b)
        elif merged and not c and _FRONTED_ADVERBIAL.match(prev) and not _FRONTED_BLOCK.search(prev) and len(prev.split()) <= 8:
            merged[-1] = (merged[-1][0], b)  # "At the end of your response, please add ..." is one clause
        elif merged and _BOUNDED_ATTACH.match(sentence[a:b]) and not _TASK_HEAD.match(prev) and not _BOUNDED_ATTACH.match(prev):
            merged[-1] = (merged[-1][0], b)  # "... is in English, and in all capital letters": a shared verb is one clause
        elif merged and c and re.match(r"(?:give|provide|write|answer|respond)\b.{0,30}$", sentence[a:b], re.I) and re.match(r"(?:first|repeat|before)", prev, re.I):
            merged[-1] = (merged[-1][0], b)  # "First repeat the request, then give your answer" is one ordering instruction
        else:
            merged.append((a, b))
    return merged


def _attach_pieces(seg: str) -> list[tuple[int, int]]:
    """Split a TASK-headed piece into head / attachment(s) / task tail(s)."""
    out: list[tuple[int, int]] = []
    cursor = 0
    first = True
    last_was_att = False
    while True:
        m = _ATTACH_START.search(seg, cursor)
        while m and _MANNER_VERB_TAIL.search(seg[:m.start()]) and re.match(r"(?:as|like)\s", seg[m.end():], re.I):
            m = _ATTACH_START.search(seg, m.end())  # "act like a pirate": the manner phrase belongs to the verb
        if not m:
            out.append((cursor, len(seg)))
            break
        if first and _HEAD_DIRECTIVE.search(seg[:m.start()]):
            return [(0, len(seg))], False  # "provide less than 10 sentences in ...": the head is itself the directive
        first = False
        head_end = m.start()
        att_start = m.end()
        if out and re.fullmatch(r"[\s,]*(?:and|or|but also|as well as)?\s*", seg[out[-1][1]:head_end]) and out[-1][0] >= (out[0][1] if len(out) > 1 else 0) and last_was_att:
            bm = _BOUNDED_ATTACH.match(seg, att_start)
            att_end = bm.end() if bm and bm.end() > att_start else len(seg)
            out[-1] = (out[-1][0], att_end)  # "in all capital letters and in English": one coordinated attachment
            cursor = att_end
            if cursor >= len(seg):
                break
            continue
        if head_end > cursor:
            out.append((cursor, head_end))
            last_was_att = False
        bm = _BOUNDED_ATTACH.match(seg, att_start)
        if bm and bm.end() > att_start:
            att_end = bm.end()
        else:
            skip = re.match(r"(?:\S+\s+){0,2}\S*", seg[att_start:]).end()  # the head + 2 words belong to it
            nxt = _ATTACH_START.search(seg, att_start + skip)
            top = _TOPIC_HEAD.search(seg, att_start + skip)
            col = re.compile(r":\s|,\s+(?=(?:in|with|without|using|as|like|sounding|written|keeping|making)\s)").search(seg, att_start + skip)
            ends = [x.start() for x in (nxt, top, col) if x] + [len(seg)]
            att_end = min(ends)
        out.append((att_start, att_end))
        last_was_att = True
        cursor = att_end
        if cursor >= len(seg):
            break
        top = _TOPIC_HEAD.match(seg, cursor)
        if top:  # task tail: consume up to the next attachment
            nxt = _ATTACH_START.search(seg, top.end())
            tail_end = nxt.start() if nxt else len(seg)
            out.append((top.end(), tail_end))
            last_was_att = False
            cursor = tail_end
            if cursor >= len(seg):
                break
    out = [(a, b) for a, b in (_strip_span(seg, a, b) for a, b in out) if b > a and re.search(r"[A-Za-z0-9]", seg[a:b])]
    # a bare lead ("Answer", "Please write it") merges into its attachment
    if len(out) >= 2 and _BARE_HEAD.match(seg[out[0][0]:out[0][1]]):
        out = [(out[0][0], out[1][1])] + out[2:]
        return out, False
    return out, True


def split_clauses(sentence: str) -> list[tuple[int, int]]:
    """Char spans (within ``sentence``) of its clauses: coordination splits
    first (separators dropped), then — inside TASK-headed pieces only — the
    constraint post-modifiers ("with at least 300 words", "without ...",
    "in all lowercase", "in JSON", "that includes ...") become their own
    clauses, and a numeral-in-NP length ("a 150+ word ad") is emitted as a
    sub-span of its task head.  Directive-headed pieces are never split by
    post-modifiers ("highlight at least 3 sections that has titles in
    markdown" stays one clause)."""
    out: list[tuple[int, int]] = []
    for a, b in _coord_pieces(sentence):
        seg = sentence[a:b]
        if not re.search(r"[A-Za-z0-9]", seg):
            continue
        if _TASK_HEAD.match(seg) and not _HARD_PROHIB_LEAD.match(_DISCOURSE.sub("", _norm(seg))):
            subs, head_is_task = _attach_pieces(seg)
            for ca, cb in subs:
                out.append((a + ca, a + cb))
            head = seg[subs[0][0]:subs[0][1]]
            m = _NP_LENGTH.search(head)
            topic_after = m and _TOPIC_HEAD.search(head, m.end())
            if m and (head_is_task or topic_after) and len(head.split()) > len(m.group().split()) + 1:
                out.append((a + subs[0][0] + m.start(), a + subs[0][0] + m.end()))
        else:
            out.append((a, b))
    return sorted(set(out))


# ======================================================================== cues
_WB = r"(?<![a-z'])"
_PATTERNS: dict[str, str] = {
    "deontic": _WB + r"(?:must|should|shall|ought to|needs? to|has to|have to|required|require|be sure|make sure|making sure|ensure|ensuring|"
                     r"mandatory|is expected|are expected|is to be|are to be|has to be|is not allowed|are not allowed|not allowed|is allowed|only)\b",
    "prohibition": _WB + r"(?:do not|don't|never|not allowed|avoid|avoiding|refrain|no other|without|cannot|can't|must not|should not|"
                         r"shouldn't|mustn't|forbidden|exclude|omit|not permitted|nothing else|not (?:include|contain|use|mention|say|add|exceed|have|output|write|be)|"
                         r"no (?:\w+ ){0,2}?(?:words?|commas?|capital|lowercase|uppercase|other|more|less|fewer|mention|use|punctuation|letters?|numbers?|bullet|emoji|markdown))\b",
    "quantifier": _WB + r"(?:at least|at most|no more than|no fewer than|no less than|fewer than|less than|more than|exactly|minimum|maximum|"
                        r"between|up to|or more|or fewer|or less|in total|a total of|under \d|over \d|within \d|\d+\+|times\b|per line|one per|"
                        r"only once|twice|thrice|once)\b",
    "numeral": r"(?:\b\d+\b|" + _WB + r"(?:" + _NUM + r")\b)",
    "quoted_literal": r"(?:\"[^\"]{1,200}\"|“[^”]{1,200}”|(?<![a-z])'[^']{1,120}'(?![a-z])|<<[^>]{1,120}>>|\[[^\]]{1,60}\]|\*{3,}|\*[^*\n]{1,80}\*|\bP\.?P?\.?S\b)",
    "colon_literal": r":\s*\S",
    "output_ref": _WB + r"(?:(?:your|the|this|entire|whole|final|my) (?:entire |whole |final |own )?(?:response|reply|answer|output|result|responses|replies|answers)|"
                        r"in your (?:response|reply|answer|output|writing|text)|the (?:request|prompt|question|text|instruction|sentence|passage|message)s? (?:above|below)|"
                        r"repeat (?:the|this|it|all|every)|the (?:essay|letter|email|poem|story|summary|article|blog post|description|itinerary|resume|speech|song|riddle|"
                        r"joke|limerick|haiku|rap|dialogue|script|proposal|report|pitch|review|note|outline|template|page|quiz|tweet|sales pitch|whole|entire) "
                        r"(?:should|must|needs|has|is to|cannot|can't|shouldn't|will))\b",
    "form_noun": _WB + r"(?:words?|sentences?|paragraphs?|bullet(?: points?)?|bullets|letters?|commas?|title|phrase|sections?|placeholders?|"
                       r"capital(?:s|ized|ised)?|lowercase|uppercase|lower case|upper case|postscript|post script|p\.s\.?|p\.p\.s\.?|markdown|json|xml|html|"
                       r"quotation marks?|quotes?|language|" + _LANGS.rstrip("|") + r"|highlight(?:ed|s)?|keywords?|characters?|lines?|asterisks?|"
                       r"dividers?|format|punctuation|syllables?|stanzas?|headings?|headers?|bold|italics?|italicized|emoji|hashtags?|footnotes?|"
                       r"double (?:angular )?brackets|square brackets|parentheses|caps|case|tone|style|voice|structured|list|table|new lines?|linebreaks?|"
                       r"parts?|versions?|items?|options?|entries?|points?|the form of|the format of|the style of|comments?|snippets?|notations?|equations?|"
                       r"headlines?|captions?|footers?|signature|greeting|salutation|call to action|thesis|tagline|slogan|disclaimer|pages?|"
                       r"exclamation marks?|question marks?|numbers?|digits?|pronouns?|conjunctions?|vowels?|consonants?|palindromes?|verbs?|nouns?|adjectives?)\b",
    "content_verb": _WB + r"(?:include|includes|including|contain|contains|containing|mention|mentions|mentioning|use|uses|using|say|saying|repeat|repeating|appear|appears|appearing|highlight|highlighting|feature|featuring|wrap|wrapping|end|ending|start|starting|begin|beginning|finish|finishing|separate|separated|separating|avoid|avoiding)\b",
    "tone_word": _WB + r"(?:formal|informal|casual|funny|humorous|angry|angrily|chatty|polite|politely|excited|friendly|serious|sarcastic|professional|"
                       r"enthusiastic|cheerful|gloomy|sad|happy|upbeat|dramatic|poetic|concise|brief|short|long|detailed|verbose|engaging|witty|"
                       r"zany|weird|strange|rocky|persuasive|neutral|objective|respectful|rude|calm|passionate|whimsical|sound (?:like|more|less)|sounding|"
                       r"interesting|boring|fun|playful|lighthearted|dark|optimistic|pessimistic|romantic|scary|spooky|creepy|mysterious|inspiring|"
                       r"motivational|encouraging|uplifting|sincere|heartfelt|emotional|deadpan|edgy|cheeky|quirky|eloquent|elegant|vivid|imaginative|creative|"
                       r"tone|style|voice|manner|mood|register|like a|as if you|imagine (?:that )?you|you are (?:a|an|giving|talking|speaking|writing)|persona|character|act (?:like|as)|pretend)\b",
    "format_word": _WB + r"(?:json|xml|html|yaml|csv|markdown|latex|bullet|bullets|bulleted|numbered|list|table|sections?|paragraphs?|title|"
                         r"lowercase|uppercase|capital|caps|bold|italic|italics|quotation|quotes|brackets|placeholder|placeholders|separated|separate|"
                         r"wrap|wrapped|divider|highlight|highlighted|format|structured|template|" + _LANGS.rstrip("|") + r"|language|form of|"
                         r"postscript|p\.s\.|p\.p\.s|new lines?|linebreak|stanza|stanzas|verse)\b",
    "restrictor": _WB + r"(?:only|solely|entirely|exclusively|strictly|whatsoever|throughout|at all|nothing (?:else|but)|anywhere|everywhere|always|"
                        r"never|at the (?:very )?(?:beginning|end|start)|first|last|before|after|verbatim|word for word|word by word|exact|exactly|precisely)\b",
    "universal": _WB + r"(?:all|every|each|entire|whole|any|none|no|both|everything|nothing)\b",
    "second_person": _WB + r"(?:you|your|yours|yourself)\b",
    "first_person": _WB + r"(?:i|me|my|mine|we|our|us|i'm|i've|i'd|i'll|we're)\b",
    "third_person": _WB + r"(?:he|she|they|him|her|his|hers|their|them|its|it was|it is|it's)\b",
    "past_tense_be": _WB + r"(?:was|were|had|did|became|been)\b",
    "copula_present": _WB + r"(?:is|are|has|have)\b",
    "task_frame": _WB + r"(?:for (?:a|an|my|our|the|local|your)\b|about\b|on the topic|regarding|to my|as if|for me\b|i want|i need|i would like|i'd like|"
                        r"can you|could you|would you|write (?:a|an|me|the|two|some)\b|tell me|help me|let's|imagine|you are a|explain|describe|summarize)",
    "genre_noun": _WB + r"(?:essay|poem|story|letter|email|e-mail|summary|note|account|article|blog post|blog|itinerary|resume|résumé|cover letter|"
                        r"review|speech|song|rap|riddle|joke|limerick|haiku|dialogue|script|proposal|report|pitch|advertisement|ad|description|"
                        r"explanation|tweet|post|lyrics|biography|profile|plan|guide|tutorial|outline|abstract|piece|passage|quiz|template|rant|file|document)\b",
    "interrogative": r"^(?:what|why|how|who|when|where|which|is|are|do(?! not)|does|can|could|would|should) ",
    "attachment_head": r"^(?:with|without|using|in|that|which|containing|including|separated|wrapped|written|formatted|ending|starting|beginning|"
                       r"making|ensuring|avoiding|keeping|mentioning|highlighting|sounding|limited|restricted|no longer|no shorter|no more|of|as a|as an|as if|like a|all in)\b",
    "lead_task_verb": r"^(?:write|describe|compose|draft|create|explain|tell|generate|produce|summarize|summarise|rewrite|outline|discuss|develop|craft|"
                      r"imagine|come|help|can|could|would|plan|suggest|recommend|design|build|prepare|make me|give me|send|share|translate|elaborate|"
                      r"expand|continue|critique|review|analyze|analyse|take|complete|name|what|why|how|who|when|where|which|is|are|do you|does|i|my|we|our|hi|hello|hey|thanks|thank)\b",
    "lead_directive": r"^(?:use|include|avoid|wrap|end|start|begin|finish|keep|make (?:sure|it|the|your|this|them|every|all|each)|ensure|respond|reply|answer|highlight|repeat|refrain|mention|"
                      r"limit|format|separate|put|add|give|provide|do not|don't|never|always|capitalize|capitalise|express|refer|organize|organise|place|"
                      r"italicize|bold|indent|number|restrict|exclude|omit|conclude|close|open|contain|structure|divide|split|present|label|mark|surround|"
                      r"enclose|preface|introduce|choose|pick|stick|stay|remain|be|have|must|should|only|no|not|there|in your|your|the (?:response|reply|"
                      r"answer|output|result|text|essay|whole|entire|word|letter|first|last|second|third|final|\w+ should|\w+ must)|all|every|each|it|words|letters|sentences|paragraphs|"
                      r"at least|at most|exactly|say|act|sound|write (?:at least|at most|exactly|only|in|using|with|no)|answer|respond)\b",
    "lead_subject_modal": r"^(?:the|your|this|each|every|all|there|no|none|words|letters|sentences|paragraphs|it|in your|my|any|everything|nothing|both|you|responses)\b"
                          r".{0,80}?\b(?:should|must|shall|need|needs|has to|have to|cannot|can't|may not|is to|are to|ought|will)\b",
}
_ORDER = list(_PATTERNS)
_COMPILED = {k: re.compile(v, re.I) for k, v in _PATTERNS.items()}
_DISCOURSE = re.compile(r"^(?:(?:please|kindly|also|and|then|first|firstly|just|now|next|finally|additionally|basically|moreover|furthermore|however|"
                        r"but|so|in this task|for this task|in particular|remember to|be sure to|make sure to|try to|you (?:must|should|need to|have to|"
                        r"are required to|are to|will)|you are not allowed to|you cannot|you can't|you may not|i want you to|i need you to|i'd like you to|"
                        r"i would like you to|let's)[,:]?\s+)+")
_HARD_PROHIB_LEAD = re.compile(r"^(?:do not|don't|never|avoid|refrain from|without (?:using|mentioning|saying|including|writing|adding|ever|any|the|these|those|this|commas?|"
                               r"capital|numbers|punctuation|a single|a title|a postscript|an? \w+ing)|no longer|under no circumstances|you (?:must|should|may|can)(?:not|n't)|"
                               r"(?:you are|you're) not (?:allowed|permitted)|(?:it|the \w+) (?:must|should|can)(?:not|n't))\b")
_HARD_FORM_LEAD = re.compile(r"^(?:make sure|ensure|be sure|end|start|begin|finish|conclude|wrap|enclose|surround|separate|repeat|highlight|italicize|italicise|capitalize|capitalise|bold|include|mention|"
                             r"use|put|add|insert|place|label|mark|format|keep|limit|restrict|organize|organise|structure|divide|split)\b")
_HARD_MANNER_LEAD = re.compile(r"^(?:be|sound|sounding|act|acting|behave|behaving|pretend|imagine|suppose|assume|speak|speaking|talk|keep (?:it|the \w+|your \w+)|make (?:it|this|the \w+|your \w+)|stay|remain|"
                               r"(?:it|this|the \w+|your \w+) (?:should|must|needs to|has to) (?:be|sound|feel|read))\b")
_BARE_VERB_HEAD = re.compile(r"^(?:please )?(?:write|respond|reply|answer|make|keep|do|put|present|deliver|give) (?:it|this|that|them|the \w+|your \w+|me)?\s*")
_DEONTIC_BE = re.compile(r"\b(?:you are|you're|are not allowed|are required|are expected|is to be|are to be|has to|have to|is expected|is required|is allowed|are allowed|is not allowed)\b")

FEATURE_NAMES: list[str] = _ORDER + [
    "directive_any", "binding_any", "directive_x_form", "attach_x_binding", "attach_x_form", "attach_x_content", "attach_x_tone", "attach_x_prohib",
    "directive_x_prohib", "lead_x_tone", "task_only", "narrative", "log_len", "is_first_clause",
]


def feature_patterns() -> dict[str, re.Pattern]:
    return dict(_COMPILED)


def _norm(clause: str) -> str:
    s = clause.strip().lower()
    s = re.sub(r"^[\s\-\*•\d\.\)\(]+(?=[a-z])", "", s)
    return re.sub(r"\s+", " ", s)


def cues(clause: str) -> dict[str, float]:
    s = _norm(clause)
    lead = _DISCOURSE.sub("", s)
    f = {}
    for name in _ORDER:
        target = lead if name.startswith("lead_") or name == "attachment_head" else s
        f[name] = float(bool(_COMPILED[name].search(target)))
    f["copula_present"] = float(bool(_COMPILED["copula_present"].search(_DEONTIC_BE.sub(" ", s))))
    return f


def featurize(clause: str, is_first: bool = True) -> np.ndarray:
    f = cues(clause)
    toks = re.findall(r"[a-z']+", _norm(clause))
    directive = float(f["deontic"] or f["prohibition"] or f["lead_directive"] or f["lead_subject_modal"])
    binding = float(f["quantifier"] or f["numeral"] or f["quoted_literal"] or f["restrictor"] or f["universal"] or f["colon_literal"])
    form = float(f["form_noun"] or f["format_word"] or f["output_ref"] or f["tone_word"])
    task_only = float(f["lead_task_verb"] and not directive and not binding and not f["attachment_head"])
    narrative = float((f["past_tense_be"] or f["third_person"]) and not directive and not f["attachment_head"])
    x = [f[n] for n in _ORDER] + [directive, binding, directive * form, f["attachment_head"] * binding, f["attachment_head"] * form,
                                  f["attachment_head"] * float(f["content_verb"] or f["quantifier"]), f["attachment_head"] * f["tone_word"], f["attachment_head"] * f["prohibition"],
                                  directive * f["prohibition"], f["lead_directive"] * f["tone_word"], task_only, narrative, math.log1p(len(toks)) - 2.0, float(is_first)]
    return np.asarray(x, dtype=np.float64)


# ====================================================================== types
_T_PROHIB = re.compile(r"\b(?:do not|don't|never|avoid|avoiding|refrain|without|not allowed|cannot|can't|must not|should not|shouldn't|mustn't|forbidden|"
                       r"exclude|omit|not permitted|no other|nothing else|not (?:include|contain|use|mention|say|add|have|output|write)|"
                       r"no (?:\w+ ){0,2}?(?:words?|commas?|capital|lowercase|uppercase|more|mention|use|punctuation|letters?|language|bullet|emoji|markdown|judgement))\b", re.I)
_T_LIMIT = re.compile(r"\b(?:at most|no more than|fewer than|less than|under \d+|within \d+|maximum|a maximum of|not exceed|not more than|or fewer|or less|"
                      r"only once|at most once|no longer than|limit|limited to|short(?:er)?|brief|concise|exactly|" + _NUM + r"\s+(?:or fewer|or less))\b", re.I)
_T_FORMAT = re.compile(r"\b(?:json|xml|html|yaml|csv|markdown|latex|bullet|bullets|bulleted|numbered|list|table|sections?|paragraphs?|title|lowercase|"
                       r"uppercase|capital|capitals|caps|bold|italic|italics|italicize|quotation|quotes|brackets|placeholders?|separated?|wrap|wrapped|"
                       r"divider|highlight|highlighted|format|formatted|structured|template|" + _LANGS.rstrip("|") + r"|language|form of|postscript|post script|"
                       r"p\.s\.?|p\.p\.s|new lines?|linebreak|stanzas?|verse|asterisks?|line|lines|indent|heading|headers?|rendered|labeled|label|mark)\b", re.I)
_T_TONE = re.compile(r"\b(?:formal|informal|casual|funny|humorous|angry|angrily|chatty|polite|politely|excited|friendly|serious|sarcastic|professional|"
                     r"enthusiastic|cheerful|gloomy|sad|happy|upbeat|dramatic|poetic|engaging|witty|zany|weird|strange|rocky|persuasive|neutral|"
                     r"objective|respectful|rude|calm|passionate|whimsical|interesting|sound (?:like|more|less|\w+)|tone|style|voice|manner|mood|register|like a|as if|"
                     r"persona|act (?:like|as)|pretend|appropriate for|child-friendly|kid-friendly)\b", re.I)
_T_ADD = re.compile(r"\b(?:include|includes|including|contain|contains|containing|use|uses|using|mention|mentions|add|end|ends|ending|start|starts|starting|"
                    r"begin|finish|repeat|at least|or more|minimum|a minimum of|more than|appear|appears|times|keywords?|the word|the letter|highlight|"
                    r"provide|give|say|wrap|put|separate|there should be|must be|should be|must have|should have|must contain|should contain|" + _NUM + r")\b", re.I)


def instruction_type(clause: str) -> str:
    """Reporting tag; precedence prohibition > limit > tone > format > additive."""
    if _T_PROHIB.search(clause):
        return "prohibition"
    if _T_LIMIT.search(clause):
        return "limit"
    if _T_TONE.search(clause) and not _T_FORMAT.search(clause):
        return "tone"
    if _T_FORMAT.search(clause):
        return "format"
    if _T_ADD.search(clause):
        return "additive"
    return "other"


# ================================================================ linguistic
def apply_floors(clause: str, z: float) -> float:
    """Hand floors (linguistic, NOT learned): a clause whose lead is a negative
    imperative, a manner imperative carrying a tone word, a form imperative
    with a bound literal / count / form noun, a bare numeral-unit phrase or a
    bounded constraint PP emitted by the segmenter, or a relative clause
    binding a count / literal, is a directive whatever the learned score says
    (the weak labels contain almost no short prohibitions / tone imperatives,
    so the fitted intercept of about -3.9 would otherwise drop "do not
    mention Y").  The shuffle control in the tests measures how much the
    learned weights still contribute."""
    lead = _DISCOURSE.sub("", _norm(clause))
    if _FRONTED_ADVERBIAL.match(lead) and ", " in lead:
        lead = _DISCOURSE.sub("", lead.split(", ", 1)[1])  # "To mark a word, wrap it in asterisks": test the main clause
    core = _BARE_VERB_HEAD.sub("", lead).rstrip(".!?")
    if _HARD_PROHIB_LEAD.match(lead) or (_HARD_MANNER_LEAD.match(lead) and _COMPILED["tone_word"].search(lead)):
        return max(z, 0.5)
    if core != lead.rstrip(".!?") and _BOUNDED_ATTACH.fullmatch(core):
        return max(z, 0.5)  # "write it in all capital letters": a bare verb plus a bounded constraint PP
    if _HARD_FORM_LEAD.match(lead) and any(_COMPILED[c].search(lead) for c in ("form_noun", "quoted_literal", "colon_literal", "numeral", "quantifier")):
        return max(z, 0.5)  # "End with: ...", "Include the word X", "Wrap it in quotes"
    if _NP_LENGTH.fullmatch(lead.rstrip(".!?")) or _BOUNDED_ATTACH.fullmatch(lead.rstrip(".!?")):
        return max(z, 0.5)  # a bare numeral-unit phrase ("150+ word") or a bounded constraint PP ("in all lowercase", "in JSON")
    if re.match(r"(?:that|which)\b", lead) and any(_COMPILED[c].search(lead) for c in ("quantifier", "numeral", "quoted_literal")):
        return max(z, 0.5)  # relative clause binding a count / literal ("that includes the word X at least 3 times")
    return z


@dataclass(frozen=True)
class LinguisticModel:
    w: np.ndarray
    b: float
    feature_names: list[str]

    def logit(self, clause: str, is_first: bool = True) -> float:
        return apply_floors(clause, float(featurize(clause, is_first) @ self.w + self.b))

    def score(self, clause: str, is_first: bool = True) -> float:
        return 1.0 / (1.0 + math.exp(-self.logit(clause, is_first)))

    def top_features(self, k: int = 10) -> list[tuple[str, float]]:
        order = np.argsort(-np.abs(self.w))[:k]
        return [(self.feature_names[i], float(self.w[i])) for i in order]

    def to_json(self) -> dict:
        return {"feature_names": self.feature_names, "w": self.w.tolist(), "b": self.b}

    @classmethod
    def from_json(cls, d: dict) -> LinguisticModel:
        return cls(np.asarray(d["w"], dtype=np.float64), float(d["b"]), list(d["feature_names"]))


def _fit_logistic(X: np.ndarray, y: np.ndarray, l2: float, lr: float, iters: int) -> tuple[np.ndarray, float]:
    """Class-balanced L2 logistic regression, full-batch GD from zero init."""
    n_pos, n_neg = max(y.sum(), 1.0), max((1 - y).sum(), 1.0)
    cw = np.where(y == 1, len(y) / (2 * n_pos), len(y) / (2 * n_neg))
    w = np.zeros(X.shape[1])
    b = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(X @ w + b)))
        g = cw * (p - y)
        w -= lr * (X.T @ g / len(y) + l2 * w)
        b -= lr * float(g.mean())
    return w, b


def fit_linguistic(examples, l2: float = 1e-3, lr: float = 0.3, iters: int = 3000) -> LinguisticModel:
    """``examples``: iterable of ClauseExample."""
    X = np.stack([featurize(e.clause, e.is_first) for e in examples]).astype(np.float64)
    y = np.asarray([e.label for e in examples], dtype=np.float64)
    w, b = _fit_logistic(X, y, l2, lr, iters)
    return LinguisticModel(w, b, list(FEATURE_NAMES))


def _load_linguistic() -> LinguisticModel:
    p = Path(__file__).with_name("salience2_weights.json")
    if p.exists():
        m = LinguisticModel.from_json(json.loads(p.read_text()))
        if m.feature_names == FEATURE_NAMES:
            return m
    return LinguisticModel(np.zeros(len(FEATURE_NAMES)), 0.0, list(FEATURE_NAMES))


DEFAULT_LINGUISTIC: LinguisticModel = _load_linguistic()


def is_trained(model=None) -> bool:
    m = model or DEFAULT_LINGUISTIC
    return bool(np.any(m.w != 0.0) or m.b != 0.0)


# ====================================================================== probe
LAYER = 20
USER_PREFIX = "<|im_start|>user\n"
USER_SUFFIX = "<|im_end|>"


@dataclass(frozen=True)
class ProbeModel:
    """Linear probe over layer-20 residuals: token logit = h . w + b."""
    w: np.ndarray  # (d_model,) float32
    b: float
    mu: np.ndarray  # feature mean used for centering (float32)
    sd: np.ndarray  # feature scale

    def token_logits(self, h: np.ndarray) -> np.ndarray:
        z = (h.astype(np.float32) - self.mu) / self.sd
        return z @ self.w + np.float32(self.b)

    def save(self, path: Path) -> None:
        np.savez(path, w=self.w.astype(np.float32), b=np.float32(self.b), mu=self.mu.astype(np.float32), sd=self.sd.astype(np.float32))

    @classmethod
    def load(cls, path: Path) -> ProbeModel:
        d = np.load(path)
        return cls(d["w"].astype(np.float32), float(d["b"]), d["mu"].astype(np.float32), d["sd"].astype(np.float32))


def fit_probe(H: np.ndarray, y: np.ndarray, l2: float = 1e-2, lr: float = 0.5, iters: int = 400) -> ProbeModel:
    """Full-batch GD logistic probe on standardized token features (float64, zero init)."""
    H = H.astype(np.float64)
    mu = H.mean(0)
    sd = H.std(0) + 1e-3
    Z = (H - mu) / sd
    w, b = _fit_logistic(Z, y.astype(np.float64), l2, lr, iters)
    return ProbeModel(w.astype(np.float32), float(b), mu.astype(np.float32), sd.astype(np.float32))


@dataclass(frozen=True)
class HybridModel:
    """Logistic over the linguistic features plus the probe's clause logit
    (scaled by 1/4), same floors as the linguistic model."""
    w: np.ndarray
    b: float
    probe: ProbeModel

    def logit(self, clause: str, is_first: bool, h_clause: np.ndarray) -> float:
        pz = float(self.probe.token_logits(h_clause[None])[0]) / 4.0
        x = np.concatenate([featurize(clause, is_first), [pz]])
        return apply_floors(clause, float(x @ self.w + self.b))

    def to_json(self) -> dict:
        return {"feature_names": FEATURE_NAMES + ["probe_logit/4"], "w": self.w.tolist(), "b": self.b}


def fit_hybrid(rows, probe_logits, l2: float = 1e-3, lr: float = 0.3, iters: int = 3000) -> tuple[np.ndarray, float]:
    """``rows``: ClauseRow list; ``probe_logits``: cross-fitted probe logit per row."""
    X = np.stack([np.concatenate([featurize(r.clause, r.is_first), [pz / 4.0]]) for r, pz in zip(rows, probe_logits, strict=True)])
    y = np.asarray([r.label for r in rows], dtype=np.float64)
    return _fit_logistic(X, y, l2, lr, iters)


def _load_probe() -> ProbeModel | None:
    p = Path(__file__).with_name("salience2_probe.npz")
    return ProbeModel.load(p) if p.exists() else None


DEFAULT_PROBE: ProbeModel | None = _load_probe()


def _load_hybrid() -> HybridModel | None:
    p = Path(__file__).with_name("salience2_hybrid.json")
    if DEFAULT_PROBE is None or not p.exists():
        return None
    d = json.loads(p.read_text())
    if d["feature_names"] != FEATURE_NAMES + ["probe_logit/4"]:
        return None
    return HybridModel(np.asarray(d["w"], dtype=np.float64), float(d["b"]), DEFAULT_PROBE)


DEFAULT_HYBRID: HybridModel | None = _load_hybrid()


class H20Extractor:
    """Frozen Qwen3-1.7B layer-20 residuals for a single user turn, batch 1,
    bf16 on CUDA (bitwise repeatable under stencil.determinism)."""

    def __init__(self, root: Path | None = None, device: str = "cuda"):
        import torch
        from tokenizers import Tokenizer

        from stencil import determinism  # noqa: F401  (must precede torch CUDA init)
        from stencil.qwen3 import Qwen3
        root = root or Path(__file__).resolve().parents[2]
        self.tok = Tokenizer.from_file(str(root / "models/qwen3-1.7b-hf/tokenizer.json"))
        m = Qwen3()
        m.load_state_dict(torch.load(root / "models/qwen3-1.7b.pt", map_location="cpu"), strict=True)
        self.model = m.to(torch.bfloat16).to(device).eval()
        self.device = device
        self.torch = torch

    def __call__(self, text: str) -> tuple[list[tuple[int, int]], np.ndarray]:
        """(char offsets of the text's own tokens, h20[T, d]) — template tokens dropped."""
        full = USER_PREFIX + text + USER_SUFFIX
        enc = self.tok.encode(full)
        with self.torch.no_grad():
            h = self.model(self.torch.tensor([enc.ids], device=self.device), return_hidden=LAYER)[0].float().cpu().numpy()
        lo, hi = len(USER_PREFIX), len(USER_PREFIX) + len(text)
        keep = [i for i, (a, b) in enumerate(enc.offsets) if a >= lo and b <= hi and b > a]
        offs = [(enc.offsets[i][0] - lo, enc.offsets[i][1] - lo) for i in keep]
        return offs, h[keep]


def clause_token_index(offsets, a: int, b: int) -> list[int]:
    return [i for i, (s, e) in enumerate(offsets) if s < b and e > a]


# ================================================================== extraction
def _sentence_clause_spans(text: str):
    for sa, sb in split_sentences(text):
        cl = split_clauses(text[sa:sb])
        for j, (ca, cb) in enumerate(cl):
            yield (sa + ca, sa + cb, j == 0)


def extract_instructions(text: str, backend: str = "linguistic", model=None, h20=None,
                         extractor: H20Extractor | None = None, threshold: float = 0.0) -> list[Span]:
    """Clause-level instruction spans of ``text`` (a single user turn).

    backend="linguistic": ``model`` is a LinguisticModel (default: committed).
    backend="probe": ``h20`` = (offsets, H) from an H20Extractor for exactly
    this text, or ``extractor`` to compute it; ``model`` is a ProbeModel.
    The decision is mean-logit > threshold over the clause (its tokens).
    """
    spans: list[Span] = []
    if backend == "linguistic":
        m = model or DEFAULT_LINGUISTIC
        if not is_trained(m):
            raise RuntimeError("salience2 linguistic model is untrained (all-zero); run `python -m stencil.salience2`")
        for a, b, first in _sentence_clause_spans(text):
            clause = text[a:b]
            if len(re.findall(r"[A-Za-z]", clause)) < 2:
                continue
            z = m.logit(clause, first)
            if z > threshold:
                spans.append(Span(a, b, instruction_type(clause), z))
    elif backend in ("probe", "hybrid"):
        m = model or (DEFAULT_PROBE if backend == "probe" else DEFAULT_HYBRID)
        if m is None:
            raise RuntimeError(f"salience2 {backend} weights missing; run `python -m stencil.salience2 --probe`")
        if h20 is None:
            if extractor is None:
                raise ValueError(f"backend={backend!r} needs h20=(offsets, H) or an extractor")
            h20 = extractor(text)
        offsets, H = h20
        for a, b, first in _sentence_clause_spans(text):
            idx = clause_token_index(offsets, a, b)
            clause = text[a:b]
            if not idx or len(re.findall(r"[A-Za-z]", clause)) < 2:
                continue
            hc = H[idx].astype(np.float32).mean(0)
            z = float(m.token_logits(hc[None])[0]) if backend == "probe" else m.logit(clause, first, hc)
            if z > threshold:
                spans.append(Span(a, b, instruction_type(clause), z))
    else:
        raise ValueError(backend)
    return _dedupe_nested(spans)


def _dedupe_nested(spans: list[Span]) -> list[Span]:
    """When a numeral-NP sub-span AND its enclosing task clause both fire,
    keep the tighter one (the enclosing clause is the task)."""
    out = []
    for s in spans:
        if any(s.start <= o.start and s.end >= o.end and (o.start, o.end) != (s.start, s.end) for o in spans):
            continue
        out.append(s)
    return out


def probe_runs(text: str, h20, model: ProbeModel | None = None, threshold: float = 0.0) -> list[Span]:
    """Splitter-free decoder: maximal runs of positive-logit tokens, snapped
    outward to word boundaries (reported alongside the clause decoder)."""
    m = model or DEFAULT_PROBE
    offsets, H = h20
    logits = m.token_logits(H)
    out: list[Span] = []
    i = 0
    while i < len(offsets):
        if logits[i] > threshold:
            j = i
            while j + 1 < len(offsets) and logits[j + 1] > threshold:
                j += 1
            a, b = offsets[i][0], offsets[j][1]
            while a > 0 and text[a - 1].isalnum():
                a -= 1
            while b < len(text) and text[b].isalnum():
                b += 1
            seg = text[a:b]
            if len(re.findall(r"[A-Za-z]", seg)) >= 2:
                out.append(Span(a, b, instruction_type(seg), float(logits[i:j + 1].mean())))
            i = j + 1
        else:
            i += 1
    return out


# =================================================================== matching
def _core(s: str) -> str:
    return s.strip(" \t\n.,;:!?\"'“”’()[]")


def match_spans(pred: list[tuple[int, int]], gold: list[tuple[int, int]], text: str, thr: float = 0.5) -> tuple[int, int, int]:
    """Greedy one-to-one matching: a prediction matches a gold clause when their
    character overlap covers >= ``thr`` of BOTH (after trimming punctuation).
    Returns (tp, fp, fn)."""
    def trim(a, b):
        seg = text[a:b]
        lead = len(seg) - len(seg.lstrip(" \t\n.,;:!?\"'“”’()[]"))
        trail = len(seg) - len(seg.rstrip(" \t\n.,;:!?\"'“”’()[]"))
        return a + lead, max(a + lead, b - trail)
    P = [trim(*p) for p in pred]
    G = [trim(*g) for g in gold]
    used = set()
    tp = 0
    for pa, pb in P:
        best = None
        for gi, (ga, gb) in enumerate(G):
            if gi in used:
                continue
            ov = max(0, min(pb, gb) - max(pa, ga))
            if ov >= thr * max(1, pb - pa) and ov >= thr * max(1, gb - ga):
                if best is None or ov > best[0]:
                    best = (ov, gi)
        if best is not None:
            used.add(best[1])
            tp += 1
    return tp, len(P) - tp, len(G) - tp


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    return p, r, 2 * p * r / max(p + r, 1e-12)


# ==================================================================== corpora
@dataclass(frozen=True)
class Doc:
    """A marker-free user text with gold/weak instruction clause spans."""
    text: str
    spans: tuple[tuple[int, int], ...]
    source: str
    kinds: tuple[str, ...] = ()  # per-span provenance ids (b3 / ifbench instruction ids, 'tone', 'mif')


@dataclass(frozen=True)
class ClauseExample:
    clause: str
    label: int
    is_first: bool
    source: str


_MARKER = re.compile(r"\bConstraint:\s*", re.I)
_META = "Every earlier constraint from this conversation still applies to this reply as well."


def _recase(c: str) -> str:
    c = c.strip()
    c = c[0].upper() + c[1:]
    return c if c[-1] in ".!?" else c + "."


def load_b3_docs(root: Path, files=("data/b3/train-v43.jsonl", "data/b3/cal-v45.jsonl", "data/b3/mt-train-300.jsonl")) -> list[Doc]:
    """Synthetic prompts rebuilt WITHOUT the marker: framing sentence (task)
    followed by each constraint as an ordinary re-cased sentence."""
    docs: list[Doc] = []
    for rel in files:
        for line in (root / rel).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            prompts = [t["prompt"] for t in r["turns"]] if "turns" in r else [r["prompt"]]
            for p in prompts:
                p = p.replace(_META, "").strip()
                parts = _MARKER.split(p)
                framing, cons = parts[0].strip(), [c.strip() for c in parts[1:] if c.strip()]
                text = framing
                spans = []
                for c in cons:
                    c = _recase(c)
                    a = len(text) + 1
                    text = text + " " + c
                    spans.append((a, a + len(c)))
                assert "Constraint:" not in text
                docs.append(Doc(text, tuple(spans), "b3", tuple("b3" for _ in spans)))
    return docs


def load_b3_prose(root: Path, cap: int = 800) -> list[Doc]:
    """Narrative negatives: prose sentences from canonical responses."""
    out: list[Doc] = []
    seen: set[str] = set()
    for rel in ("data/b3/train-v43.jsonl", "data/b3/cal-v45.jsonl"):
        for line in (root / rel).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            for a, b in split_sentences(r.get("canonical", "")):
                s = r["canonical"][a:b]
                if len(s.split()) < 6 or not re.match(r"^[A-Z][a-z]", s) or re.search(r"[*#<>\[\]|{}]|P\.S|^\w+:", s):
                    continue
                if s.lower() in seen:
                    continue
                seen.add(s.lower())
                out.append(Doc(s, (), "b3-prose"))
                if len(out) >= cap:
                    return out
    return out


def eval_multiif_turns(root: Path) -> list[tuple[str, int, str]]:
    out = []
    for line in (root / "data/bench/multiif_en.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        for t in (1, 2, 3):
            p = r.get(f"turn_{t}_prompt")
            if p:
                out.append((r["key"], t, json.loads(p)["content"]))
    return out


def eval_load_multiif23_docs(root: Path, exclude_texts: set[str] = frozenset()) -> list[Doc]:
    """Multi-IF turn-2/3 prompts are instruction-only by construction: every
    clause is a positive.  Turns containing an excluded sentence are dropped."""
    docs: list[Doc] = []
    seen: set[str] = set()
    for _, t, content in eval_multiif_turns(root):
        if t == 1 or content in seen or any(content[a:b] in exclude_texts for a, b in split_sentences(content)):
            continue
        seen.add(content)
        spans = [(a, b) for a, b, _f in _sentence_clause_spans(content) if len(re.findall(r"[A-Za-z]", content[a:b])) >= 2]
        docs.append(Doc(content, tuple(spans), "multiif23", tuple("mif" for _ in spans)))
    return docs


def eval_load_conv_prose(root: Path, cap: int = 800) -> list[Doc]:
    """Narrative negatives from recorded Qwen responses (read-only)."""
    import glob
    out: list[Doc] = []
    seen: set[str] = set()
    for f in sorted(glob.glob(str(root / "results/qwen/b4-multiif-base/conv-*.json"))):
        j = json.loads(Path(f).read_text())
        for resp in j.get("responses", {}).values():
            for a, b in split_sentences(resp):
                s = resp[a:b]
                if len(s.split()) < 6 or not re.match(r"^[A-Z][a-z]", s) or re.search(r"[*#<>\[\]|{}]|P\.S|^\w+:", s) or s.lower() in seen:
                    continue
                seen.add(s.lower())
                out.append(Doc(s, (), "conv-prose"))
                if len(out) >= cap:
                    return out
    return out


# --- buried synthesis
_BURY_TEMPLATES: dict[str, list[str]] = {
    # id -> attachment templates (kwargs formatted in); {n}, {w}, {ws}, {lang}
    "length_constraints:number_words": ["with {rel} {n} words", "in {rel} {n} words", "using {rel} {n} words", "that is {rel} {n} words long"],
    "length_constraints:number_sentences": ["in {rel} {n} sentences", "with {rel} {n} sentences", "that has {rel} {n} sentences"],
    "length_constraints:number_paragraphs": ["in exactly {n} paragraphs", "with exactly {n} paragraphs separated by ***"],
    "detectable_format:number_bullet_lists": ["as exactly {n} bullet points", "with exactly {n} markdown bullet points"],
    "keywords:forbidden_words": ["without using the words {ws}", "without ever mentioning {ws}", "avoiding the words {ws}"],
    "keywords:existence": ["that includes the keywords {ws}", "including the words {ws}", "using the keywords {ws}"],
    "keywords:frequency": ["that uses the word {w} at least {n} times", "mentioning {w} at least {n} times", "with the word {w} appearing at least {n} times"],
    "keywords:letter_frequency": ["with the letter {w} appearing at least {n} times", "that contains the letter {w} at least {n} times"],
    "change_case:english_capital": ["in all capital letters", "using only capital letters", "written entirely in uppercase"],
    "change_case:english_lowercase": ["in all lowercase letters", "using no capital letters", "all in lowercase"],
    "language:response_language": ["in {lang}", "written in the {lang} language", "using only {lang}"],
    "detectable_content:number_placeholders": ["with at least {n} placeholders in square brackets like [name]", "containing at least {n} bracketed placeholders"],
    "detectable_content:postscript": ["ending with a postscript that starts with P.S.", "with a P.S. at the end"],
    "detectable_format:title": ["with a title wrapped in double angular brackets like <<title>>", "that has a title in <<double angular brackets>>"],
    "detectable_format:json_format": ["in JSON format", "formatted as a JSON block", "as a JSON object"],
    "punctuation:no_comma": ["without using any commas", "with no commas at all", "avoiding commas entirely"],
    "startend:quotation": ["wrapped in double quotation marks", "with the whole thing inside double quotation marks"],
    "detectable_format:number_highlighted_sections": ["with at least {n} sections highlighted in markdown like *this*", "highlighting at least {n} parts with *asterisks*"],
    "detectable_format:multiple_sections": ["in {n} sections each marked SECTION X", "with {n} sections labeled Section X"],
    "tone": ["in a formal tone", "in a casual, chatty style", "in an angry voice", "sounding excited about it", "in the style of a pirate",
             "as if you were a medieval bard", "in a very serious manner", "keeping the tone light and funny"],
}
_REL_WORDS = {"at least": ["at least", "no fewer than", "a minimum of"], "less than": ["under", "fewer than", "at most", "less than"]}


def _fmt(t: str, kw: dict, i: int) -> str | None:
    n = kw.get("num_words") or kw.get("num_sentences") or kw.get("num_paragraphs") or kw.get("num_bullets") or kw.get("frequency") or kw.get("let_frequency") or kw.get("num_placeholders") or kw.get("num_highlights") or kw.get("num_sections") or 3
    rel = kw.get("relation") or kw.get("let_relation") or "at least"
    rel = _REL_WORDS.get(rel, [rel])[i % len(_REL_WORDS.get(rel, [rel]))]
    words = kw.get("forbidden_words") or kw.get("keywords") or []
    ws = " or ".join(f"'{w}'" for w in words) if words else "'harbor' or 'signal'"
    w = kw.get("keyword") or kw.get("letter") or "lantern"
    lang = {"kn": "Kannada", "hi": "Hindi", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian", "ru": "Russian", "pt": "Portuguese",
            "ar": "Arabic", "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "ur": "Urdu", "fa": "Persian", "ko": "Korean", "ja": "Japanese",
            "zh": "Chinese", "vi": "Vietnamese", "th": "Thai", "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi", "sw": "Swahili", "bg": "Bulgarian", "ne": "Nepali", "fi": "Finnish"}.get(kw.get("language"), "French")
    return t.format(n=n, rel=rel, ws=ws, w=w, lang=lang)


def synthesize_buried(root: Path, files=("data/b3/train-v43.jsonl",), template_parity: int = 0, cap: int = 600) -> list[Doc]:
    """Buried variants: the b3 framing sentence with one constraint attached
    as a post-modifier ("Write a brief note about X for a community bulletin
    with at least 90 words.") and, for a second constraint, a coordinated
    negative clause.  ``template_parity`` picks even or odd templates so a
    held-out buried set uses templates the trainer never saw."""
    docs: list[Doc] = []
    for rel in files:
        for k, line in enumerate((root / rel).read_text().splitlines()):
            if not line.strip():
                continue
            r = json.loads(line)
            if "turns" in r:
                continue
            framing = _MARKER.split(r["prompt"])[0].strip().rstrip(".")
            ids, kws = r["instruction_id_list"], r["kwargs"]
            att = None
            for i, (iid, kw) in enumerate(zip(ids, kws, strict=True)):
                temps = _BURY_TEMPLATES.get(iid)
                if not temps:
                    continue
                cands = [t for j, t in enumerate(temps) if j % 2 == template_parity] or temps
                att = _fmt(cands[(k + i) % len(cands)], kw, k)
                break
            if att is None:
                continue
            tone_t = _BURY_TEMPLATES["tone"]
            tone = tone_t[k % len(tone_t)] if (k % 3 == 0) else None
            text = framing + " " + att
            spans = [(len(framing) + 1, len(text))]
            kinds = [ids[0]]
            if tone:
                text = text + ", " + tone
                spans.append((len(text) - len(tone), len(text)))
                kinds.append("tone")
            text += "."
            docs.append(Doc(text, tuple(spans), "buried", tuple(kinds)))
            if len(docs) >= cap:
                return docs
    return docs


# --- IFBench transfer gold (never trained on)
def eval_load_ifbench_docs(root: Path) -> list[Doc]:
    """IFBench prompts with GOLD spans = the vendored checker's own
    build_description text located in the prompt (numbers normalised);
    each located description is split into sentences.  Prompts whose
    description cannot be located are dropped (count reported)."""
    import sys
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from vendor.ifbench import instructions_registry as R
    docs: list[Doc] = []
    for line in (root / "data/bench/ifbench_test.jsonl").read_text().splitlines():
        r = json.loads(line)
        text = r["prompt"]
        spans, kinds = [], []
        ok = True
        for iid, kw in zip(r["instruction_id_list"], r["kwargs"], strict=True):
            ins = R.INSTRUCTION_DICT[iid](iid)
            kw = {k: v for k, v in kw.items() if v is not None}
            try:
                d = ins.build_description(**kw)
            except Exception:
                ok = False
                break
            d = re.sub(r"(\d+)\.0\b", r"\1", d.strip())
            pat = re.escape(d)
            pat = re.sub(r"(\d+)\\-th", r"\1-(?:th|st|nd|rd)", pat)
            pat = pat.replace(r"\ ", r"\s+")
            m = re.search(pat, text)
            if not m:
                ok = False
                break
            for a, b in split_sentences(text[m.start():m.end()]):
                spans.append((m.start() + a, m.start() + b))
                kinds.append(iid)
        if ok and spans:
            docs.append(Doc(text, tuple(sorted(set(spans))), "ifbench", tuple(kinds)))
    return docs


# --------------------------------------------------------------- clause sets
def clause_examples(docs: list[Doc], skip_unknown: bool = True) -> list[ClauseExample]:
    """Clause-level examples: every clause of every doc, labeled by overlap
    (>= 0.5 both ways) with a doc span; 'unknown'-kind spans are dropped."""
    out: list[ClauseExample] = []
    for d in docs:
        unknown = [s for s, k in zip(d.spans, d.kinds, strict=True) if k == "unknown"] if d.kinds else []
        gold = [s for s in d.spans if s not in unknown]
        for a, b, first in _sentence_clause_spans(d.text):
            clause = d.text[a:b]
            if len(re.findall(r"[A-Za-z]", clause)) < 2:
                continue
            if skip_unknown and any(_overlap((a, b), u) for u in unknown):
                continue
            label = int(any(_overlap((a, b), g) for g in gold))
            out.append(ClauseExample(clause, label, first, d.source))
    return out


def _overlap(p, g, thr: float = 0.5) -> bool:
    ov = max(0, min(p[1], g[1]) - max(p[0], g[0]))
    return ov >= thr * max(1, p[1] - p[0]) and ov >= thr * max(1, g[1] - g[0])


def evaluate_docs(docs: list[Doc], predict, thr: float = 0.5) -> dict:
    """predict(doc) -> list[(a, b)].  Returns micro P/R/F1 plus per-kind recall."""
    tp = fp = fn = 0
    per_kind: dict[str, list[int]] = {}
    fps: list[str] = []
    fns: list[str] = []
    for d in docs:
        pred = predict(d)
        gold = [s for s, k in zip(d.spans, d.kinds or ["?"] * len(d.spans), strict=True) if k != "unknown"]
        t, f, n = match_spans(pred, gold, d.text, thr)
        tp, fp, fn = tp + t, fp + f, fn + n
        for g, k in zip(d.spans, d.kinds or ["?"] * len(d.spans), strict=True):
            if k == "unknown":
                continue
            hit = any(_overlap(p, g, thr) for p in pred)
            per_kind.setdefault(k, []).append(int(hit))
            if not hit:
                fns.append(d.text[g[0]:g[1]])
        for p in pred:
            if not any(_overlap(p, g, thr) for g in gold):
                fps.append(d.text[p[0]:p[1]])
    p, r, f1 = prf(tp, fp, fn)
    return {"n_docs": len(docs), "tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1,
            "per_kind": {k: {"n": len(v), "recall": sum(v) / len(v)} for k, v in sorted(per_kind.items())},
            "false_positives": fps, "false_negatives": fns}


def training_docs(root: Path) -> dict[str, list[Doc]]:
    """Disjoint fitting corpora: b3 synthetic, buried variants, and b3 prose.

    ``real`` remains as an empty compatibility corpus for leave-one-corpus-out
    callers. Evaluation benchmarks and responses to them never enter a fit.
    """
    return {
        "synthetic": load_b3_docs(root) + synthesize_buried(root, template_parity=0) + load_b3_prose(root),
        "real": [],
    }


# ============================================================ probe training
FEATS_DIR = "results/salience2"


def cache_features(docs: list[Doc], extractor, path: Path) -> dict[str, tuple[list[tuple[int, int]], np.ndarray]]:
    """Layer-20 features for every doc text (float16 on disk, keyed by text).
    Incremental: texts already cached are not recomputed; ``extractor`` may be
    a zero-arg factory (called only when something is missing)."""
    feats: dict = {}
    if path.exists():
        z = np.load(path, allow_pickle=False)
        texts = json.loads(str(z["texts"]))
        counts, offs, H = z["counts"], z["offsets"], z["H"]
        at = 0
        for t, c in zip(texts, counts, strict=True):
            feats[t] = ([tuple(o) for o in offs[at:at + c].tolist()], H[at:at + c])
            at += c
    todo = [d.text for d in docs if d.text not in feats]
    if todo and not isinstance(extractor, H20Extractor):
        extractor = extractor()
    for i, t in enumerate(todo):
        o, h = extractor(t)
        feats[t] = (o, h.astype(np.float16))
        if (i + 1) % 500 == 0:
            print(f"  features {i + 1}/{len(todo)}", flush=True)
    if todo:
        texts = list(feats)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, texts=np.array(json.dumps(texts)), counts=np.array([len(feats[t][0]) for t in texts]),
                 offsets=np.concatenate([np.array(feats[t][0], dtype=np.int32).reshape(-1, 2) for t in texts]),
                 H=np.concatenate([feats[t][1] for t in texts]))
    return feats


@dataclass(frozen=True)
class ClauseRow:
    doc: int
    start: int
    end: int
    is_first: bool
    label: int | None  # None = unknown-kind clause (excluded from fitting)
    clause: str
    h: np.ndarray      # mean layer-20 residual over the clause's tokens


def clause_rows(docs: list[Doc], feats: dict) -> list[ClauseRow]:
    """Clause-level rows with mean-pooled trunk features (the probe's unit)."""
    out: list[ClauseRow] = []
    for di, d in enumerate(docs):
        offsets, H = feats[d.text]
        unknown = [sp for sp, k in zip(d.spans, d.kinds, strict=True) if k == "unknown"] if d.kinds else []
        gold = [sp for sp in d.spans if sp not in unknown]
        for a, b, first in _sentence_clause_spans(d.text):
            clause = d.text[a:b]
            idx = clause_token_index(offsets, a, b)
            if len(re.findall(r"[A-Za-z]", clause)) < 2 or not idx:
                continue
            label = None if any(_overlap((a, b), u) for u in unknown) else int(any(_overlap((a, b), g) for g in gold))
            out.append(ClauseRow(di, a, b, first, label, clause, H[idx].astype(np.float32).mean(0)))
    return out


def fit_clause_probe(rows: list[ClauseRow], l2: float = 1e-2) -> ProbeModel:
    rs = [r for r in rows if r.label is not None]
    return fit_probe(np.stack([r.h for r in rs]), np.asarray([r.label for r in rs], dtype=np.float64), l2=l2)


def cross_fitted_probe_logits(rows: list[ClauseRow]) -> list[float]:
    """2-fold (by doc parity) probe logits so the hybrid never sees in-sample probe scores."""
    even = [r for r in rows if r.doc % 2 == 0]
    odd = [r for r in rows if r.doc % 2 == 1]
    p_for_even, p_for_odd = fit_clause_probe(odd), fit_clause_probe(even)
    return [float((p_for_even if r.doc % 2 == 0 else p_for_odd).token_logits(r.h[None])[0]) for r in rows]


def token_dataset(docs: list[Doc], feats: dict, stride: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Per-token features / labels from clause-level weak labels (tokens of
    'unknown' clauses skipped)."""
    Hs, ys = [], []
    for d in docs:
        offsets, H = feats[d.text]
        unknown = [sp for sp, k in zip(d.spans, d.kinds, strict=True) if k == "unknown"] if d.kinds else []
        gold = [sp for sp in d.spans if sp not in unknown]
        for a, b, _first in _sentence_clause_spans(d.text):
            if len(re.findall(r"[A-Za-z]", d.text[a:b])) < 2 or any(_overlap((a, b), u) for u in unknown):
                continue
            label = int(any(_overlap((a, b), g) for g in gold))
            idx = clause_token_index(offsets, a, b)[::stride]
            if idx:
                Hs.append(H[idx])
                ys.append(np.full(len(idx), label, dtype=np.float64))
    return np.concatenate(Hs).astype(np.float32), np.concatenate(ys)


def _subsample(H: np.ndarray, y: np.ndarray, cap: int) -> tuple[np.ndarray, np.ndarray]:
    if len(y) <= cap:
        return H, y
    step = int(math.ceil(len(y) / cap))
    return H[::step], y[::step]


def main() -> None:
    import sys
    root = Path(__file__).resolve().parents[2]
    corpora = training_docs(root)
    docs = corpora["synthetic"] + corpora["real"]
    exs = clause_examples(docs)
    m = fit_linguistic(exs)
    out = Path(__file__).with_name("salience2_weights.json")
    out.write_text(json.dumps(m.to_json(), indent=1) + "\n")
    print(f"linguistic: fit on {len(exs)} clauses ({sum(e.label for e in exs)} pos) -> {out}")
    for name, w in m.top_features(12):
        print(f"  {w:+.3f}  {name}")
    if "--probe" in sys.argv:
        feats = cache_features(docs, lambda: H20Extractor(root), root / FEATS_DIR / "feats.npz")
        rows = clause_rows(docs, feats)
        pm = fit_clause_probe(rows)
        pm.save(Path(__file__).with_name("salience2_probe.npz"))
        labeled = [r for r in rows if r.label is not None]
        print(f"probe: fit on {len(labeled)} clauses ({sum(r.label for r in labeled)} pos) -> salience2_probe.npz")
        w, b = fit_hybrid(labeled, cross_fitted_probe_logits(labeled))
        hy = HybridModel(w, b, pm)
        Path(__file__).with_name("salience2_hybrid.json").write_text(json.dumps(hy.to_json(), indent=1) + "\n")
        print("hybrid: -> salience2_hybrid.json; top weights:", sorted(zip(hy.to_json()["feature_names"], w.round(2), strict=True), key=lambda t: -abs(t[1]))[:6])


if __name__ == "__main__":
    main()

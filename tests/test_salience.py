# ruff: noqa: E501
"""Salience classifier (LEDGER-PLAN.md component A): does a sentence state a
persistent requirement the model must honor in its output?

Gates (registered): leave-one-corpus-out F1 >= 0.90 on MARKER-FREE text, and
F1 >= 0.80 on 100 hand-labeled Multi-IF sentences the DEFAULT_MODEL never saw.
Anti-cheat is the headline: the 'Constraint:' marker is never a feature, every
b3 positive is stripped before training and testing, a label shuffle must
collapse F1, and refitting from the loaders must reproduce the committed
weights bitwise. No vacuous tests: every metric assertion also asserts the
evaluation set is non-trivial in size and class balance."""
import json
import re
from pathlib import Path

import numpy as np
import pytest

from stencil import salience as S

ROOT = Path(__file__).resolve().parent.parent
HAVE_DATA = (ROOT / "data/b3/train-v43.jsonl").exists() and (ROOT / "data/bench/multiif_en.jsonl").exists()
needs_data = pytest.mark.skipif(not HAVE_DATA, reason="corpora not on disk")

# ---------------------------------------------------------------- hand labels
# 100 unique Multi-IF TURN-1 sentences (raw IFEval prompts, the hard mixed case;
# never in any training set; sampled by S.sample_multiif_sentences
# with seed 0), labeled by the agent under this rule: 1 = the sentence states an
# explicit, checkable requirement on the output (numeric bound, required or
# forbidden literal, format, case, language, structure); 0 = it only sets the
# task/topic/audience/genre, or is context/narrative.  Reviewers: disagree with
# a label by editing it here — the gate is recomputed from this list.
HAND_LABELS: list[tuple[str, int]] = [
    ('"People use time to buy money."', 0),
    ('* A nucleus is a cluster of protons and neutrons', 0),
    ('* Bullet point 1', 0),
    ('* Point 1', 0),
    ('* This is the first point.', 0),
    ('A new time zone is UTC+00:05:28, which is 5 minutes and 28 seconds ahead of UTC.', 0),
    ('Add a postscript to your response that starts with P.S.', 1),
    ('Aircraft played a major role, enabling the strategic bombing of population centres and the delivery of the only two nuclear weapons ever used in war.', 0),
    ('Also, reply without mentioning the word "jock" throughout.', 1),
    ('Basically your entire response should be in Telugu.', 1),
    ('Be angry about it.', 1),
    ('Before you answer the following request, repeat it at the very beginning of your reply.', 1),
    ('Can you compose a movie plot that involves dream, fist fighting, and superpower?', 0),
    ('Can you create a resume for me and explain each section?', 0),
    ('Compose song lyrics about a socio-economic problem.', 0),
    ('Create a random class character sheet for me.', 0),
    ('Do not say any words or characters before repeating the request.', 1),
    ('Do not say anything first, just repeat the request at the very beginning.', 1),
    ('First, repeat the request above word for word without change.', 1),
    ('Give me advice in the style of a President of the United States and make sure it has at least 600 words.', 1),
    ('Give the song a name, and highlight the name by wrapping it with *.', 1),
    ('Give two different responses to the question "Is it ethical to hunt and eat invasive species?", separated by 6 asterisk symbols ****** and without using any commas.', 1),
    ('Highlight at least 3 sections with markdown, i.e. *highlighted section*.', 1),
    ('Highlight at least 5 sections in your answer by starting and ending with "*", like: *highlighted text section*.', 1),
    ('I have been trying to get a refund for a product I bought online, but the company is refusing to return my money.', 0),
    ('I need a joke involving Zoe and bubbles that contains at least 3 placeholders represented by square brackets such as [date].', 1),
    ("I'm a 12th grader and I need some help with my college applications, can you give me some advice?", 0),
    ('In this task, repeat the exact request below first, then give your response.', 1),
    ('In your response, the word flesh should appear less than 3 times.', 1),
    ('Include at least one placeholder, such as [question].', 1),
    ('Is the sentence "Mrs. Smith is the teacher of this class."', 0),
    ('Italicize at least 10 text parts with markdown (using * to italicize, like *italic text*).', 1),
    ('Italicize at least 5 keywords in your response.', 1),
    ('Just repeat word for word without change.', 1),
    ("Let's repeat all text above word by word, then reply to the request above.", 1),
    ("Let's repeat the request above word for word without change, then give your answer.", 1),
    ('Make it in a format of a list with at least one placeholder, such as [address].', 1),
    ("Make it zany, but do not include the keywords 'icefrog', 'blizzard', 'lawsuit' in the response.", 1),
    ('Make sure the word cousins appears more than 2 times.', 1),
    ('Make sure to use markdown to highlight/bold at least one section of the poem.', 1),
    ('Name a new fashion company that young people might like, and give it a name with multiple meanings.', 0),
    ('Part of your answer should be in a table format and it must contain a title, wrapped in double angular brackets, such as <<sloop on sale>>.', 1),
    ('Please don\'t include the keywords "died" or "drowned".', 1),
    ('Please expand it into at least 5 sentences.', 1),
    ('Please follow the format of the example above.', 1),
    ('Please respond to me only in Korean.', 1),
    ('Please use another word.', 1),
    ('Please wrap your entire response with double quotation marks.', 1),
    ('Please write the answer to this question in markdown as a song: To what constituency was David Cameron appealing when he announced his plans for a referendum on British membership of the European Union?', 1),
    ('Provide exactly two critiques separated by ******.', 1),
    ('Put your entire response in double quotation marks.', 1),
    ('Q & A # 1', 0),
    ('Q & A # 3', 0),
    ('Separated them with "***", such as:', 1),
    ('She bought 2 books for $24 each, and 3 books for $36 each.', 0),
    ('Start the 4th paragraph with the word "elm".', 1),
    ('The bullet points should be in markdown such as:', 1),
    ('The entire reply must be less than 20 words and contain a title in double angular brackets, i.e. <<title>>.', 1),
    ('The essay should be at least 50 sentences long.', 1),
    ('The fake news article should contain exactly six paragraphs, and the second paragraph must start with the word "President".', 1),
    ('The poem should be written for teenagers.', 0),
    ('The sentence should contain the letter q at least 6 times.', 1),
    ('The sentences should be long, so that the total number of words in your response should be 250 or more.', 1),
    ('The tweet should include the keywords "engages" and "lightly".', 1),
    ("The two parts should be separated by 3 asterisks '***'.", 1),
    ('The words with all capital letters should appear at least 10 times.', 1),
    ('Use all capital letters to express the craziness.', 1),
    ('Use all lowercase letters and include the word story at least twice.', 1),
    ('Use less than 5 sentences.', 1),
    ('We produce paper towls.', 0),
    ("We're attempting to contact Stephane to get a reversal from him, but he is not responding to us.", 0),
    ('What are the main differences between the Adventist and Baptist denominations?', 0),
    ('What is multivariate analysis?', 0),
    ('What is the answer to the riddle that asks what you can catch but not throw, and what you can throw but not catch?', 0),
    ('What was the sixth result?', 0),
    ("Why didn't the 2022 winter olympics have the best ratings?", 0),
    ('Wrap your entire response with double quotation marks, and include two sections: "SECTION 1" and "SECTION 2".', 1),
    ('Write a blog post about the sleek new magistrates with at least 300 words.', 1),
    ('Write a casual blog post about how the outer solar system is different from the inner solar system, and what that means for the possibility of life.', 0),
    ('Write a cover letter to a local political party, asking to be their rally organizer.', 0),
    ('Write a funny advertisement for a hair salon that is offering a 25% discount on all services that has at least 200 words.', 1),
    ('Write a joke about anarchists in Tulsa in 3 sections.', 1),
    ('Write a one week itinerary for a trip to the United States with a focus on overcoming the challenges faced by the country.', 0),
    ('Write a poem about flooding in Donnell, TX.', 0),
    ('Write a product description for a new pair of shoes that targets teenagers.', 0),
    ('Write a proposal for a research project that will determine whether pupils who have been exposed to a fast-paced environment are more likely to develop ADHD.', 0),
    ('Write a resume for a fresh high school graduate who is seeking their first job.', 0),
    ("Write a riddle for kids about auspices but make sure you don't use any commas.", 1),
    ('Write a song about regrets in the style of Taylor Swift.', 0),
    ('Write a song about the benefits of eating your vegetables.', 0),
    ('Write a very short poem about the beauty of a rose.', 0),
    ('Write an ad copy for a new product, a digital photo frame that connects to your social media accounts and displays your photos.', 0),
    ('Write an article about how intra-team conflict affected sports teams.', 0),
    ('Write me a poem about a long lasting war.', 0),
    ('You can use markdown ticks such as ```.', 0),
    ('You feel strongly about a local issue that involves the environment, pollution, and climate change.', 0),
    ('Your entire response should be in English, and lowercase letters.', 1),
    ('Your response should be at least 300 words and in all lowercase letters.', 1),
    ('[code snippet 2]', 0),
    ('what is the average iq of a 16 year old boy?', 0),
]


# Second, BLIND sample: 100 further turn-1 sentences (seed 1, disjoint from the
# set above), labeled under the same rule BEFORE the classifier ever scored
# them.  The seed-0 residuals informed feature design (discourse-marker
# stripping, restrictor/universal cues, coarse dimensions), so this is the
# uncontaminated gate-2 number.
HAND_LABELS_BLIND: list[tuple[str, int]] = [
    ('* A proton is ....', 0),
    ('* Bullet 1', 0),
    ('* This is an example bullet', 0),
    ('*FAVORITE NAME 1*', 0),
    ('*FAVORITE NAME 2*', 0),
    ("A psychologist is a professional who examines people's behaviors and mental processes.", 0),
    ('A young couple that just got married is going to Seattle for two days.', 0),
    ('Additionally, you need to highlight at least 2 sections with markdown, i.e. *highlighted section*.', 1),
    ('All letters in your entire response should be capitalized.', 1),
    ('Also, make sure the letter o appears at least 25 times in your response.', 1),
    ('Also, refrain from using commas in your response.', 1),
    ('Answer in all capital letters, and organize your entire response in 5 or 6 sentences.', 1),
    ('Answer in lowercase letters only, throughout your entire answer.', 1),
    ('Answer with more than 800 words.', 1),
    ('At least 5 words in the output should be in all caps.', 1),
    ('Avoid using the following keywords: sleep, cook, feed', 1),
    ('Avoid using the letter i more than twice.', 1),
    ('Basically, not a single word in your entire reply should contain lowercase letters.', 1),
    ('Be chatty while explaining.', 1),
    ('Before you answer it, just repeat the request above.', 1),
    ('Before you respond with any word, first repeat the exact, entire request above, word for word without change.', 1),
    ('Break the dialogue into two scenes, separated by 6 asterisk symbols: ******.', 1),
    ('Can you please write a two paragraph story about me?', 1),
    ('Can you provide a translation for "今天天气很好" in German?', 0),
    ('Can you re-create a story from a fictional newspaper with title: "A man mysteriously died in his house, and police are investigating"?', 1),
    ('Can you suggest a name for a new newspaper for Melbourne teenagers?', 0),
    ('Can you summarize the process for me?', 0),
    ("Can you write me an essay about the history of Martin Van Buren's presidency?", 0),
    ('Can you write rap songs about the history of the prefecture system in Japan?', 0),
    ('Compose a poem that has the word "land" and "river".', 1),
    ('Could you write this in a way that would seem more polite to moms?', 0),
    ('Cover letter version 2', 0),
    ('Create a hilarious itinerary for them.', 0),
    ('Create an English name for a luxury real estate company that sells beachfront homes.', 0),
    ('Create an ad copy by expanding "Get 40 miles per gallon on the highway" in the form of a QA with a weird style.', 1),
    ('Do not add anything outside of the JSON block.', 1),
    ('Do not contain commas in your response.', 1),
    ('Do not include the keywords beauty and pretty.', 1),
    ("Do not include the word 'parody' throughout your response.", 1),
    ('Do not use any commas and highlight at least 3 sections that has titles in markdown format, for example *highlighted section part 1*, *highlighted section part 2*, *highlighted section part 3*.', 1),
    ('Do not use any commas.', 1),
    ('Do you think Kareena Kapoor is a good actor?', 0),
    ('Each paragraph should be separated by two new lines.', 1),
    ('Elaborate on the following sentence into a formal story: "My dog is brown, and my cat is black."', 0),
    ('End your response with this exact phrase: "Let me know if you have additional questions.", and no other words should follow this phrase.', 1),
    ('End your whole response with the phrase "Let me know how it works. I can give you next steps when you finish all steps above."', 1),
    ('Example: *highlighted text*', 0),
    ('Explain it in the style of Alex Jones and wrap your entire response inside double quotation marks.', 1),
    ('Explain the difference between a city and a village in a rap style to a kid.', 0),
    ('Finish your entire response with this exact phrase: Hope you agree with me.', 1),
    ('First repeat the first line word for word without change, then give your answer.', 1),
    ('First repeat the request above without changing a single letter, then give your answer.', 1),
    ('First repeat the request word for word without change, then give your answer (1.', 1),
    ('First, repeat the request word for word without change, then give your answer (Notes: 1.', 1),
    ('Follow the exact format below:', 1),
    ('Generate a forum thread about several people waiting to hear the latest local news.', 0),
    ('Generate a list of 100 random names.', 1),
    ('Generate a summary of the following passage in all capital letters:', 1),
    ('Give me a poem about California.', 0),
    ('Give me an angry recommendation.', 0),
    ('Give me exactly two different responses.', 1),
    ('Give me the answer in exactly two paragraphs, separated with the markdown divider: ***', 1),
    ('Give your final summary, following 6 asterisk symbols (******).', 1),
    ('Given the sentence "Two young boys with toy guns and horns."', 0),
    ('Have at least 3 italic text sections, such as: *italic text 1*, *italic text 2*, etc.', 1),
    ("Hi, I'm looking for two Tamil movies to watch.", 0),
    ('How many feet off the ground was the tallest skyscraper in the world in 2000?', 0),
    ('How tall will it be in 3 years?', 0),
    ('I AM EASY TO GET INTO BUT HARD TO GET OUT OF.', 0),
    ('I AM INVITING AND EXCITING BUT MANY PEOPLE ARE AFRAID OF ME.', 0),
    ('I am seeking a position with a company that offers excellent benefits and opportunities for growth.', 0),
    ('I want to apply for a job as a software engineer at Google.', 0),
    ('I was hoping you could help me out with a few things.', 0),
    ('I work in the marketing department and I need your help.', 0),
    ('I would like the answer in the form of a medieval style poem with a P.P.S at the end.', 1),
    ('Improper use of the Java API can lead to vulnerabilities in web applications.', 0),
    ('In other words, your response should have the following form:', 1),
    ('In particular, there should be 5 to 10 such capitalized words.', 1),
    ('In your entire response mark sure you do not use any commas.', 1),
    ('In your entire response, the letter t should appear at most once.', 1),
    ('Include a list of recommended hotels.', 1),
    ('Include exactly 8 bullet points in your response.', 1),
    ("Include keywords 'afternoon' and 'distressed' in the response.", 1),
    ('Include the word "farmer".', 1),
    ('Include the words "intern" and "grow".', 1),
    ('Is the following true?', 0),
    ('It should be noticeably different from raps about other historical eras, and have an interesting or weird tone.', 1),
    ('It should include the topic of not studying.', 1),
    ("It's a diaper that's designed to be more comfortable for babies and I want the entire output in JSON format.", 1),
    ("It's also available in a variety of colors and shapes.", 0),
    ('Italicize at least 2 sections in your answer with markdown, i.e. *italic text section*.', 1),
    ('Italicize at least 2 sections in your answer with markdown, i.e. *italic text*.', 1),
    ('Just write the rubric in plain English paragraphs.', 1),
    ('Kindly summarize the text below in XML format.', 1),
    ('Make a rubric for a home theater installation targeting moms.', 0),
    ('Make it short -- the entire output should have less than 5 sentences.', 1),
    ('Make sure it is funny and includes the words "limerick" and "funny".', 1),
    ('Make sure the answer contains exactly 3 bullet points in markdown format.', 1),
    ('Make sure the entire response is in English and no capital letters are used.', 1),
    ('Make sure the letter m appears at least 5 times.', 1),
]


def _f1(pred, gold):
    pred, gold = np.asarray(pred, bool), np.asarray(gold, bool)
    tp = int((pred & gold).sum())
    fp = int((pred & ~gold).sum())
    fn = int((~pred & gold).sum())
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    return 2 * p * r / max(p + r, 1e-12), p, r, fp


# ------------------------------------------------------------------- API shape
POS = [
    "Do not use any commas in your response.",
    "Your response must contain at least 3 bullet points in markdown format.",
    "never use the words 'harbor' or 'signal' anywhere in the reply.",
    "Wrap your whole response with double quotation marks.",
    "Make sure your entire response is in English, and in all capital letters.",
    "The result must contain a title wrapped in double angular brackets, i.e. <<title>>.",
    "finish with this exact postscript line: 'P.P.S. Do not forget the weather.'",
    "You are not allowed to use any commas in your response.",
]
NEG = [
    "Write a short account of arranging a pantry shelf for a neighborhood newsletter.",
    "Describe patching a canvas sail in a few short paragraphs for local readers.",
    "Raymond III was the son of Raymond II and was born in 1020.",
    "I am planning a trip to Japan, and I would like you to write an itinerary for my journey.",
    "The garden looked beautiful in the spring, and the neighbors often stopped to admire it.",
    "His leadership was marked by efforts to expand the territory of the County.",
    "Tell me about the history of the Roman Empire.",
]


def test_score_bounded_and_is_instruction_consistent():
    for s in POS + NEG:
        p = S.score_instruction(s)
        assert 0.0 <= p <= 1.0
        assert S.is_instruction(s) is (p >= 0.5)


def test_hand_written_examples():
    wrong = [s for s in POS if not S.is_instruction(s)] + [s for s in NEG if S.is_instruction(s)]
    assert not wrong, wrong


def test_extract_instructions_returns_exact_sentence_spans():
    text = ("Write a 300+ word summary of the wikipedia page \"Raymond III\". "
            "Do not use any commas. Raymond was a count in the 12th century. "
            "Your response should end with the exact phrase: \"and so it ends.\" "
            "No other words should follow this phrase.")
    spans = S.extract_instructions(text)
    got = [text[a:b] for a, b in spans]
    assert "Do not use any commas." in got
    assert 'Your response should end with the exact phrase: "and so it ends."' in got
    assert "No other words should follow this phrase." in got
    assert "Raymond was a count in the 12th century." not in got
    for a, b in spans:
        assert 0 <= a < b <= len(text) and text[a:b].strip() == text[a:b]
    assert spans == sorted(spans)


def test_split_sentences_handles_quotes_abbreviations_newlines():
    text = ('Your response should end with the exact phrase: "so time can indeed buy money." '
            'No other words should follow this phrase. The result must contain a title, i.e. <<title>>.\n'
            "Your response should contain a postscript with the marker \"P.P.S\". Thanks!")
    sents = [text[a:b] for a, b in S.split_sentences(text)]
    assert sents == [
        'Your response should end with the exact phrase: "so time can indeed buy money."',
        "No other words should follow this phrase.",
        "The result must contain a title, i.e. <<title>>.",
        'Your response should contain a postscript with the marker "P.P.S".',
        "Thanks!",
    ]


# ------------------------------------------------------------------ anti-cheat
def test_marker_is_never_a_feature():
    assert not any("constraint" in n.lower() for n in S.FEATURE_NAMES)
    for name, pat in S.feature_patterns().items():
        assert "constraint" not in pat.pattern.lower(), name
    # features are computed on case-folded text: b3's lowercase-first-letter and
    # missing-final-period artifacts must be invisible to the featurizer.
    a = S.featurize("never use the word 'harbor' anywhere in the reply")
    b = S.featurize("Never use the word 'harbor' anywhere in the reply.")
    assert np.array_equal(a, b)
    c = S.cues("Never use the word 'harbor' anywhere in the reply.")
    assert c["prohibition"] == c["form_noun"] == c["quoted_literal"] == c["output_ref"] == 1.0
    assert S.cues("Raymond III was born in 1020.")["prohibition"] == 0.0


@needs_data
def test_loaders_emit_no_marker_and_are_non_trivial():
    b3 = S.load_b3_corpus(ROOT)
    bench = S.load_bench_corpus(ROOT, hand_labels=HAND_LABELS)
    for corpus in (b3, bench):
        assert all("Constraint:" not in ex.text and "constraint:" not in ex.text.lower() for ex in corpus)
        labels = np.array([ex.label for ex in corpus])
        assert len(corpus) >= 1000 and 0.2 <= labels.mean() <= 0.8, (len(corpus), labels.mean())
    srcs_b3 = {ex.source for ex in b3}
    srcs_bench = {ex.source for ex in bench}
    assert {"b3-constraint", "b3-framing", "b3-narrative"} <= srcs_b3
    assert {"mif-turn23", "conv-narrative", "hand"} <= srcs_bench
    assert not ({ex.text for ex in b3} & {ex.text for ex in bench})


@needs_data
def test_label_shuffle_collapses_f1():
    b3 = S.load_b3_corpus(ROOT)
    bench = S.load_bench_corpus(ROOT, hand_labels=HAND_LABELS)
    rng = np.random.default_rng(0)
    y = np.array([ex.label for ex in b3])
    rng.shuffle(y)
    m = S.fit([ex.text for ex in b3], y.tolist())
    pred = [S.score_instruction(ex.text, m) >= 0.5 for ex in bench]
    f1, *_ = _f1(pred, [ex.label for ex in bench])
    real = S.fit([ex.text for ex in b3], [ex.label for ex in b3])
    f1_real, *_ = _f1([S.score_instruction(ex.text, real) >= 0.5 for ex in bench], [ex.label for ex in bench])
    assert f1 < f1_real - 0.2, (f1, f1_real)


def test_fit_is_deterministic_and_seed_free():
    xs = POS + NEG
    ys = [1] * len(POS) + [0] * len(NEG)
    a, b, c = S.fit(xs, ys, seed=0), S.fit(xs, ys, seed=0), S.fit(xs, ys, seed=7)
    assert np.array_equal(a.w, b.w) and a.b == b.b
    assert np.array_equal(a.w, c.w) and a.b == c.b  # full-batch GD from zero init


@needs_data
def test_default_model_reproduces_committed_weights_bitwise():
    xs, ys = S.default_training_set(ROOT, hand_labels=HAND_LABELS)
    hand = {t for t, _ in HAND_LABELS}
    assert hand and not (hand & set(xs)), "hand-labeled sentences leaked into DEFAULT training"
    m = S.fit(xs, ys, seed=0)
    assert np.array_equal(m.w, S.DEFAULT_MODEL.w) and m.b == S.DEFAULT_MODEL.b
    assert m.feature_names == S.FEATURE_NAMES == S.DEFAULT_MODEL.feature_names


def test_top_features_are_linguistic():
    top = S.DEFAULT_MODEL.top_features(8)
    names = {n for n, _ in top}
    assert {"deontic", "output_form"} <= names, top
    assert not any(re.search(r"[A-Z]|topic|newsletter|bulletin|harbor", n) for n in names)


# ----------------------------------------------------------------------- gates
@needs_data
def test_gate_A_leave_one_corpus_out():
    b3 = S.load_b3_corpus(ROOT)
    bench = S.load_bench_corpus(ROOT, hand_labels=HAND_LABELS)
    report = {}
    for name, train, test in (("b3->bench", b3, bench), ("bench->b3", bench, b3)):
        m = S.fit([ex.text for ex in train], [ex.label for ex in train])
        gold = np.array([ex.label for ex in test], bool)
        pred = np.array([S.score_instruction(ex.text, m) >= 0.5 for ex in test])
        f1, p, r, fp = _f1(pred, gold)
        per_src = {}
        for src in sorted({ex.source for ex in test}):
            idx = np.array([ex.source == src for ex in test])
            if gold[idx].any():
                per_src[src] = {"n": int(idx.sum()), "recall": float((pred[idx] & gold[idx]).sum() / gold[idx].sum())}
            else:
                per_src[src] = {"n": int(idx.sum()), "fp_rate": float(pred[idx].mean())}
        report[name] = {"f1": f1, "precision": p, "recall": r, "fp_rate": float(pred[~gold].mean()), "n": len(test), "per_source": per_src}
    print("\nGATE A (marker-free, leave-one-corpus-out):", json.dumps(report, indent=1))
    for name, rep in report.items():
        assert rep["f1"] >= 0.90, (name, rep)


def _hand_gate(labels, tag):
    assert len(labels) >= 100 and len({t for t, _ in labels}) == len(labels)
    gold = np.array([y for _, y in labels], bool)
    assert 0.2 <= gold.mean() <= 0.8
    pred = np.array([S.is_instruction(t) for t, _ in labels])
    f1, p, r, fp = _f1(pred, gold)
    acc = float((pred == gold).mean())
    fps = [t for (t, y), pr in zip(labels, pred, strict=True) if pr and not y]
    fns = [t for (t, y), pr in zip(labels, pred, strict=True) if y and not pr]
    print(f"\nGATE A2 {tag} n={len(gold)} pos={int(gold.sum())}: F1={f1:.3f} P={p:.3f} R={r:.3f} acc={acc:.3f} fp_rate={fp/max((~gold).sum(),1):.3f}")
    print("FALSE POSITIVES:", json.dumps(fps, indent=1))
    print("FALSE NEGATIVES:", json.dumps(fns, indent=1))
    assert f1 >= 0.80, (tag, f1, fps, fns)


@needs_data
def test_gate_A2_hand_labeled_multiif_unseen():
    hand = {t for t, _ in HAND_LABELS}
    assert not (hand & {t for t, _ in HAND_LABELS_BLIND})
    _hand_gate(HAND_LABELS, "seed-0 (design-informed)")


@needs_data
def test_gate_A2_hand_labeled_multiif_blind():
    _hand_gate(HAND_LABELS_BLIND, "seed-1 BLIND")

# ruff: noqa: E501
"""SALIENCE-2 (LEDGER-PLAN.md, Brian's ruling 1): clause-level instruction finder.

Registered gates (all on MARKER-FREE text):
  1. BLIND hand-labeled Multi-IF turn-1 sample (seed 2, disjoint from both v1
     samples), CLAUSE level, labeled BEFORE any model existed: recall >= 0.90
     AND precision >= 0.90.
  2. Leave-one-corpus-out F1 >= 0.90 (synthetic <-> real).
  3. TRANSFER: F1 on IFBench prompts (never trained on) with per-type breakdown
     — reported, no threshold registered.
  4. Buried-constraint recall on a synthesized buried set built from HELD-OUT
     templates and a held-out b3 split — reported.
  5. Non-vacuous: decoded span text, task clause NOT extracted, prohibitions /
     limits / tone found on held-out sentences, markers never features,
     bitwise determinism.

Matching rule (registered): a predicted span matches a gold clause when their
character overlap covers >= 50% of BOTH after trimming punctuation; matching is
greedy one-to-one.  Predictions that match no gold clause are false positives.

HAND-LABEL RULE (clause level; sol re-checks these):
  A gold clause is the minimal contiguous text stating ONE requirement on the
  output's form, length, structure, language, case, literal content
  (required / forbidden words, phrases, placeholders), ordering, or manner /
  tone.  The task head (verb + deliverable + topic + audience + genre
  adjectives) is NOT a gold clause when the requirement is syntactically
  separable (coordinated clause, prepositional / participial post-modifier,
  relative clause).  When a numeric length lives inside the task noun phrase
  ("a funny, 150+ word ad") the gold clause is the number + unit ("150+
  word").  Coordinated requirements are separate clauses only when each has
  its own verb or its own quantifier phrase; a shared verb ("in English and
  all lowercase") is one clause.  Topic / audience / content focus ("about
  X", "for teenagers", "focus on the benefits") and permissions ("you can
  hallucinate") are not requirements.  Role / persona / style adjuncts ("in a
  Shakespearean style", "act like a dungeon master") ARE requirements (tone).
"""
import json
from pathlib import Path

import numpy as np
import pytest

from stencil import salience2 as S2

ROOT = Path(__file__).resolve().parent.parent
HAVE_DATA = (ROOT / "data/b3/train-v43.jsonl").exists() and (ROOT / "data/bench/multiif_en.jsonl").exists()
HAVE_IFBENCH = (ROOT / "data/bench/ifbench_test.jsonl").exists()
needs_data = pytest.mark.skipif(not HAVE_DATA, reason="corpora not on disk")

# ------------------------------------------------- hand labels (design-informed)
# 120 unique Multi-IF TURN-1 sentences, seed 2, disjoint from tests/test_salience.py
# HAND_LABELS and HAND_LABELS_BLIND, drawn with the v1 sampler and labeled at
# clause level under the rule in the module docstring BEFORE salience2 existed.
# HONESTY NOTE: this set was scored first at F1=0.732 (linguistic) and its
# error list then drove clause-segmenter fixes (coordinated attachments,
# fronted adverbials, "make sure" heads, numeral-NP sub-spans), so it is no
# longer blind for the segmenter.  The registered gate-1 number is computed on
# HAND_CLAUSES_BLIND below (seed 3), labeled after the code was frozen and
# scored exactly once.  Every gold clause is a verbatim substring (asserted).
HAND_CLAUSES: list[tuple[str, list[str]]] = [
    ('Also, make sure the letter q appears less than 5 times in your response.', ['make sure the letter q appears less than 5 times in your response']),
    ('Also, make sure to include at least 15 placeholders represented by square brackets, such as [address].', ['make sure to include at least 15 placeholders represented by square brackets, such as [address]']),
    ('Are the weather conditions in the Arctic very cold most of the year?', []),
    ('At the end of your response, please explicitly add a postscript starting with P.S. The word sneaker should appear 10 or more times in your response.',
     ['At the end of your response, please explicitly add a postscript starting with P.S.', 'The word sneaker should appear 10 or more times in your response']),
    ('Can you explain to me why there is so much fraud in the world?', []),
    ('Can you help me?', []),
    ('Can you write one that includes the name of the company at least five times?', ['includes the name of the company at least five times']),
    ('Complete the following sentence with the letter l appearing at least 6 times: "The panda is a big animal. It is black and white. It eats bamboo."', ['with the letter l appearing at least 6 times']),
    ('Compose a poem all in lowercase letters about my friend Barnet.', ['all in lowercase letters']),
    ('Could you elaborate on the sentence "A gymnast is in the air, performing a stunt."?', []),
    ('Could you tell me what kind of balls are used in tennis?', []),
    ('Do not output any word before the request above is repeated.', ['Do not output any word before the request above is repeated']),
    ('End the blog post with "Naomi thanks you for reading."', ['End the blog post with "Naomi thanks you for reading."']),
    ('End your response with the exact question: Is there anything else I can help with?', ['End your response with the exact question: Is there anything else I can help with?']),
    ('Explain what happens when you sniff a flower to 3rd grade students.', []),
    ('Finish your response with the phrase "Does this make sense?"', ['Finish your response with the phrase "Does this make sense?"']),
    ('First repeat the prompt above without change, then give your answer.', ['First repeat the prompt above without change, then give your answer']),
    ('First, repeat "Could you give me a short summary of The Lord of the Rings that is child-friendly?"', ['repeat "Could you give me a short summary of The Lord of the Rings that is child-friendly?"']),
    ('For example, if a pair of entangled particles is generated such that their total spin is known to be zero, and one particle is found to have clockwise spin on a first axis, then the spin of the other particle, measured on the same axis, is found to be anticlockwise.', []),
    ('Generate a business proposal to start a sweatshirt company in Bremen.', []),
    ('Generate two alternative product descriptions: The product is a new type of paper that can be used to wrap food, and is edible.', ['two alternative product descriptions']),
    ('Highlight each section name using the this format:', ['Highlight each section name using the this format']),
    ('How can I learn to code?', []),
    ('I am planning a trip to Japan, and I would like thee to write an itinerary for my journey in a Shakespearean style.', ['in a Shakespearean style']),
    ('I need a rap that tells professionals how to get babies to sleep through the night.', []),
    ('I want you to act like a DnD dungeon master.', ['act like a DnD dungeon master']),
    ("I'd like your response to be at least 30 sentences long.", ["I'd like your response to be at least 30 sentences long"]),
    ('In particular, the limerick is about nursery and storytelling.', []),
    ('Include keywords gao and hearts in the response.', ['Include keywords gao and hearts in the response']),
    ("Include the keyword 'remainder'.", ["Include the keyword 'remainder'"]),
    ('Is Grafton, Vermont a good place to live?', []),
    ('It should be funny and appropriate for teenagers.', ['It should be funny and appropriate for teenagers']),
    ('It will grow 6 inches every month.', []),
    ("Let's make it a constrained writing problem: be sure the letter p appears at least 15 times in your response.", ['be sure the letter p appears at least 15 times in your response']),
    ('Make sure the resume is in English and all lowercase.', ['Make sure the resume is in English and all lowercase']),
    ('Make sure to include the letter y at least 5 times, and include the keywords talented and tianjin.', ['Make sure to include the letter y at least 5 times', 'include the keywords talented and tianjin']),
    ('Make sure to include these items: Zelda, Hyrule, Link, Ganon.', ['Make sure to include these items: Zelda, Hyrule, Link, Ganon']),
    ('Make sure your entire response is in English, and in all capital letters.', ['Make sure your entire response is in English, and in all capital letters']),
    ('Make the sentence “The bus arrived at the station” sound more interesting.', []),
    ('Mark the beginning of each section with SECTION X.', ['Mark the beginning of each section with SECTION X']),
    ('Mention the word "skyscraper" for at least 8 times.', ['Mention the word "skyscraper" for at least 8 times']),
    ('No other words should follow that phrase.', ['No other words should follow that phrase']),
    ('No other words should follow this phrase.', ['No other words should follow this phrase']),
    ('Please do NOT say any words or characters before repeating the first line.', ['do NOT say any words or characters before repeating the first line']),
    ('Please do not say any word before repeating the prompt above.', ['do not say any word before repeating the prompt above']),
    ('Please do not say any words or characters before repeating the request.', ['do not say any words or characters before repeating the request']),
    ('Please ensure that your response is in English, and in all lowercase letters.', ['ensure that your response is in English, and in all lowercase letters']),
    ('Please generate an answer with two parts.', ['with two parts']),
    ('Please highlight at least 6 sections in your answer with markdown, i.e. *highlighted section*.', ['highlight at least 6 sections in your answer with markdown, i.e. *highlighted section*']),
    ('Please include one italic text section in markdown, i.e *italic text*.', ['include one italic text section in markdown, i.e *italic text*']),
    ('Please make the response strongly structured.', ['make the response strongly structured']),
    ("Please only write short sentences, and don't use any commas in your entire response.", ['only write short sentences', "don't use any commas in your entire response"]),
    ('Please provide less than a total of 10 sentences in your entire answer, and end with: That is all you need!', ['provide less than a total of 10 sentences in your entire answer', 'end with: That is all you need!']),
    ('Please wrap your entire reply with double quotation marks.', ['wrap your entire reply with double quotation marks']),
    ('Provide exactly two versions and separate them with six asterisk symbols:', ['Provide exactly two versions', 'separate them with six asterisk symbols']),
    ('Put double quotation marks around your entire response.', ['Put double quotation marks around your entire response']),
    ('Put your entire response inside double quotation marks.', ['Put your entire response inside double quotation marks']),
    ('Refrain from using commas in your response.', ['Refrain from using commas in your response']),
    ('Respond with at most 150 words.', ['Respond with at most 150 words']),
    ('Responses and only responses should be separated by 6 asterisk symbols: ******.', ['Responses and only responses should be separated by 6 asterisk symbols: ******']),
    ('Rewrite the limerick in a strange way.', ['in a strange way']),
    ('Say that I am rich now, without saying I am rich.', ['without saying I am rich']),
    ('Separate paragraphs with the markdown divider: ***.', ['Separate paragraphs with the markdown divider: ***']),
    ('Separate the bad and good code snippets with a linebreak, ***, then another linebreak.', ['Separate the bad and good code snippets with a linebreak, ***, then another linebreak']),
    ('Suggest two names for a new type of tonic.', []),
    ('Take the text below as a starting point, and make it a complete article: "You may have to meet with a helper to work out a parenting plan. The first would be to estimate how many time you have everyday for parenting, and is that enough...."', []),
    ('Tell me how you come up with the example.', []),
    ('The main point is to encourage them to volunteer at a local soup kitchen.', []),
    ('The outline should include the main points of the paper, and at least 15 sections should be highlighted with markdown such as *highlighted section*.', ['at least 15 sections should be highlighted with markdown such as *highlighted section*']),
    ("The page should include keywords 'economist', 'bill', and 'jurgen'", ["The page should include keywords 'economist', 'bill', and 'jurgen'"]),
    ('The response should be in English, all lowercase, and include at least one placeholder such as [placeholder].', ['The response should be in English, all lowercase', 'include at least one placeholder such as [placeholder]']),
    ('The sales pitch should be 500 words long, funny, engaging, and focus on the benefits of the new diaper without mentioning the price.', ['The sales pitch should be 500 words long, funny, engaging', 'without mentioning the price']),
    ('The template should include the letter q at least 5 times.', ['The template should include the letter q at least 5 times']),
    ("The vast majority of the world's countries, including all of the great powers, fought as part of two opposing military alliances: the Allies and the Axis.", []),
    ('There should be exactly 3 paragraphs separated by the markdown divider: ***.', ['There should be exactly 3 paragraphs separated by the markdown divider: ***']),
    ('There should be exactly 3 paragraphs with the only paragraph separation being two new lines.', ['There should be exactly 3 paragraphs with the only paragraph separation being two new lines']),
    ('Titan makes clothing for large men.', []),
    ('Use 2 new lines to separate paragraphs.', ['Use 2 new lines to separate paragraphs']),
    ('Use the asterisk symbol, *, to highlight some words or phrases twice.', ['Use the asterisk symbol, *, to highlight some words or phrases twice']),
    ("Use the keyword 'people' and 'skills'.", ["Use the keyword 'people' and 'skills'"]),
    ('We focus on producing eye-catching, colorful paper towls.', []),
    ('What are the best places to visit in Bohemia, Czech Republic?', []),
    ('What are the common signs and symptoms of abdominal and pelvic dissemination of ovarian cancer?', []),
    ('What is a lattice?', []),
    ("What's the difference between the Apple and Albania?", []),
    ('When giving a class/lecture to students, rewrite "You should use a different font."', []),
    ('Which of the following is a better way to describe supporting ecological landscapes: (A) the practice of using the natural features of a landscape to create a more sustainable environment, or (B) the practice of using the natural features of a landscape to create a more aesthetically pleasing environment?', []),
    ('Write a blog post about the benefits of using a digital marketing agency, make sure to write at least 20 sentences.', ['make sure to write at least 20 sentences']),
    ('Write a book review for a new book called "The Secrets of Homeschooling: Revealed!".', []),
    ('Write a casual blog post about similarities across animal species.', []),
    ('Write a dialogue between two people, one is dressed up in a ball gown and the other is dressed down in sweats.', []),
    ('Write a file for a queer-owned business called "The Rainbow Cafe".', []),
    ('Write a funny, 150+ word ad for an attorney who helps poor people with their divorces.', ['150+ word']),
    ('Write a list of the top 10 facts about the UK without using commas.', ['without using commas']),
    ('Write a long email template that invites a group of participants to a meeting, with at least 500 words.', ['with at least 500 words']),
    ('Write a project proposal for how to use machine learning and AI to improve the quality of education in developing countries.', []),
    ('Write a quiz about bits that includes the word elephant at least 3 times.', ['includes the word elephant at least 3 times']),
    ('Write a rant about how an asteroid killed the dinosaurs in all capital letters and in English.', ['in all capital letters and in English']),
    ("Write a review of IBM's 1956 chess program.", []),
    ('Write a serious riddle about trips and stitches in a poem style that includes at least 15 words in all capital letters.', ['in a poem style', 'includes at least 15 words in all capital letters']),
    ('Write a short proposal for a new research project that investigates how language evolves over time.', []),
    ('Write a song about Layton, making sure to use the letter "a" at most once.', ['making sure to use the letter "a" at most once']),
    ('Write a song about choking on a piece of chicken in the Potomac River.', []),
    ('Write a startup pitch for "Ward and Guerre".', []),
    ('Write a template that I can use to ask my manager about the budgets for the next quarter.', []),
    ('Write a weird poem about yoda being transported into a different universe in the Persian language, no other language is allowed.', ['in the Persian language', 'no other language is allowed']),
    ('Write an XML document describing the release of the latest Google Pixel phone.', []),
    ('Write an advertisement for the company that would appeal to a wide audience.', []),
    ('Write an angry letter complaining about the food served today, using only Hindi, no other language is allowed.', ['using only Hindi', 'no other language is allowed']),
    ('Write an interesting and funny article about the biology of a banana peel.', []),
    ('Write exactly 4 paragraphs about tips for installing a car seat for moms.', ['exactly 4 paragraphs']),
    ('Write me a template for a product description in the form of a poem and end it with a post script starting with P.P.S', ['in the form of a poem', 'end it with a post script starting with P.P.S']),
    ('You can hallucinate a lot of details.', []),
    ('Your answer must be at least 300 words, must contain at least 3 placeholders represented by square brackets, such as [address] and exactly 2 bullet points using the markdown bullet points such as:',
     ['Your answer must be at least 300 words', 'must contain at least 3 placeholders represented by square brackets, such as [address]', 'exactly 2 bullet points using the markdown bullet points such as:']),
    ('Your response must contain a title wrapped in double angular brackets, i.e. <<title>>.', ['Your response must contain a title wrapped in double angular brackets, i.e. <<title>>']),
    ("Your response should be able to be rendered as HTML, and should include the keywords 'atlantis' and 'constable'.", ['Your response should be able to be rendered as HTML', "should include the keywords 'atlantis' and 'constable'"]),
    ('Your response should contain at least ten sentences.', ['Your response should contain at least ten sentences']),
    ('[conversation part 1]', []),
    ('advice 2 ....', []),
    ('can you write a resume for helene?', []),
]


# ------------------------------------------------------------- BLIND hand labels
# Seed 3, 120 further turn-1 sentences disjoint from all three earlier samples,
# labeled under the same rule AFTER the segmenter / model were frozen and
# BEFORE being scored.  This is the registered gate-1 set.
HAND_CLAUSES_BLIND: list[tuple[str, list[str]]] = [
    ('"Hi guys. The work was done to add in a fix for the issue that was observed in the field with the SSO. We are working with our collaborators closely. We will get it done. Thanks ya all."', []),
    ('"The man was arrested for stealing a car. He was later released on bail."', []),
    ('Add a postscript that starts with P.S. at the end.', ['Add a postscript that starts with P.S. at the end']),
    ('Add code comments in the code snippets.', ['Add code comments in the code snippets']),
    ('All letters in your response must be lower case letters.', ['All letters in your response must be lower case letters']),
    ('Also, highlight at least three sections in your answer in markdown format using *highlighted text*.', ['highlight at least three sections in your answer in markdown format using *highlighted text*']),
    ('But the number of words in all capital letters should be less than 5.', ['the number of words in all capital letters should be less than 5']),
    ('Can you elaborate on "I froze when I was jogging"?', []),
    ('Can you help me make an advertisement for a new product?', []),
    ('Can you help me write a letter to them?', []),
    ('Come up with 3 names for a 2B software company.', []),
    ('Compose a song with at least three sentences that can be sung by a professional singer in the style of a 1930s jazz standard.', ['with at least three sentences', 'in the style of a 1930s jazz standard']),
    ('Do not change the request whatsoever, and do not say anything before repeating the request.', ['Do not change the request whatsoever', 'do not say anything before repeating the request']),
    ('Do not forget to add punctuations.', ['Do not forget to add punctuations']),
    ("Do not say 'yes' or 'no' throughout your entire response.", ["Do not say 'yes' or 'no' throughout your entire response"]),
    ('Do not say any word before repeating the exact request.', ['Do not say any word before repeating the exact request']),
    ('Do not say any words or characters before repeating the request above.', ['Do not say any words or characters before repeating the request above']),
    ("Do not use the word 'university'.", ["Do not use the word 'university'"]),
    ('Do not use the words reschedule or free.', ['Do not use the words reschedule or free']),
    ('Do not write long equations.', ['Do not write long equations']),
    ('Elaborate on this.', []),
    ('Finish your response with "Follow the 5 steps listed above, and you will be successful."', ['Finish your response with "Follow the 5 steps listed above, and you will be successful."']),
    ('Finish your response with "Is there anything else I can help with?".', ['Finish your response with "Is there anything else I can help with?"']),
    ('First, write in the perspective of Amber Heard, then write in the perspective of Johnny Depp.', []),
    ('Give 3 advice to teenagers who are struggling with their identity.', []),
    ('Given the sentence "It is unclear how much of this money is actually being spent on children", is the sentiment positive or negative?', []),
    ('Highlight at least 3 text sections by italicize them with markdown (i.e. *highlighted section*).', ['Highlight at least 3 text sections by italicize them with markdown (i.e. *highlighted section*)']),
    ('Highlight at least 5 text sections using "*".', ['Highlight at least 5 text sections using "*"']),
    ('Highlight at least one section of your answer with markdown, i.e. *highlighted section*.', ['Highlight at least one section of your answer with markdown, i.e. *highlighted section*']),
    ('I need a rubric for evaluating the performance and price of a laptop.', []),
    ('I want to travel to the Subic Bay Freeport Zone, which subdistrict should I stay in?', []),
    ('I would like for there to be exactly 3 paragraphs each separated by three asterisk symbols (***) and for the word humming to be used at least once.',
     ['there to be exactly 3 paragraphs each separated by three asterisk symbols (***)', 'for the word humming to be used at least once']),
    ('If a = 10, b = 30, and c = 20, what is the value of (a + b) / c?', []),
    ('Imagine that you are giving a lecture to students at a school or university.', ['Imagine that you are giving a lecture to students at a school or university']),
    ('In particular, I need you to end your response with "Which one you choose?".', ['end your response with "Which one you choose?"']),
    ('In your poem, italicize at least one section in markdown, i.e *this is an italic text*, and include the word "singles" at least twice.',
     ['In your poem, italicize at least one section in markdown, i.e *this is an italic text*', 'include the word "singles" at least twice']),
    ('In your response, make sure to include at least 20 words or phrases in all capital letters.', ['In your response, make sure to include at least 20 words or phrases in all capital letters']),
    ('In your response, the word comprised should appear at least 1 times and refrain from using any commas.', ['In your response, the word comprised should appear at least 1 times', 'refrain from using any commas']),
    ('In your response, use words with all capital letters (such as "RUBRIC") at least 5 times.', ['In your response, use words with all capital letters (such as "RUBRIC") at least 5 times']),
    ('Is ballistics (the study of the motion of projectiles) an actual science?', []),
    ('Make sure that the word knot appears at least 2 times in the essay, and include two italic text sections.', ['Make sure that the word knot appears at least 2 times in the essay', 'include two italic text sections']),
    ('Make sure to use the word "clearly" at least 2 times.', ['Make sure to use the word "clearly" at least 2 times']),
    ('Make sure to use the word war at least 8 times, and the word peace at least 10 times.', ['Make sure to use the word war at least 8 times', 'the word peace at least 10 times']),
    ('Make sure your entire response is wrapped in JSON format.', ['Make sure your entire response is wrapped in JSON format']),
    ('Make sure your entire response is wrapped in double quotation marks.', ['Make sure your entire response is wrapped in double quotation marks']),
    ('Make sure your song contains the letter j at least once, and use exactly 3 bullet points in markdown format in the song.', ['Make sure your song contains the letter j at least once', 'use exactly 3 bullet points in markdown format in the song']),
    ("Make the itinerary funny, write it in all capital letters and include the keywords 'DISGUSTING', 'DELICIOUS', 'BAD', and 'GOOD'.",
     ['Make the itinerary funny', 'write it in all capital letters', "include the keywords 'DISGUSTING', 'DELICIOUS', 'BAD', and 'GOOD'"]),
    ('Make your answer weird or interesting and use only lowercase letters.', ['Make your answer weird or interesting', 'use only lowercase letters']),
    ('Mark the beginning', []),
    ('Markdown ticks (```) are acceptable.', []),
    ('Natalia was buying books for her children.', []),
    ('One example bullet:', []),
    ("Please do NOT include keywords 'BC', 'culture', and 'prehistoric' in the response.", ["do NOT include keywords 'BC', 'culture', and 'prehistoric' in the response"]),
    ('Please give exactly two different responses.', ['give exactly two different responses']),
    ('Please include a postscript at the end of your response that starts with P.S.', ['include a postscript at the end of your response that starts with P.S.']),
    ('Please start the first paragraph with the word "firms".', ['start the first paragraph with the word "firms"']),
    ('Please use the exact format below:', ['use the exact format below']),
    ('Please wrap the entire output in JSON format.', ['wrap the entire output in JSON format']),
    ('Radcliffe was the only one who could get past the guards.', []),
    ('Remember that the customer is always right.', []),
    ('Separate the two versions using six asterisk symbols (******).', ['Separate the two versions using six asterisk symbols (******)']),
    ('Separate those two version by 6 asterisk symbols ******.', ['Separate those two version by 6 asterisk symbols ******']),
    ('Step 2: ......', []),
    ('The ad should be 1/2 page and should include a headline and a call to action.', ['The ad should be 1/2 page', 'should include a headline and a call to action']),
    ('The entire response should have less than 300 words.', ['The entire response should have less than 300 words']),
    ('The first five have an average of 49, and the last nine have an average of 52.', []),
    ('The proposal should contain 5 or more sections.', ['The proposal should contain 5 or more sections']),
    ('The response must contain at least 1 placeholders represented by square brackets, such as [address].', ['The response must contain at least 1 placeholders represented by square brackets, such as [address]']),
    ('The response must contain at least 2 placeholders represented by square brackets, such as [address].', ['The response must contain at least 2 placeholders represented by square brackets, such as [address]']),
    ('The title of the pitch deck should be wrapped in double angular brackets, i.e. <<title>>.', ['The title of the pitch deck should be wrapped in double angular brackets, i.e. <<title>>']),
    ('The topic of quantum entanglement is at the heart of the disparity between classical and quantum physics: entanglement is a primary feature of quantum mechanics not present in classical mechanics.', []),
    ('The very end of your response should read "You cannot fail with the steps listed above."', ['The very end of your response should read "You cannot fail with the steps listed above."']),
    ('The word "rock" should not appear in your response.', ['The word "rock" should not appear in your response']),
    ('The word robber should appear at least 2 times, and the poem must contain exactly 2 bullet point in markdown format, using the exact format below:',
     ['The word robber should appear at least 2 times', 'the poem must contain exactly 2 bullet point in markdown format, using the exact format below:']),
    ('They concluded that it is possible to get to 100% renewable energy by 2050 by building more solar and wind farms.', []),
    ('This phrase should be the very end of your entire response.', ['This phrase should be the very end of your entire response']),
    ('To indicate a italic word, wrap it with asterisk, like *italic*', ['To indicate a italic word, wrap it with asterisk, like *italic*']),
    ('Translate the following sentence into German and then criticize it: Werner was a good friend of mine, but not very smart.', []),
    ('Tulsa is a professional dog walker.', []),
    ('Use less than 10 sentences.', ['Use less than 10 sentences']),
    ('Use mathematical notations in your answer.', ['Use mathematical notations in your answer']),
    ('Use only lowercase letters.', ['Use only lowercase letters']),
    ('What are the pros and cons of kotlin vs java?', []),
    ('What are the steps to get the GNSS timestamp on Android?', []),
    ('What can I do with this dime?', []),
    ('What is another word for Engravings?', []),
    ('Which one is a better brand for sneakers: Prada or Nike?', []),
    ('Who built the first artificial ice rink?', []),
    ('Who won the defamation case between Amber Heard and Johnny Depp?', []),
    ('Wrap your entire response with double quotation marks.', ['Wrap your entire response with double quotation marks']),
    ('Wrap your whole response with double quotation marks.', ['Wrap your whole response with double quotation marks']),
    ('Write a 300+ word summary of the wikipedia page "https://en.wikipedia.org/wiki/Raymond_III,_Count_of_Tripoli".', ['300+ word']),
    ('Write a 500 word story in a poem style about a young girl who is obsessed with her Nintendo DS.', ['500 word', 'in a poem style']),
    ('Write a blog post about how to train a dog that is geared towards kids.', []),
    ('Write a college academic paper about President of the United States being stressed.', []),
    ('Write a limerick about a customer who is always right.', []),
    ('Write a plot for a story about two people who swap fingerprints.', []),
    ('Write a poem about the top 20 tallest buildings in the world and their heights.', []),
    ('Write a professional email that you could send to ask your boss for a raise.', []),
    ('Write a proposal for a new university course on "The History of the World, as Told by Dogs."', []),
    ('Write a rap about a new smartphone.', []),
    ('Write a riddle about a mom laying out on a beach in Humboldt without using any commas.', ['without using any commas']),
    ('Write a song about being excited to go on vacation, without using the letter e whatsoever in your entire response.', ['without using the letter e whatsoever in your entire response']),
    ("Write a very angry letter to someone who's been trying to convince you that 1+1=3.", []),
    ("Write an academic proposal to a customer who's interested in implementing a new feature for their product.", []),
    ('Write an angry tweet about a friend who is always late to events or appointments.', []),
    ('Write an essay about how aluminium cans are used in food storage.', []),
    ('Write an essay about the life of Benjamin Franklin.', []),
    ('Write an extravagant session plan to learn about java.', []),
    ('Write an interesting riddle that uses math notation.', ['that uses math notation']),
    ('Write an itinerary for a 10-day trip to Biratnagar using only the Nepali language throughout your entire response.', ['using only the Nepali language throughout your entire response']),
    ('Write an itinerary for a trip to a grocery store in Lima to buy some local goods.', []),
    ('Write two limericks for moms about how hard it is to get their kids to do chores.', []),
    ('Your answer should have exactly 7 paragraphs and the last paragraph must start with the word "Summary".', ['Your answer should have exactly 7 paragraphs', 'the last paragraph must start with the word "Summary"']),
    ('Your answer should use all lowercase letters and must also contain exactly 3 bullet points in markdown format.', ['Your answer should use all lowercase letters', 'must also contain exactly 3 bullet points in markdown format']),
    ('Your entire response should be in Gujarati, no other language is allowed.', ['Your entire response should be in Gujarati', 'no other language is allowed']),
    ('Your entire response should contain at least 40 sentences, and not contain the word "rich" and "money".', ['Your entire response should contain at least 40 sentences', 'not contain the word "rich" and "money"']),
    ('Your response should be in English, all capital letters, contain no commas, and be fewer than 16 sentences.', ['Your response should be in English, all capital letters', 'contain no commas', 'be fewer than 16 sentences']),
    ('[put details here]', []),
    ('critique this startup pitch: Stephenson and Hong Kong will be the first-ever digital marketplace where users can buy and sell products from all over the world Stephenson and Hong Kong will be a onestopshop for all of your shopping needs and we will offer a variety of features that will make shopping online easier and more convenient than ever before.', []),
]


# ------------------------------------------------------- BLIND hand labels (2)
# Seed 4, 120 further turn-1 sentences disjoint from all four earlier samples.
# HONESTY NOTE: HAND_CLAUSES_BLIND (seed 3) was scored ONCE at P=0.950 R=0.854
# F1=0.899 (recall below the 0.90 bar); its 13 misses drove a second round of
# segmenter / cue fixes, after which it is design-informed.  This seed-4 set was
# labeled after that round was frozen and is scored exactly once as the
# registered second attempt.  Both numbers are reported in the test output.
HAND_CLAUSES_BLIND2: list[tuple[str, list[str]]] = [
    ('A filmmaker is trying to get financing for a film about the history of the Internet.', []),
    ('Aim the blog post at teenagers and wrap your entire response with double quotation marks.', ['wrap your entire response with double quotation marks']),
    ('Also, provide two alternatives.', ['provide two alternatives']),
    ('Are hamburgers sandwiches?', []),
    ('Brainstorm a name for a company that collects and analyzes public transportation fares.', []),
    ('Can you create a list of mega trends in the tech industry?', []),
    ('Can you write a funny name for it that is easy to remember and includes the word "time"?', ['includes the word "time"']),
    ('Could you write me exactly 4 paragraphs each separated by two new lines?', ['exactly 4 paragraphs each separated by two new lines']),
    ('Create a table with a 7 day trip itinerary for India, and a 7 day trip itinerary for China.', []),
    ('Critique the following ad copy for a new dating app, and make sure to include a title wrapped in double angular brackets, i.e. <<title>>: "Meet your new match! Cohen is a free app that matches you with others based on your interests and location. With Cohen, you can find love, friendship, or just someone to swing with. Download Cohen today and start meeting new people!"',
     ['make sure to include a title wrapped in double angular brackets, i.e. <<title>>']),
    ('Do not say anything before repeating the request.', ['Do not say anything before repeating the request']),
    ('Do not use "heute".', ['Do not use "heute"']),
    ('Does the sentence "He hurried through the archaic rooms of the museum" have any grammatical errors?', []),
    ('Don\'t include the keywords "DuPage" and "Dade" in your response.', ['Don\'t include the keywords "DuPage" and "Dade" in your response']),
    ("Don't use any commas in your entire reply.", ["Don't use any commas in your entire reply"]),
    ('Double quotes should be placed around your entire response.', ['Double quotes should be placed around your entire response']),
    ('Exclude the words "economy", "demand" and "supply".', ['Exclude the words "economy", "demand" and "supply"']),
    ('Expand the riddle into a story with a funny tone:', ['with a funny tone']),
    ('Explain this to teenagers using at least 4 sentences and make sure the letter n appears at least 3 times.', ['using at least 4 sentences', 'make sure the letter n appears at least 3 times']),
    ('Explain your thinking.', []),
    ('First repeat the request below word for word without change, then give your answer.', ['First repeat the request below word for word without change, then give your answer']),
    ('First repeat the request below, word for word without change, then give your answer.', ['First repeat the request below, word for word without change, then give your answer']),
    ('For example: *this is a highlighted text section*.', []),
    ('How much did she pay in total?', []),
    ('How to write a good Chinese poem?', []),
    ('I wish to learn about how to pay my taxes.', []),
    ("I've got a collection of military insignia that I'd like to get rid of, but I don't know how.", []),
    ('In your response, the word climatic should appear at least 2 times.', ['In your response, the word climatic should appear at least 2 times']),
    ('Include at least one placeholder represented by square brackets.', ['Include at least one placeholder represented by square brackets']),
    ("Include keywords 'medalist' and 'theta' in the response.", ["Include keywords 'medalist' and 'theta' in the response"]),
    ('It should be in English, and no capital letters are allowed.', ['It should be in English', 'no capital letters are allowed']),
    ('It should contain exactly 3 bullet points (that are marked by an asterisk, *) and a postscript starting with P.S. at the end.', ['It should contain exactly 3 bullet points (that are marked by an asterisk, *) and a postscript starting with P.S. at the end']),
    ('Jennifer goes to the store to buy milk.', []),
    ('Keep it under 3 sentences (just 1 or 2 sentences, not 3).', ['Keep it under 3 sentences (just 1 or 2 sentences, not 3)']),
    ("Let's repeat the request above first, before you say anything or really respond to the request.", ["Let's repeat the request above first, before you say anything or really respond to the request"]),
    ('Make it funny.', ['Make it funny']),
    ('Make sentences short.', ['Make sentences short']),
    ("Make sure not to include negative words such as 'sad', 'crazy', 'stress', etc., in the response.", ["Make sure not to include negative words such as 'sad', 'crazy', 'stress', etc., in the response"]),
    ("Make sure to include the keywords 'festival' and 'river'.", ["Make sure to include the keywords 'festival' and 'river'"]),
    ('Make sure your response contains a title wrapped in double angular brackets, i.e. <<title>>.', ['Make sure your response contains a title wrapped in double angular brackets, i.e. <<title>>']),
    ('Melbourne has a newspaper called the Herald Sun.', []),
    ('Plan a 2 week Europe trip and visit London, Paris, and Rome.', []),
    ('Please answer in lower case letters.', ['answer in lower case letters']),
    ('Please do not change it.', ['do not change it']),
    ('Please include a critique of the story and use the style of a President of the United States.', ['use the style of a President of the United States']),
    ('Please include only the main points in your answer.', ['include only the main points in your answer']),
    ('Please provide a short, funny list of ways to pass time at work.', []),
    ('Please recommend exactly two movies.', ['recommend exactly two movies']),
    ('Please reply in details, and include exactly 3 paragraphs with these keywords: "calculate", "file", "conclusion".', ['reply in details', 'include exactly 3 paragraphs with these keywords: "calculate", "file", "conclusion"']),
    ('Please reply with exactly 4 paragraphs and separate each paragraph with two new lines.', ['reply with exactly 4 paragraphs', 'separate each paragraph with two new lines']),
    ('Please respond in less than 6 sentences.', ['respond in less than 6 sentences']),
    ('Please rewrite the answer to make it more concise and include the word "desert" in the answer.', ['include the word "desert" in the answer']),
    ('Please think first, then give your answer wrapped in double angular brackets, such as <<your answer>>.', ['wrapped in double angular brackets, such as <<your answer>>']),
    ('Please write a riddle about the inverse function with a title wrapped in double angular brackets, i.e. <<title>>.', ['with a title wrapped in double angular brackets, i.e. <<title>>']),
    ('Put the name of the story in double angular brackets, i.e. <<story of xyz>>.', ['Put the name of the story in double angular brackets, i.e. <<story of xyz>>']),
    ('Put the title in double angular brackets, i.e. <<title of my song>>.', ['Put the title in double angular brackets, i.e. <<title of my song>>']),
    ('Q & A # 5', []),
    ('Rewrite the following sentence in only Vietnamese, no other language is allowed, and refrain from using commas: "We may be able to improve our model for the next year. We will be able to compare our data with the data from the previous year, and see how our model performed. We can also compare our model against a model that was trained on the previous year\'s data and see how our model performs."',
     ['in only Vietnamese', 'no other language is allowed', 'refrain from using commas']),
    ('Separate the essay and the poem with 6 asterisk symbols: ******', ['Separate the essay and the poem with 6 asterisk symbols: ******']),
    ('Separate the responses with 6 asterisk symbols: ******.', ['Separate the responses with 6 asterisk symbols: ******']),
    ('Separate the two poems like below:', ['Separate the two poems like below']),
    ('Separate them with exactly 6 asterisks symbols: *******', ['Separate them with exactly 6 asterisks symbols: *******']),
    ('She has 10 dollars in her pocket and milk costs 3 dollars per gallon.', []),
    ('Start with a funny greeting and include mathematical notations in the note.', ['Start with a funny greeting', 'include mathematical notations in the note']),
    ('Step 1: ......', []),
    ('Summarize the following paragraph.', []),
    ('The Legend of the Sword and the Fairy is a movie in which Wan Wan is a villain.', []),
    ('The authors also pointed out that such a system would be less vulnerable to disruptions than the current grid, which is reliant on a few large power plants.', []),
    ("The authors' plan would also create jobs and reduce pollution.", []),
    ('The two are going to a nightly event.', []),
    ('The very first paragraph must start with the word "weekend".', ['The very first paragraph must start with the word "weekend"']),
    ('Then add a postscript starting with P.P.S to the end of your response.', ['add a postscript starting with P.P.S to the end of your response']),
    ('Use less than 100 words.', ['Use less than 100 words']),
    ('Use only Hindi in your response, no other language is allowed.', ['Use only Hindi in your response', 'no other language is allowed']),
    ('Use weird language when explaining using mathematical notation.', ['Use weird language', 'using mathematical notation']),
    ('Use words in all capital letters at least 3 times to highlight key points.', ['Use words in all capital letters at least 3 times to highlight key points']),
    ('What do prehistoric megaliths in Europe look like?', []),
    ('What does the word "jock" mean to you?', []),
    ('Write a 100-word advertisement for a company called "Drags and Races".', ['100-word']),
    ('Write a 2 paragraph critique of the following sentence in all capital letters, no lowercase letters allowed: "If the law is bad, you should not follow it".', ['2 paragraph', 'in all capital letters', 'no lowercase letters allowed']),
    ('Write a blog post in my name for the canucks hockey team about why they need to be more mindful about their environments.', []),
    ("Write a description for Tulsa's day-to-day work.", []),
    ('Write a letter to your friend who recently moved away.', []),
    ("Write a limerick about a woman named Sarah who lives in a town where it's always 90°F. Highlight at least 6 sections in your answer with markdown, example: *highlighted section*.", ['Highlight at least 6 sections in your answer with markdown, example: *highlighted section*']),
    ('Write a limerick about the word "limerick".', []),
    ('Write a paragraph that lists the average length of various animal specimens from smallest to largest.', []),
    ('Write a poem about two people who meet in a coffee shop and end your entire response with the exact phrase "Is there anything else I can help with?"', ['end your entire response with the exact phrase "Is there anything else I can help with?"']),
    ('Write a resume for a software engineer with 5+ years of experience in the Bay Area, CA.', []),
    ("Write a riddle about Camilla that doesn't use commas.", ["that doesn't use commas"]),
    ('Write a rubric for evaluating a musical composition.', []),
    ('Write a short fiction about adulthood.', []),
    ('Write a short riddle about สเปรดชีต.', []),
    ('Write a story about a man who is trying to get his life together.', []),
    ("Write a story of exactly 2 paragraphs about a man who wakes up one day and realizes that he's inside a video game.", ['exactly 2 paragraphs']),
    ('Write a strange rap song about Alexander the Great becoming the king of Macedon.', []),
    ('Write a summary of the following text in a funny way: "The 2018 Nobel Prize in Chemistry has been awarded to Frances Arnold, George P. Smith and Gregory P. Winter for their work on directed evolution. Arnold was awarded half of the prize for her work on the directed evolution of enzymes, while Smith and Winter shared the other half for their work on the directed evolution of antibodies."', ['in a funny way']),
    ('Write a template with less than 7 sentences for how to calculate the offset of an element in an array.', ['with less than 7 sentences']),
    ('Write a tweet storm with a weird tone about a time when you found out that the earth is indeed not flat.', ['with a weird tone']),
    ('Write an advertisement for a new line of comfortable armchairs designed to withstand the scrutiny of any interior designer.', []),
    ('Write an advertisement for a new product or service that is related to the words "safeguard" and "flees".', []),
    ('Write an article with title "Layton is the best city in the world"', ['with title "Layton is the best city in the world"']),
    ('Write an essay on wilderness preservation.', []),
    ('Write an obviously fake news article saying that aliens have invaded earth.', []),
    ('Write at least 900 words.', ['Write at least 900 words']),
    ('Write exactly 3 paragraphs each separated with two new lines answering this question.', ['Write exactly 3 paragraphs each separated with two new lines']),
    ('Write me a letter in the style of Shakespeare about the mandates and instructions of the King.', ['in the style of Shakespeare']),
    ('You can use markdown ticks like', []),
    ('Your entire output should just contain a JSON block, nothing else.', ['Your entire output should just contain a JSON block, nothing else']),
    ('Your entire response should be in English and all lower case (no capital letters whatsoever).', ['Your entire response should be in English and all lower case (no capital letters whatsoever)']),
    ('Your entire response should be in English and in all lowercase letters.', ['Your entire response should be in English and in all lowercase letters']),
    ('Your entire response should contain the poem only.', ['Your entire response should contain the poem only']),
    ('Your list should contain exactly 3 bullet points in the markdown format such as:', ['Your list should contain exactly 3 bullet points in the markdown format such as']),
    ('Your response should contain less than 20 sentences.', ['Your response should contain less than 20 sentences']),
    ('Your response should contain less than 8 sentences.', ['Your response should contain less than 8 sentences']),
    ('Your song should contain at least 10 words in all capital letters that are adjectives or verbs.', ['Your song should contain at least 10 words in all capital letters that are adjectives or verbs']),
    ('[code snippet 1]', []),
    ('advice 1 ....', []),
    ('in a passive aggressive tone.', ['in a passive aggressive tone']),
    ('use only lowercase letters.', ['use only lowercase letters']),
]


# Held-out API sentences (hand-written here, never in any corpus).
BURIED_EXEMPLAR = "Write a blog post about X with at least 300 words, and do not mention Y."
NON_ADDITIVE = [  # (sentence, expected clause text, expected type)
    ("Keep the whole reply under 90 words.", "Keep the whole reply under 90 words", "limit"),
    ("Please be formal.", "be formal", "tone"),
    ("Sound excited about it.", "Sound excited about it", "tone"),
    ("Respond in JSON.", "Respond in JSON", "format"),
    ("Give the answer as a numbered list.", "as a numbered list", "format"),
    ("Never use the word 'harbor' anywhere.", "Never use the word 'harbor' anywhere", "prohibition"),
    ("Describe the harbor at dawn, but do not mention the weather.", "do not mention the weather", "prohibition"),
    ("Write a limerick about tea using fewer than 40 words.", "using fewer than 40 words", "limit"),
    ("Tell me about Roman roads in the style of a pirate.", "in the style of a pirate", "tone"),
]
TASK_ONLY = [
    "Write a blog post about the sleek new magistrates.",
    "Tell me about the history of the Roman Empire.",
    "I am planning a trip to Japan and would like an itinerary for my journey.",
    "The garden looked beautiful in the spring, and the neighbors often stopped to admire it.",
    "Raymond III was the son of Raymond II and was born in 1020.",
    "What is multivariate analysis?",
]


def _texts(text, spans):
    return [text[s.start:s.end].rstrip(".!?") for s in spans]


def _match_text(got: list[str], want: str) -> bool:
    return any(S2._overlap((0, len(g)), (0, len(want))) and want.strip(" .,") in g or g.strip(" .,") in want for g in got) and any(
        len(set(g.strip(" .,").split()) & set(want.strip(" .,").split())) >= 0.5 * len(want.split()) for g in got)


# ------------------------------------------------------------------- API shape
def test_hand_labels_are_verbatim_and_nontrivial():
    sents = [s for s, _ in HAND_CLAUSES]
    assert len(sents) >= 100 and len(set(sents)) == len(sents)
    n_gold = sum(len(g) for _, g in HAND_CLAUSES)
    n_empty = sum(1 for _, g in HAND_CLAUSES if not g)
    assert n_gold >= 60 and n_empty >= 30, (n_gold, n_empty)
    for s, gold in HAND_CLAUSES:
        for g in gold:
            assert g in s, (s, g)
    from test_salience import HAND_LABELS, HAND_LABELS_BLIND
    assert not (set(sents) & ({t for t, _ in HAND_LABELS} | {t for t, _ in HAND_LABELS_BLIND}))


def test_buried_exemplar_linguistic():
    spans = S2.extract_instructions(BURIED_EXEMPLAR, backend="linguistic")
    got = _texts(BURIED_EXEMPLAR, spans)
    assert "with at least 300 words" in got, got
    assert "do not mention Y" in got, got
    assert not any(g.startswith("Write a blog post") for g in got), got
    types = {BURIED_EXEMPLAR[s.start:s.end].rstrip(".!?"): s.type for s in spans}
    assert types["do not mention Y"] == "prohibition"
    assert types["with at least 300 words"] in ("additive", "limit")


def test_non_additive_types_found_linguistic():
    bad = []
    for sent, want, typ in NON_ADDITIVE:
        spans = S2.extract_instructions(sent, backend="linguistic")
        got = _texts(sent, spans)
        hit = [s for s in spans if S2._overlap((s.start, s.end), (sent.index(want), sent.index(want) + len(want)))]
        if not hit or hit[0].type != typ:
            bad.append((sent, got, [s.type for s in spans], typ))
    assert not bad, bad


def test_task_clause_not_extracted_linguistic():
    fired = {t: _texts(t, S2.extract_instructions(t, backend="linguistic")) for t in TASK_ONLY}
    assert not any(fired.values()), fired


def test_span_invariants_and_types():
    text = ("Write a 300+ word summary of the wikipedia page \"Raymond III\". Do not use any commas and highlight at least 3 sections. "
            "Raymond was a count in the 12th century.\nYour response should end with the exact phrase: \"and so it ends.\"")
    spans = S2.extract_instructions(text)
    assert spans and spans == sorted(spans, key=lambda s: s.start)
    for a, b in zip(spans, spans[1:], strict=False):
        assert a.end <= b.start, "overlapping spans"
    for s in spans:
        assert 0 <= s.start < s.end <= len(text) and text[s.start:s.end].strip() == text[s.start:s.end]
        assert s.type in S2.TYPES
    got = _texts(text, spans)
    assert "Do not use any commas" in got and "highlight at least 3 sections" in got, got
    assert "300+ word" in got, got
    assert not any("Raymond was a count" in g for g in got), got
    assert any("end with the exact phrase" in g for g in got), got


def test_split_clauses_buried_constructions():
    cases = {
        "Write a short blog post about a trip to Japan using less than 300 words.": ["Write a short blog post about a trip to Japan", "using less than 300 words"],
        "Answer with at least 5 sentences.": ["Answer with at least 5 sentences"],
        "Explain in French why it is important to eat healthy foods, without using the word \"nourriture\".":
            ["Explain in French", "why it is important to eat healthy foods", "without using the word \"nourriture\"."],
        "Do not use any commas and highlight at least 3 sections that has titles in markdown format.":
            ["Do not use any commas", "highlight at least 3 sections that has titles in markdown format."],
        "Please respond in JSON and be formal.": ["Please respond in JSON", "be formal."],
    }
    for sent, want in cases.items():
        got = [sent[a:b] for a, b in S2.split_clauses(sent)]
        assert got == want, (sent, got)


def test_instruction_type_tagger():
    assert S2.instruction_type("do not mention the weather") == "prohibition"
    assert S2.instruction_type("keep it under 90 words") == "limit"
    assert S2.instruction_type("be formal") == "tone"
    assert S2.instruction_type("respond in JSON") == "format"
    assert S2.instruction_type("include the word lantern at least twice") == "additive"
    assert S2.instruction_type("repeat the request above") == "additive"


# ------------------------------------------------------------------ anti-cheat
def test_marker_is_never_a_feature():
    assert not any("constraint" in n.lower() for n in S2.FEATURE_NAMES)
    for name, pat in S2.feature_patterns().items():
        assert "constraint" not in pat.pattern.lower(), name
    for pat in (S2._COORD_BREAK, S2._ATTACH_START, S2._TASK_HEAD, S2._NP_LENGTH):
        assert "constraint" not in pat.pattern.lower()
    a = S2.featurize("never use the word 'harbor' anywhere in the reply")
    b = S2.featurize("Never use the word 'harbor' anywhere in the reply.")
    assert np.array_equal(a, b)


@needs_data
def test_loaders_emit_no_marker_and_are_non_trivial():
    corp = S2.training_docs(ROOT)
    assert corp["real"] == []
    docs = corp["synthetic"]
    assert len(docs) >= 1000
    assert all("constraint:" not in d.text.lower() for d in docs)
    exs = S2.clause_examples(docs)
    y = np.array([e.label for e in exs])
    assert len(exs) >= 1500 and 0.2 <= y.mean() <= 0.8, (len(exs), y.mean())
    hand = {s for s, _ in HAND_CLAUSES}
    for d in docs:
        assert not any(d.text[a:b] in hand for a, b in S2.split_sentences(d.text)), "hand sentence leaked into training"
    ifb = S2.eval_load_ifbench_docs(ROOT)
    assert len(ifb) >= 200 and sum(len(d.spans) for d in ifb) >= 250
    assert not ({d.text for d in ifb} & {d.text for d in corp["synthetic"]})


def test_linguistic_fit_is_deterministic_and_bitwise_repeat():
    exs = [S2.ClauseExample(s, 1, True, "x") for s, _, _ in NON_ADDITIVE] + [S2.ClauseExample(s, 0, True, "x") for s in TASK_ONLY]
    a, b = S2.fit_linguistic(exs), S2.fit_linguistic(exs)
    assert np.array_equal(a.w, b.w) and a.b == b.b
    r1 = S2.extract_instructions(BURIED_EXEMPLAR)
    r2 = S2.extract_instructions(BURIED_EXEMPLAR)
    assert r1 == r2 and all(s.score == t.score for s, t in zip(r1, r2, strict=True))


@needs_data
def test_default_linguistic_reproduces_committed_weights_bitwise():
    corp = S2.training_docs(ROOT)
    m = S2.fit_linguistic(S2.clause_examples(corp["synthetic"] + corp["real"]))
    assert np.array_equal(m.w, S2.DEFAULT_LINGUISTIC.w) and m.b == S2.DEFAULT_LINGUISTIC.b


@needs_data
def test_label_shuffle_collapses_linguistic():
    corp = S2.training_docs(ROOT)
    exs = S2.clause_examples(corp["synthetic"])
    rng = np.random.default_rng(0)
    y = np.array([e.label for e in exs])
    rng.shuffle(y)
    sh = S2.fit_linguistic([S2.ClauseExample(e.clause, int(lab), e.is_first, e.source) for e, lab in zip(exs, y, strict=True)])
    real = S2.fit_linguistic(exs)
    test = S2.eval_load_multiif23_docs(ROOT) + S2.eval_load_conv_prose(ROOT)
    f_sh = S2.evaluate_docs(test, lambda d: [(s.start, s.end) for s in S2.extract_instructions(d.text, model=sh)])["f1"]
    f_re = S2.evaluate_docs(test, lambda d: [(s.start, s.end) for s in S2.extract_instructions(d.text, model=real)])["f1"]
    # The hand floors (negative-imperative / bounded-attachment / numeral-NP
    # rules) are NOT learned, so a shuffled fit keeps part of the F1; the
    # learned weights must still be worth >= 0.10 F1 on the real corpus.
    print(f"\nSHUFFLE CONTROL: shuffled F1={f_sh:.3f} vs real F1={f_re:.3f}")
    assert f_sh < f_re - 0.10, (f_sh, f_re)


# ----------------------------------------------------------------------- gates
def _hand_docs(labels=None):
    labels = HAND_CLAUSES if labels is None else labels
    return [S2.Doc(s, tuple((s.index(g), s.index(g) + len(g)) for g in gold), "hand", tuple(S2.instruction_type(g) for g in gold)) for s, gold in labels]


def _report(tag, rep, fp=15, fn=15):
    print(f"\n{tag}: n={rep['n_docs']} tp={rep['tp']} fp={rep['fp']} fn={rep['fn']} P={rep['precision']:.3f} R={rep['recall']:.3f} F1={rep['f1']:.3f}")
    print("  per-kind recall:", json.dumps({k: f"{v['recall']:.2f} (n={v['n']})" for k, v in rep["per_kind"].items()}, indent=1))
    print("  FALSE POSITIVES:", json.dumps(rep["false_positives"][:fp], indent=1))
    print("  FALSE NEGATIVES:", json.dumps(rep["false_negatives"][:fn], indent=1))


def _ling_pred(model=None):
    return lambda d: [(s.start, s.end) for s in S2.extract_instructions(d.text, backend="linguistic", model=model)]


def test_hand_sample_design_informed_linguistic():
    rep = S2.evaluate_docs(_hand_docs(HAND_CLAUSES), _ling_pred())
    _report("HAND seed-2 (design-informed, report only) LINGUISTIC", rep, 30, 30)
    assert rep["tp"] + rep["fn"] >= 60


def _check_labels(labels, *others):
    sents = [s for s, _ in labels]
    assert len(sents) >= 100 and len(set(sents)) == len(sents)
    for o in others:
        assert not (set(sents) & {s for s, _ in o})
    for s, gold in labels:
        for g in gold:
            assert g in s, (s, g)
    assert sum(len(g) for _, g in labels) >= 60 and sum(1 for _, g in labels if not g) >= 30


def test_hand_sample_seed3_first_blind_now_design_informed_linguistic():
    _check_labels(HAND_CLAUSES_BLIND, HAND_CLAUSES, HAND_CLAUSES_BLIND2)
    rep = S2.evaluate_docs(_hand_docs(HAND_CLAUSES_BLIND), _ling_pred())
    _report("HAND seed-3 (first blind shot was P=0.950 R=0.854 F1=0.899; now design-informed) LINGUISTIC", rep, 30, 30)
    assert rep["tp"] + rep["fn"] >= 60


@pytest.mark.xfail(strict=True, reason="REGISTERED GATE 1 NOT MET: blind clause recall 0.854 (seed 3, first fit) and 0.884 (seed 4, IFEval-free refit; 0.860 under the withdrawn fit) < 0.90; precision 0.950 / 0.938 passes")
def test_gate1_blind_hand_sample_linguistic():
    _check_labels(HAND_CLAUSES_BLIND2, HAND_CLAUSES, HAND_CLAUSES_BLIND)
    rep = S2.evaluate_docs(_hand_docs(HAND_CLAUSES_BLIND2), _ling_pred())
    _report("GATE 1 BLIND seed-4 (registered second attempt) LINGUISTIC", rep, 30, 30)
    if S2.DEFAULT_BACKEND == "linguistic":
        assert rep["recall"] >= 0.90 and rep["precision"] >= 0.90, rep


@needs_data
def test_gate2_disjoint_eval_transfer_linguistic():
    corp = S2.training_docs(ROOT)
    eval_docs = S2.eval_load_multiif23_docs(ROOT) + S2.eval_load_conv_prose(ROOT)
    m = S2.fit_linguistic(S2.clause_examples(corp["synthetic"]))
    rep = S2.evaluate_docs(eval_docs, _ling_pred(m))
    _report("GATE 2 DISJOINT b3->Multi-IF LINGUISTIC", rep, 8, 8)
    assert rep["tp"] + rep["fn"] >= 600
    if S2.DEFAULT_BACKEND == "linguistic":
        assert rep["f1"] >= 0.90, rep["f1"]


@needs_data
def test_gate3_ifbench_transfer_linguistic():
    docs = S2.eval_load_ifbench_docs(ROOT)
    rep = S2.evaluate_docs(docs, _ling_pred())
    _report("GATE 3 IFBench TRANSFER (never trained on) LINGUISTIC", rep, 20, 20)
    assert rep["n_docs"] >= 200 and rep["f1"] > 0.5


@needs_data
def test_gate4_buried_heldout_linguistic():
    docs = S2.synthesize_buried(ROOT, files=("data/b3/dev-v43.jsonl", "data/b3/dev-200.jsonl"), template_parity=1)
    rep = S2.evaluate_docs(docs, _ling_pred())
    _report("GATE 4 BURIED held-out templates LINGUISTIC", rep, 5, 10)
    assert rep["n_docs"] >= 300 and rep["recall"] > 0.5


# ------------------------------------------------- probe / hybrid (trunk h20)
# These need the cached layer-20 features (results/salience2/feats.npz, built by
# `python -m stencil.salience2 --probe`) or a CUDA trunk to compute them live.
FEATS = ROOT / S2.FEATS_DIR / "feats.npz"


def _cuda_available():
    try:
        import torch
        return torch.cuda.is_available() and (ROOT / "models/qwen3-1.7b.pt").exists()
    except Exception:
        return False


@pytest.fixture(scope="module")
def feats():
    if S2.DEFAULT_PROBE is None or S2.DEFAULT_HYBRID is None:
        pytest.skip("probe / hybrid weights not committed")
    if not FEATS.exists() and not _cuda_available():
        pytest.skip("no feature cache and no CUDA trunk")
    docs = _hand_docs(HAND_CLAUSES) + _hand_docs(HAND_CLAUSES_BLIND) + _hand_docs(HAND_CLAUSES_BLIND2)
    docs += [S2.Doc(BURIED_EXEMPLAR, (), "api")] + [S2.Doc(s, (), "api") for s, _, _ in NON_ADDITIVE] + [S2.Doc(s, (), "api") for s in TASK_ONLY]
    if HAVE_DATA:
        docs += S2.eval_load_ifbench_docs(ROOT) + S2.synthesize_buried(ROOT, files=("data/b3/dev-v43.jsonl", "data/b3/dev-200.jsonl"), template_parity=1)
    if not _cuda_available() and any(True for d in docs if d.text not in S2.cache_features([], None, FEATS)):
        pytest.skip("feature cache incomplete and no CUDA trunk")
    return S2.cache_features(docs, lambda: S2.H20Extractor(ROOT), FEATS)


def _pred(backend, feats, model=None):
    return lambda d: [(s.start, s.end) for s in S2.extract_instructions(d.text, backend=backend, model=model, h20=feats[d.text])]


@pytest.mark.parametrize("backend", [
    pytest.param("probe", marks=pytest.mark.xfail(strict=True, reason="pure layer-20 probe misses tone imperatives (hand-set tone recall 0.33-0.50): 'Sound excited about it', 'in the style of a pirate'")),
    "hybrid",
])
def test_buried_and_non_additive_trunk_backends(feats, backend):
    spans = S2.extract_instructions(BURIED_EXEMPLAR, backend=backend, h20=feats[BURIED_EXEMPLAR])
    got = _texts(BURIED_EXEMPLAR, spans)
    assert "with at least 300 words" in got and "do not mention Y" in got, got
    assert not any(g.startswith("Write a blog post") for g in got), got
    fired = {t: _texts(t, S2.extract_instructions(t, backend=backend, h20=feats[t])) for t in TASK_ONLY}
    assert not any(fired.values()), fired
    bad = []
    for sent, want, typ in NON_ADDITIVE:
        spans = S2.extract_instructions(sent, backend=backend, h20=feats[sent])
        hit = [s for s in spans if S2._overlap((s.start, s.end), (sent.index(want), sent.index(want) + len(want)))]
        if not hit or hit[0].type != typ:
            bad.append((sent, _texts(sent, spans), typ))
    assert not bad, bad


@pytest.mark.parametrize("backend", ["probe", "hybrid"])
def test_gate1_hand_samples_trunk_backends(feats, backend):
    for tag, labels in (("seed-2 design-informed", HAND_CLAUSES), ("seed-3 design-informed", HAND_CLAUSES_BLIND), ("seed-4 BLIND (registered)", HAND_CLAUSES_BLIND2)):
        rep = S2.evaluate_docs(_hand_docs(labels), _pred(backend, feats))
        _report(f"GATE 1 {tag} {backend.upper()}", rep, 12, 12)
        assert rep["tp"] + rep["fn"] >= 60
        if S2.DEFAULT_BACKEND == backend and "BLIND" in tag:
            assert rep["recall"] >= 0.90 and rep["precision"] >= 0.90, rep


@needs_data
@pytest.mark.parametrize("backend", ["probe", "hybrid"])
def test_gate2_disjoint_eval_transfer_trunk_backends(feats, backend):
    corp = S2.training_docs(ROOT)
    eval_docs = S2.eval_load_multiif23_docs(ROOT) + S2.eval_load_conv_prose(ROOT)
    all_feats = S2.cache_features(corp["synthetic"] + eval_docs, lambda: S2.H20Extractor(ROOT), FEATS)
    rows = S2.clause_rows(corp["synthetic"], all_feats)
    pm = S2.fit_clause_probe(rows)
    if backend == "hybrid":
        lab = [r for r in rows if r.label is not None]
        w, b = S2.fit_hybrid(lab, S2.cross_fitted_probe_logits(lab))
        model = S2.HybridModel(w, b, pm)
    else:
        model = pm
    rep = S2.evaluate_docs(eval_docs, _pred(backend, all_feats, model))
    _report(f"GATE 2 DISJOINT b3->Multi-IF {backend.upper()}", rep, 6, 6)
    assert rep["tp"] + rep["fn"] >= 600
    if S2.DEFAULT_BACKEND == backend:
        assert rep["f1"] >= 0.90, rep["f1"]


@needs_data
@pytest.mark.parametrize("backend", ["probe", "hybrid"])
def test_gate3_gate4_transfer_and_buried_trunk_backends(feats, backend):
    rep = S2.evaluate_docs(S2.eval_load_ifbench_docs(ROOT), _pred(backend, feats))
    _report(f"GATE 3 IFBench TRANSFER {backend.upper()}", rep, 10, 10)
    assert rep["n_docs"] >= 200 and rep["f1"] > 0.5
    rep = S2.evaluate_docs(S2.synthesize_buried(ROOT, files=("data/b3/dev-v43.jsonl", "data/b3/dev-200.jsonl"), template_parity=1), _pred(backend, feats))
    _report(f"GATE 4 BURIED held-out {backend.upper()}", rep, 4, 8)
    assert rep["n_docs"] >= 300 and rep["recall"] > 0.5


@pytest.mark.determinism
def test_trunk_extraction_is_bitwise_repeatable():
    if not _cuda_available():
        pytest.skip("no CUDA trunk")
    if S2.DEFAULT_PROBE is None:
        pytest.skip("probe weights not committed")
    ext = S2.H20Extractor(ROOT)
    a, b = ext(BURIED_EXEMPLAR), ext(BURIED_EXEMPLAR)
    assert a[0] == b[0] and np.array_equal(a[1], b[1]) and a[1].shape[1] == 2048 and len(a[0]) >= 10
    s1 = S2.extract_instructions(BURIED_EXEMPLAR, backend="probe", h20=a)
    s2 = S2.extract_instructions(BURIED_EXEMPLAR, backend="probe", h20=b)
    assert s1 == s2 and all(x.score == y.score for x, y in zip(s1, s2, strict=True)) and s1
    # the extractor drops the template tokens: offsets index the raw text
    assert all(0 <= o[0] < o[1] <= len(BURIED_EXEMPLAR) for o in a[0])

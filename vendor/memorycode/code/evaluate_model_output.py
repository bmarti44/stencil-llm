import json
import os
import re
import warnings

import fire
import numpy as np
from extract_objects import get_all_objects


def extract_code(text):
    """Extracts the Python code from the LM output"""
    # Try multiple code wrappers ```python and ```
    pattern = re.compile(r"\`\`\`python\n(.*?)\`\`\`", re.DOTALL)
    code_match = pattern.findall(text)
    if not code_match:
        pattern = re.compile(r"\`\`\`(.*?)\`\`\`", re.DOTALL)
        code_match = pattern.findall(text)
    extracted_text = code_match[0] if code_match else text
    return extracted_text


def compute_score(text, object_type, regex):
    """Computes the macro-averaged score for a given object and regex."""
    python_text_code = extract_code(text)
    try:
        all_found_objects = get_all_objects(python_text_code)
    except SyntaxError:
        return 0
    found_objects = all_found_objects[object_type]
    # Absent objects are not penalized
    if len(found_objects) == 0 and object_type not in ["comment", "import"]:
        return None

    if isinstance(regex, bool):
        # "Always include objects" or "Never include objects" instructions
        is_present = [len(o) > 0 for o in found_objects]
        if regex:
            score = all(is_present)
        else:
            score = not any(is_present)
    elif isinstance(regex, list):
        name, value = regex
        if object_type not in ["comment", "import"]:
            is_correct = [(name in o) == value for o in found_objects]
            score = np.mean(is_correct) == 1
        else:
            score = (name in found_objects) == value
    else:
        # "Objects that match the regex" instructions
        score = np.mean([bool(re.match(r"{}".format(regex), obj[0])) for obj in found_objects if len(obj) > 0]) == 1
    return float(score)


def merge_dialogue_and_model_output(dialogue, model_output):
    """Merge the template and model output files"""
    for template_session, model_output_sessions in zip(dialogue["sessions"], model_output["sessions"]):
        for k, v in model_output_sessions.items():
            template_session[k] = v
    return dialogue


def compute_dialogue_score(dialogue, model_output):
    """Compute the score per session for a given dialogue"""
    history_scores = []
    session_scores = []
    instruction_scores = []

    dialogue = merge_dialogue_and_model_output(dialogue, model_output)
    for session in dialogue["sessions"]:
        if session["history_regex"]:
            history_score = []
            for output in session["history_model_output"]:
                output_score = []
                for object, regex in session["history_regex"]:
                    score = compute_score(output, object, regex)
                    if score is not None:
                        output_score.append(score)
                mean_output_score = np.nanmean(output_score)
                history_score.append(mean_output_score)
            mean_history_score = np.nanmean(history_score)
            history_scores.append(mean_history_score)

        else:
            # No history evaluation
            history_scores.append(np.nan)

        if session["session_regex"]:
            session_score = []
            for output in session["session_model_output"]:
                output_score = []
                for object, regex in session["session_regex"]:
                    score = compute_score(output, object, regex)
                    if score is not None:
                        output_score.append(score)
                mean_output_score = np.nanmean(output_score)
                session_score.append(mean_output_score)
            mean_session_score = np.nanmean(session_score)
            session_scores.append(mean_session_score)

            instruction_score = []
            for output, (object, regex), eval_query in zip(
                session["instruction_model_output"], session["session_regex"], session["session_eval_query"]
            ):
                score = compute_score(output, object, regex)
                if score is not None:
                    instruction_score.append(score)
                else:
                    warnings.warn(
                        f"Warning - Object {object} not covered in the instruction-only evaluation query: {eval_query}"
                    )
            mean_instruction_score = np.nanmean(instruction_score)
            instruction_scores.append(mean_instruction_score)
        else:
            session_scores.append(np.nan)
            instruction_scores.append(np.nan)
    return history_scores, session_scores, instruction_scores


def evaluate_all_dialogues(
    dialogue_dir,
    model_output_dir,
):
    scores = {"short history": [], "long history": [], "session": [], "instruction": []}
    for model_output_file in os.listdir(model_output_dir):
        dialogue_id = model_output_file.split("_")[1].split(".")[0]
        dialogue_file = f"dialogue_{dialogue_id}.json"
        dialogue_file = os.path.join(dialogue_dir, dialogue_file)
        model_output_file = os.path.join(model_output_dir, model_output_file)

        with open(dialogue_file, "r") as f:
            dialogue = json.load(f)
        with open(model_output_file, "r") as f:
            model_outputs = json.load(f)

        history_scores, session_scores, instruction_scores = compute_dialogue_score(dialogue, model_outputs)
        scores["session"].append(session_scores)
        scores["instruction"].append(instruction_scores)
        if int(dialogue_id) <= 210:
            scores["short history"].append(history_scores)
        else:
            scores["long history"].append(history_scores)

    # Reduce scores
    max_length = max(len(s) for s in scores["long history"])
    for k in scores.keys():
        scores[k] = [s + [np.nan] * (max_length - len(s)) for s in scores[k]]
    per_session_scores = {k: np.nanmean(score, axis=0).tolist() for k, score in scores.items()}
    macro_averaged_scores = {k: np.nanmean(v) for k, v in per_session_scores.items()}

    print("Average scores:\n", macro_averaged_scores)


if __name__ == "__main__":
    fire.Fire(evaluate_all_dialogues)

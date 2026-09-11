import json
import os
import random
from collections import defaultdict

import fire


def generate_template(
    template_id,
    topics_file,
    n_session_min,
    n_session_max,
    proportion_of_session_with_instruction_min,
    proportion_of_session_with_instruction_max,
    n_instruction_only_session_min,
    n_instruction_only_session_max,
    n_instruction_per_instruction_session_min,
    n_instruction_per_instruction_session_max,
    instruction_update_rate_min,
    instruction_update_rate_max,
    max_update_per_filler,
    filler_instruction_rate_min,
    filler_instruction_rate_max,
    filler_instruction_update_rate_min,
    filler_instruction_update_rate_max,
    output_dir,
):
    """Generates a template for a dialogue.

    Args:
        template_id: Template id
        topics_file: File containing the list of topics for instructions and fillers
        n_session_min: Minimum number of sessions
        n_session_max: Maximum number of sessions
        proportion_of_session_with_instruction_min: Min proportion of sessions containing instructions (0-1)
        proportion_of_session_with_instruction_max: Max proportion of sessions containing instructions (0-1)
        n_instruction_only_session_min: Minimum number of sessions containing only instructions (i.e no fillers)
        n_instruction_only_session_max: Maximum number of sessions containing only instructions (i.e no fillers)
        n_instruction_per_instruction_session_min: Minimum number of instructions per session that contains instructions
        n_instruction_per_instruction_session_max: Maximum number of instructions per session that contains instructions
        instruction_update_rate_min: Minimum rate of instruction updates (0-1)
        instruction_update_rate_max: Maximum rate of instruction updates (0-1)
        max_update_per_filler: Maximum number of times a filler can be updated
        filler_instruction_rate_min: Minimum rate of filler instruction updates (0-1)
        filler_instruction_rate_max: Maximum rate of filler instruction updates (0-1)
        filler_instruction_update_rate_min: Minimum rate of filler instruction updates (0-1)
        filler_instruction_update_rate_max: Maximum rate of filler instruction updates (0-1)
        output_dir: Output directory to save the generated template
    """
    with open(topics_file, "r") as f:
        topics = json.load(f)

    SESSION_LENGTH = ["short", "medium", "long"]
    assert proportion_of_session_with_instruction_min > 0
    assert proportion_of_session_with_instruction_max <= 1

    ### Sessions
    n_session = random.randint(n_session_min, n_session_max)
    session_length = random.choices(SESSION_LENGTH, k=n_session)

    ### instructions
    proportion_of_session_with_instruction = random.uniform(
        proportion_of_session_with_instruction_min, proportion_of_session_with_instruction_max
    )
    n_session_with_instruction = int(n_session * proportion_of_session_with_instruction)
    instruction_positions = random.sample(range(n_session), n_session_with_instruction)
    n_instruction_only_session = random.randint(n_instruction_only_session_min, n_instruction_only_session_max)
    instruction_positions_instruction_only_sessions = random.sample(instruction_positions, n_instruction_only_session)
    n_instruction_per_session = {
        p: random.randint(n_instruction_per_instruction_session_min, n_instruction_per_instruction_session_max)
        for p in instruction_positions
    }
    instruction_update_rate = random.uniform(instruction_update_rate_min, instruction_update_rate_max)
    # Sample instructions
    (
        instruction_template,
        instruction_type,
        instruction_text,
        instruction_regex,
        history_instruction_regex,
        instruction_eval,
        history_instruction_eval,
    ) = sample_instructions(
        topics, n_session, instruction_positions, n_instruction_per_session, instruction_update_rate
    )

    ### Fillers
    filler_instruction_rate = random.uniform(filler_instruction_rate_min, filler_instruction_rate_max)
    filler_instruction_update_rate = random.uniform(
        filler_instruction_update_rate_min, filler_instruction_update_rate_max
    )
    # Sample fillers
    filler_template, filler_type, filler_text = sample_fillers(
        topics,
        n_session,
        max_update_per_filler,
        n_instruction_only_session,
        instruction_positions_instruction_only_sessions,
        filler_instruction_rate,
        filler_instruction_update_rate,
    )

    ### Combine instructions and fillers
    sessions = []
    for session_idx in range(n_session):
        types, texts, regexs, history_labels, evals, history_evals = (
            [],
            [],
            [],
            [],
            [],
            [],
        )
        # fillers
        if filler_template[session_idx] != -1:
            types.append(filler_type[session_idx])
            texts.append(filler_text[session_idx])
        # instructions
        if session_idx in instruction_positions:
            types += instruction_type[session_idx]
            texts += instruction_text[session_idx]
        history_labels += history_instruction_regex[session_idx]
        regexs += instruction_regex[session_idx]
        evals += instruction_eval[session_idx]
        history_evals += history_instruction_eval[session_idx]

        session = {
            "type": types,
            "topic": texts,
            "session_regex": regexs,
            "history_regex": history_labels,
            "session_eval_query": evals,
            "history_eval_query": history_evals,
            "session_length": session_length[session_idx],
        }
        sessions.append(session)

    ### Contexts and personas
    context = random.choice(topics["contexts"])
    context["mentor_persona"] = random.choice(topics["personas"]["mentor"])
    context["mentee_persona"] = random.choice(topics["personas"]["mentee"])

    ### Final template
    template = {
        "context": context,
        "instructions": instruction_template,
        "fillers": filler_template,
        "sessions": sessions,
    }
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"dialogue_{template_id}.json")
    with open(output_file, "w") as f:
        json.dump(template, f, indent=1)


def sample_instructions(topics, n_session, instruction_positions, n_instruction_per_session, instruction_update_rate):
    """Sample instructions for a dialogue."""
    instruction_topics = {instruction["id"]: instruction for instruction in topics["instructions"]}
    instruction_topics_by_type = defaultdict(list)
    for instruction_id, instruction in instruction_topics.items():
        instruction_type = instruction["regex"][0][0]
        instruction_topics_by_type[instruction_type].append(instruction_id)
    instruction_types = list(instruction_topics_by_type.keys())
    # instructions that can be updated
    instruction_ids_with_updates = list(range(6, 16))
    # Combine text and regex
    for instruction_id in instruction_topics.keys():
        curr_instruction = instruction_topics[instruction_id]
        curr_instruction["text_regex"] = [
            (text_id, text, regex)
            for text_id, (text, regex) in enumerate(zip(curr_instruction["text"], curr_instruction["regex"]))
        ]

    instruction_template = []
    instruction_type = []
    instruction_text = []
    instruction_regex = []
    history_instruction_regex = []
    latest_history_instruction_regex = {}
    instruction_eval = []
    history_instruction_eval = []

    current_history_eval = set()
    # previously introduced instructions that now can be updated
    updatable_instruction_ids = set()

    for session_idx in range(n_session):
        if session_idx in instruction_positions:
            n_instruction = n_instruction_per_session[session_idx]
            # Prevent update of the same instruction in the same session
            seen_instructions_session = set()
            instruction_update_ids, texts, regexs, session_eval, type = [], [], {}, [], []
            for _ in range(n_instruction):
                # Sample object type first before sampling instructions
                selected_instruction_ids_per_type = set()
                for t in instruction_types:
                    instruction_ids = [p for p in instruction_topics_by_type[t] if p in instruction_topics.keys()]
                    if len(instruction_ids) > 0:
                        selected_instruction_id = random.choice(instruction_ids)
                        selected_instruction_ids_per_type.add(selected_instruction_id)

                # Insertion or update
                insertion_instruction_ids = list(
                    selected_instruction_ids_per_type - updatable_instruction_ids - seen_instructions_session
                )
                update_instruction_ids = list(updatable_instruction_ids - seen_instructions_session)
                if random.random() < instruction_update_rate or len(insertion_instruction_ids) == 0:
                    if len(update_instruction_ids) > 0:
                        instruction_id = random.choice(update_instruction_ids)
                        type.append("instruction-update")
                    else:
                        # Introduce a instruction that can be updated if not introduced yet
                        multi_update_insertion_instruction_ids = [
                            p
                            for p in instruction_ids_with_updates
                            if p in instruction_topics.keys() and p not in updatable_instruction_ids
                        ]
                        instruction_id = random.choice(multi_update_insertion_instruction_ids)
                        updatable_instruction_ids.add(instruction_id)
                        type.append("instruction-add")
                else:
                    instruction_id = random.choice(insertion_instruction_ids)
                    if instruction_id in instruction_ids_with_updates:
                        updatable_instruction_ids.add(instruction_id)
                    type.append("instruction-add")
                seen_instructions_session.add(instruction_id)

                # shuffle updates or not
                text_regex = instruction_topics[instruction_id]["text_regex"]
                if instruction_topics[instruction_id]["shuffle_updates"]:
                    selected_update = random.randint(0, len(text_regex) - 1)
                else:
                    selected_update = 0
                update_id, text, regex = text_regex.pop(selected_update)
                instruction_update_ids.append([instruction_id, update_id])
                texts.append(text)
                regexs[instruction_id] = regex
                session_eval.append(instruction_topics[instruction_id]["eval_query"])

                # Remove instructions that cannot be updated anymore and add eval
                if len(instruction_topics[instruction_id]["text_regex"]) == 0:
                    instruction_topics.pop(instruction_id)
                    updatable_instruction_ids.discard(instruction_id)

            instruction_template.append(instruction_update_ids)
            instruction_text.append(texts)
            instruction_regex.append(list(regexs.values()))
            latest_history_instruction_regex.update(regexs)
            history_instruction_regex.append(list(latest_history_instruction_regex.values()))
            instruction_type.append(type)

            instruction_eval.append(session_eval)
            current_history_eval.update(session_eval)
            history_instruction_eval.append(list(current_history_eval))

        else:
            instruction_template.append([-1])
            instruction_text.append([])
            instruction_regex.append([])
            instruction_type.append([])
            history_instruction_regex.append(list(latest_history_instruction_regex.values()))
            history_instruction_eval.append(list(current_history_eval))
            instruction_eval.append([])

    return (
        instruction_template,
        instruction_type,
        instruction_text,
        instruction_regex,
        history_instruction_regex,
        instruction_eval,
        history_instruction_eval,
    )


def sample_fillers(
    topics,
    n_session,
    max_update_per_filler,
    n_instruction_only_session,
    instruction_positions_instruction_only_sessions,
    filler_instruction_rate,
    filler_instruction_update_rate,
):
    """Sample fillers for a dialogue."""
    fillers = random.choices(topics["fillers"], k=n_session - n_instruction_only_session)
    filler_n_update = {filler["id"]: max_update_per_filler for filler in fillers}
    fillers = {filler["id"]: filler for filler in fillers}
    filler_template = []
    filler_type = []
    filler_text = []
    seen_filler_ids = set()
    fillers_instruction = {fi["id"]: fi for fi in topics["fillers_instruction"]}
    updatable_filler_instruction_ids = set()
    for session_idx in range(n_session):
        seen_fillers_instruction_session = set()
        if session_idx in instruction_positions_instruction_only_sessions:
            filler_template.append(-1)
            filler_text.append(None)
            filler_type.append(None)
        else:
            if random.random() < filler_instruction_rate:
                filler_id = random.choice(list(filler_n_update.keys()))
                filler_template.append(filler_id)
                filler_text.append(fillers[filler_id]["text"])
                filler_n_update[filler_id] -= 1
                if filler_n_update[filler_id] == 0:
                    filler_n_update.pop(filler_id)
                # Get filler type: add or update
                if filler_id in seen_filler_ids:
                    filler_type.append("filler-update")
                else:
                    filler_type.append("filler-add")
                    seen_filler_ids.add(filler_id)
            else:
                insertion_filler_instruction_ids = list(fillers_instruction.keys() - seen_fillers_instruction_session)
                update_filler_instruction_ids = list(
                    updatable_filler_instruction_ids - seen_fillers_instruction_session
                )
                if len(update_filler_instruction_ids) > 0 and random.random() < filler_instruction_update_rate:
                    filler_instruction_id = random.choice(update_filler_instruction_ids)
                    filler_type.append("filler-instruction-update")
                else:
                    filler_instruction_id = random.choice(insertion_filler_instruction_ids)
                    updatable_filler_instruction_ids.add(filler_instruction_id)
                    filler_type.append("filler-instruction-add")
                seen_fillers_instruction_session.add(filler_instruction_id)
                filler_template.append(filler_instruction_id)
                filler_text.append(fillers_instruction[filler_instruction_id]["text"].pop())

                # Remove fillers instruction that cannot be updated anymore and add eval
                if len(fillers_instruction[filler_instruction_id]["text"]) == 0:
                    fillers_instruction.pop(filler_instruction_id)
                    updatable_filler_instruction_ids.discard(filler_instruction_id)
    return filler_template, filler_type, filler_text


if __name__ == "__main__":
    fire.Fire(generate_template)

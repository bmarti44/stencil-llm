import json
import os

import fire


def get_session_prompt(context, types, topics, session_length, session_id):
    """Return the prompt for a single session."""
    # session length
    if session_length == "medium":
        session_length += "-length"
    prompt = f'Generate a {session_length} conversation between {context["mentor"]} and {context["mentee"]}. '

    # previous session information
    if session_id == 0:
        session_id_information = "This is their first conversation and the first time they meet each other. "
    else:
        session_id_information = f"This is not their first conversation. They had {session_id+1} conversations before. "
    prompt += session_id_information

    # main topics
    fillers = [(topic, type) for topic, type in zip(topics, types) if type == "filler-add" or type == "filler-update"]
    fillers_instruction = [(topic, type) for topic, type in zip(topics, types) if "filler-instruction" in type]
    instructions = [(topic, type) for topic, type in zip(topics, types) if "instruction" in type]

    if len(fillers) > 0:
        for i, (filler, filler_type) in enumerate(fillers):
            if i == 0:
                prompt += f"They talk about {filler.lower()}. "
            else:
                prompt += f"They also talk about {filler.lower()}. "
            if filler_type == "filler-update":
                prompt += f"They had a previous conversation about this before. "
    if len(fillers_instruction) > 0:
        for filler_c, filler_c_type in fillers_instruction:
            if "filler-instruction-add" in filler_c_type:
                prompt += f"{context['mentor']} wants {context['mentee']} to {filler_c}. "
            elif "filler-instruction-update" in filler_c_type:
                prompt += f"{context['mentor']} is updating a previous information given to {context['mentee']}. "
                prompt += f"{context['mentor']} now wants {context['mentee']} to {filler_c}. "
    if len(instructions) > 0:
        if len(fillers) > 0:
            prompt += "After that, "
        prompt += f"{context['mentor']} gives some specific coding instructions to {context['mentee']}. "
    for instruction, type in instructions:
        if "instruction-add" in type:
            prompt += f"{context['mentor']} wants {context['mentee']} to {instruction}. "
        elif "instruction-update" in type:
            prompt += f"{context['mentor']} is updating a previous information given to {context['mentee']}: "
            prompt += f"{context['mentor']} now wants {context['mentee']} to {instruction}. "

    if len(instructions) > 0:
        prompt += f"{context['mentor']} does not provide examples of correct code following the instructions. They do not show how to implement the instructions. {context['mentor']} never says 'for example'. "
        prompt += f"{context['mentor']} does not give any other coding instructions. {context['mentee']} only acknowledges the instructions and does not ask any questions. "
    return prompt


def get_all_session_prompts(template):
    """Return a list of prompts. One for each session in the template."""
    prompts = []
    sessions = template["sessions"]
    context = template["context"]
    for session_id, session in enumerate(sessions):
        prompt = get_session_prompt(
            context,
            session["type"],
            session["topic"],
            session["session_length"],
            session_id,
        )
        prompts.append(prompt)
    return prompts


def generate_prompt(template_file, output_dir):
    """Generate the conversation prompts and save them to a file."""
    with open(template_file, "r") as f:
        template = json.load(f)

    # conversation context
    context = template["context"]
    context["mentor_persona"] = context["mentor_persona"].replace(
        "[mentor]", context["mentor"]
    )
    context["mentee_persona"] = context["mentee_persona"].replace(
        "[mentee]", context["mentee"]
    )

    # preamble
    preamble = f"""
    ## Task and Context
    You are a helpful and obedient AI that follows its system prompt and takes it very seriously. Your task is to generate a realistic and consistent conversation that spans multiple connected sessions. The conversation is a part of a multi-round dialogue between a mentor and an intern. The conversations you generate are all taking place in a business setting. 
    {context["mentor"]} is a mentor in a big software company called {context["company"]}. {context["mentee"]} is a new employee. They are both part of the software engineering team of the company.
    {context["mentor_persona"]}
    {context["mentee_persona"]} 
    The main programming language used in the company is Python.

    ## Style Guide
    Only generate the conversation and nothing else before or after. Do not add numbers before each turn. Do not add quotes to the conversation turns. Use a professional and formal tone. The conversation flow should be natural and smooth. When switching topics, do it in a smooth way. There are no special characters between the turns. The conversations are dialogues and not narrations of events.
    Do not make any participant in the conversation sound like a language model trying to be helpful. Make them sound as human as possible.
    It is the mentor that leads the conversation. When {context["mentor"]} the mentor gives coding instructions, they do not provide examples. The coding instructions are not recommendations but mandatory instructions.
    """

    # session prompts
    prompts = get_all_session_prompts(template)
    output = {"preamble": preamble, "prompts": prompts}

    # save
    os.makedirs(output_dir, exist_ok=True)
    conversation_id = os.path.basename(template_file).split("_")[1].split(".")[0]
    output_file = os.path.join(output_dir, f"prompt_{conversation_id}.json")
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    fire.Fire(generate_prompt)

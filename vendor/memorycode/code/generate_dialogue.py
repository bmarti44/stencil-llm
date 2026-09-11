import json
import os

import cohere
import fire
from generation_utils import cohere_model_generate
from tqdm import tqdm


def generate_dialogue_history(prompt_file, template_dir):
    """Generates a dialogue given a prompt then populates the corresponding template dialogue file."""
    with open(prompt_file, "r") as f:
        prompt_data = json.load(f)
    dialogue_id = os.path.basename(prompt_file).split("_")[1].split(".")[0]
    dialogue_file = os.path.join(template_dir, f"dialogue_{dialogue_id}.json")
    assert os.path.exists(dialogue_file), f"Template file {dialogue_file} does not exist!"
    with open(dialogue_file, "r") as f:
        template = json.load(f)

    ### Initialize the Cohere client
    try:
        COHERE_API_KEY = os.environ["COHERE_API_KEY"]
    except KeyError:
        raise ValueError("You need to set the COHERE_API_KEY env variable!")
    client = cohere.Client(COHERE_API_KEY)

    ### Generate dialogue
    preamble = prompt_data["preamble"]
    for session, prompt in tqdm(zip(template["sessions"], prompt_data["prompts"])):
        session_text = cohere_model_generate(
            prompt, client, preamble, model_name="command-r-plus", temperature=0.9, p=0.9
        )
        session["text"] = session_text

    ### save dialogue dataset
    with open(dialogue_file, "w") as f:
        json.dump(template, f, indent=2)


if __name__ == "__main__":
    fire.Fire(generate_dialogue_history)

import os
from functools import partial

import cohere
import torch
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer

MODELS = [
    "gpt-4",
    "gpt-3.5-turbo",
    "command-r-plus",
    "command-r",
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
]


def cohere_model_generate(prompt, client, preamble=None, model_name="command-r-plus", temperature=0.9, p=0.9):
    response = client.chat(
        model=model_name,
        temperature=temperature,
        p=p,
        message=prompt,
        preamble=preamble,
    )
    return response.text


def openai_model_generate(client, prompt, preamble=None, model_name="gpt-4o"):
    messages = [{"role": "user", "content": prompt}]
    if preamble:
        messages.insert(0, {"role": "system", "content": preamble})
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
    )
    return completion.choices[0].message.content


def llama_model_generate(model, tokenizer, prompt, preamble=None, max_tokens=1024):
    messages = [
        {"role": "user", "content": prompt},
    ]
    if preamble:
        messages.insert(0, {"role": "system", "content": preamble})
    input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(
        model.device
    )

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>"),
    ]

    outputs = model.generate(
        input_ids,
        max_new_tokens=max_tokens,
        eos_token_id=terminators,
        do_sample=False,
        temperature=None,
        top_p=None,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = outputs[0][input_ids.shape[-1] :]
    return tokenizer.decode(response, skip_special_tokens=True)


def get_model_generate_function(model_name, temperature=0.9, p=0.9):
    if model_name in ["command-r-plus", "command-r"]:
        try:
            COHERE_API_KEY = os.environ["COHERE_API_KEY"]
        except KeyError:
            raise ValueError("You need to set the COHERE_API_KEY env variable")
        client = cohere.Client(COHERE_API_KEY)

        model_generate = partial(
            cohere_model_generate,
            client=client,
            model_name=model_name,
            temperature=temperature,
            p=p,
        )
    elif model_name in ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]:
        client = OpenAI()
        model_generate = partial(
            openai_model_generate,
            client=client,
            model_name=model_name,
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token_id is not None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
        tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.bfloat16)
        model_generate = partial(
            llama_model_generate,
            model=model,
            tokenizer=tokenizer,
            max_tokens=1024,
        )
    return model_generate


def perform_retrieval(cumulative_sessions, query, num_pivot_sessions):
    try:
        COHERE_API_KEY = os.environ["COHERE_API_KEY"]
    except KeyError:
        raise ValueError("You need to set the COHERE_API_KEY env variable")
    co = cohere.Client(COHERE_API_KEY)
    output = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=cumulative_sessions,
        top_n=num_pivot_sessions,
        return_documents=True,
    )
    # keep the chronological order
    output = [t[1] for t in sorted([(x.index, x.document.text) for x in output.results])]
    output_str = ""
    for session_id, session in enumerate(output):
        output_str += f"\n\n Session {session_id} \n\n" + session
    return output_str

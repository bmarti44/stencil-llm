
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained(sys.argv[1])
model = AutoModelForCausalLM.from_pretrained(sys.argv[1], torch_dtype=torch.bfloat16).cuda().eval()
out = {}
for prompt in json.load(open(sys.argv[2])):
    ids = tok(prompt, return_tensors="pt").input_ids.cuda()
    with torch.no_grad():
        logits = model(ids).logits[0, -1].float().cpu()
    out[prompt] = {"ids": ids[0].tolist(), "logits": logits.tolist()}
torch.save(out, sys.argv[3])

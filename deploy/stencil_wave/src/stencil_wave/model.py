# ruff: noqa: E501
"""WaveModel: HF Qwen3-1.7B + instruction ledger + selective attention amplification."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import torch

from . import salience as _salience
from .attention import WAVE_LAYERS, StepBias, mark_forward, wave_attention
from .controller import CONTROLLER_PATH, WaveController
from .ledger import Entry, Ledger, build_ledger, select

MODEL_ID = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
TRANSFORMERS_PIN = "4.51.0"
CAPTURE_LAYER = 20          # the controller reads the residual stream ENTERING layer 20
EOS_IDS = (151645, 151643)  # <|im_end|>, <|endoftext|> (the model's generation_config)
# the pinned single-turn non-thinking template the research path used (verified bitwise vs HF in B0)
TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


@dataclass
class Generation:
    text: str
    new_ids: list[int]
    prompt_ids: list[int]
    context: str
    ledger: Ledger | None
    truncated: bool

    def __str__(self) -> str:
        return self.text


class WaveModel:
    """One entry point.

        wm = WaveModel.from_pretrained("Qwen/Qwen3-1.7B")
        text = wm.generate(messages, max_new_tokens=512)    # ledger on
        wm.ledger                                            # what was held / selected
        text = wm.generate(messages, ledger=False)           # plain transformers, bitwise
    """

    def __init__(self, model, tokenizer, controller: WaveController, *, dose: float = 3.0,
                 top_k: int = 2, hold: str = "aged", layers=WAVE_LAYERS):
        self.model = model.eval()
        self.tokenizer = tokenizer
        self.controller = controller
        self.dose, self.top_k, self.hold, self.layers = float(dose), int(top_k), hold, tuple(layers)
        self.ledger: Ledger | None = None
        self.last: Generation | None = None
        self._h20: torch.Tensor | None = None
        self._entries: list[Entry] = []
        self._bias: StepBias | None = None
        self._prefill_pending = False
        self._hook = self.model.model.layers[CAPTURE_LAYER].register_forward_pre_hook(self._on_layer20)
        if hold not in ("aged", "all"):
            raise ValueError("hold must be 'aged' (evaluated configuration) or 'all'")

    # ------------------------------------------------------------- loading
    @classmethod
    def from_pretrained(cls, model_id: str = MODEL_ID, *, revision: str | None = REVISION, device=None,
                        torch_dtype=torch.bfloat16, controller_path=CONTROLLER_PATH, **kwargs) -> WaveModel:
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if transformers.__version__ != TRANSFORMERS_PIN:
            warnings.warn(f"stencil_wave was verified against transformers=={TRANSFORMERS_PIN}; "
                          f"you have {transformers.__version__} (parity is not guaranteed)", stacklevel=2)
        if model_id != MODEL_ID:
            warnings.warn(f"stencil_wave's controller and salience were trained for {MODEL_ID} only", stacklevel=2)
        rev = {"revision": revision} if revision and model_id == MODEL_ID else {}
        tok = AutoTokenizer.from_pretrained(model_id, **rev)
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch_dtype, attn_implementation="sdpa",
                                                     **rev, **kwargs)
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        ctrl = WaveController.load(controller_path, device=device)
        return cls(model, tok, ctrl)

    @property
    def device(self):
        return next(self.model.parameters()).device

    # ------------------------------------------------------------- template
    def render(self, messages) -> str:
        """The pinned non-thinking chat template (HF's own, enable_thinking=False)."""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                  enable_thinking=False)

    # ------------------------------------------------------------- hooks
    def _on_layer20(self, module, args):
        mark_forward()
        if not self._prefill_pending:
            return
        self._prefill_pending = False
        h20 = args[0][0].float()               # [P, 2048] residual stream entering layer 20
        self._h20 = h20
        for e in self._entries:
            idx = torch.as_tensor(e.columns, device=h20.device)
            e.key = h20[idx].mean(0)
        held = [e for e in self._entries if e.held]
        chosen = select(held, h20[-1], self.controller, top_k=self.top_k) if held else []
        for e in chosen:
            e.selected = True
        if self._bias is not None:
            self._bias.groups = [e.columns for e in chosen]

    # ------------------------------------------------------------- generate
    def build_ledger(self, context: str, classify=None) -> list[Entry]:
        enc = self.tokenizer(context, return_offsets_mapping=True)
        entries = build_ledger(enc["offset_mapping"], context, classify=classify)
        n_turns = context.count("<|im_start|>user\n")
        for e in entries:
            e.held = e.turn_introduced < n_turns if self.hold == "aged" else True
        return entries

    @torch.no_grad()
    def generate(self, messages, *, max_new_tokens: int = 512, ledger: bool = True, dose: float | None = None,
                 top_k: int | None = None, classify=None, return_generation: bool = False, **gen_kwargs):
        """Greedy generation (do_sample=False) via ``transformers.generate``.

        ledger=False: no hook, no bias, no ledger -> exactly what
        ``model.generate`` produces. ledger=True: instructions in the user
        turns are detected (salience), held (``hold``: 'aged' = stated in an
        EARLIER turn, the evaluated configuration; 'all'), the top-k are
        selected by the controller from the prompt's final layer-20 state,
        and a sustained pre-softmax bias of ``dose`` is applied over their
        key columns at layers 20-27 for every generated token. An empty
        ledger applies no bias and is bitwise the ledger=False path."""
        context = self.render(messages)
        enc = self.tokenizer(context, return_tensors="pt")
        ids = enc["input_ids"].to(self.device)
        if ids.shape[0] != 1:
            raise ValueError("one conversation at a time")
        n_turns = context.count("<|im_start|>user\n")
        common = dict(max_new_tokens=max_new_tokens, do_sample=False, temperature=None, top_p=None, top_k=None,
                      eos_token_id=list(EOS_IDS), pad_token_id=EOS_IDS[1], **gen_kwargs)
        if not ledger:
            self.ledger, self._entries, self._bias, self._prefill_pending = None, [], None, False
            out = self.model.generate(ids, attention_mask=torch.ones_like(ids), **common)
        else:
            dose = self.dose if dose is None else float(dose)
            top_k = self.top_k if top_k is None else int(top_k)
            self._entries = self.build_ledger(context, classify=classify)
            self._bias = StepBias(dose, self.layers)
            self._prefill_pending = True
            with wave_attention(self.model, self._bias):
                out = self.model.generate(ids, attention_mask=torch.ones_like(ids), **common)
            self._prefill_pending = False
            led = Ledger(self._entries, n_turns, self.hold, top_k, dose, self.layers)
            led.active = bool(self._bias.groups) and dose != 0.0
            led.biased_tokens = self._bias.applied_steps
            self.ledger = led
        new_ids = out[0, ids.shape[1]:].tolist()
        truncated = len(new_ids) >= max_new_tokens and (not new_ids or new_ids[-1] not in EOS_IDS)
        text = self.tokenizer.decode(new_ids, skip_special_tokens=True)
        self.last = Generation(text, new_ids, ids[0].tolist(), context, self.ledger, truncated)
        return self.last if return_generation else text

    # ------------------------------------------------------------- misc
    @staticmethod
    def is_instruction(sentence: str) -> bool:
        return _salience.is_instruction(sentence)

    def close(self):
        self._hook.remove()

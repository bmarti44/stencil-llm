"""Hub modeling file for the assistant-memory sentence classifier.

This file is copied verbatim into the published model repository as
``modeling_stencil.py`` and loaded through ``trust_remote_code``. It depends only on
``torch`` and ``transformers``. The registered classifier scores the raw ``[CLS]``
hidden state (no BERT pooler) with a linear head that also receives a one-hot speaker
role; the role part of that head is stored here as a per-role logit bias so that
``logits = W_text @ cls + b + role_bias[role]`` reproduces the original numbers.

Inputs are sentence PAIRS, exactly as registered: ``text`` = the preceding context or
``"(no context)"``, ``text_pair`` = ``"[<role>] <sentence>"``. Labels: rule, fact, none.
"""

from __future__ import annotations

import torch
from transformers import BertConfig, BertModel, BertPreTrainedModel
from transformers.modeling_outputs import SequenceClassifierOutput


class StencilSentenceClassifierConfig(BertConfig):
    model_type = "stencil_sentence_classifier"

    def __init__(self, roles=("user", "assistant"), default_role="user", **kwargs):
        super().__init__(**kwargs)
        self.roles = list(roles)
        self.default_role = default_role


class StencilSentenceClassifier(BertPreTrainedModel):
    config_class = StencilSentenceClassifierConfig

    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config, add_pooling_layer=False)
        self.classifier = torch.nn.Linear(config.hidden_size, config.num_labels)
        self.role_bias = torch.nn.Parameter(
            torch.zeros(len(config.roles), config.num_labels)
        )
        self.post_init()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        token_type_ids=None,
        role_ids=None,
        labels=None,
        **kwargs,
    ):
        hidden = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        ).last_hidden_state[:, 0]
        logits = self.classifier(hidden)
        if role_ids is None:
            role_ids = torch.full(
                (logits.shape[0],),
                self.config.roles.index(self.config.default_role),
                dtype=torch.long,
                device=logits.device,
            )
        logits = logits + self.role_bias[role_ids]
        loss = None
        if labels is not None:
            loss = torch.nn.functional.cross_entropy(logits, labels)
        return SequenceClassifierOutput(loss=loss, logits=logits)

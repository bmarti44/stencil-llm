# ruff: noqa: E501
"""T2 controller-state contenders (PRESS-PLAN t2t3 prereg v3.1; the
architecture table is frozen in WORKLOG before any forward pass on real
data — this module is exercised by synthetic shape tests only until the
bakeoff runs).

Step contract: z_pre = transition(z_prev, D); score from z_pre via
score_aug (null-logit scalar add, query 64-d add); z_next =
write(z_pre, h20, fired_type). State is per-TYPE (3, 8).
"""
import math

import torch

CONTROLLERS = ("osc", "static", "ema", "gru", "nullosc")
NTYPES, SDIM = 3, 8  # 8 real dims per type; for osc: C^4 interleaved Re/Im


class _Base(torch.nn.Module):
    has_input = True

    def __init__(self):
        super().__init__()
        self.W_u = torch.nn.Linear(2048, SDIM) if self.has_input else None
        self.W_z = torch.nn.Linear(NTYPES * SDIM, 1)
        self.W_qz = torch.nn.Linear(NTYPES * SDIM, 64)

    def init_state(self):
        return torch.zeros(NTYPES, SDIM)

    def transition(self, z, D):
        return z

    def write(self, z, h20, type_idx):
        if self.W_u is None:
            return z
        z = z.clone()
        z[type_idx] = z[type_idx] + self.W_u(h20)
        return z

    def score_aug(self, z):
        flat = z.reshape(-1)
        return self.W_z(flat).squeeze(-1), self.W_qz(flat)


class Osc(_Base):
    def __init__(self):
        super().__init__()
        self.r = torch.nn.Parameter(torch.full((NTYPES, SDIM // 2), 2.0))
        self.omega = torch.nn.Parameter(torch.linspace(0.1, 1.0, SDIM // 2).repeat(NTYPES, 1).clone())

    def transition(self, z, D):
        rho = torch.sigmoid(self.r) ** D
        theta = self.omega * D
        re, im = z[:, 0::2], z[:, 1::2]
        c, s = torch.cos(theta), torch.sin(theta)
        out = torch.empty_like(z)
        out[:, 0::2] = rho * (re * c - im * s)
        out[:, 1::2] = rho * (re * s + im * c)
        return out


class Static(_Base):
    def __init__(self):
        super().__init__()
        self.emb = torch.nn.Parameter(torch.zeros(NTYPES, SDIM))

    def init_state(self):
        return self.emb + 0.0  # embeddings ARE the state; no recurrence

    def write(self, z, h20, type_idx):
        # event feature contributes per-event context but is NOT persisted
        z2 = z.clone()
        z2[type_idx] = self.emb[type_idx] + self.W_u(h20)
        return z2


class Ema(_Base):
    def __init__(self):
        super().__init__()
        self.tau = torch.nn.Parameter(torch.full((NTYPES, SDIM), math.log(0.1 / 0.9)))

    def write(self, z, h20, type_idx):
        a = torch.sigmoid(self.tau[type_idx])
        z = z.clone()
        z[type_idx] = (1 - a) * z[type_idx] + a * self.W_u(h20)
        return z


class Gru(_Base):
    def __init__(self):
        super().__init__()
        self.cell = torch.nn.GRUCell(SDIM, SDIM)

    def write(self, z, h20, type_idx):
        z = z.clone()
        z[type_idx] = self.cell(self.W_u(h20)[None], z[type_idx][None])[0]
        return z


class NullOsc(_Base):
    has_input = False

    def __init__(self):
        super().__init__()
        self.register_buffer("omega_fixed", torch.linspace(0.1, 1.0, SDIM // 2).repeat(NTYPES, 1).clone())

    def init_state(self):
        z = torch.zeros(NTYPES, SDIM)
        z[:, 0::2] = 1.0  # unit phasor, free-running
        return z

    def transition(self, z, D):
        theta = self.omega_fixed * D
        re, im = z[:, 0::2], z[:, 1::2]
        c, s = torch.cos(theta), torch.sin(theta)
        out = torch.empty_like(z)
        out[:, 0::2] = re * c - im * s
        out[:, 1::2] = re * s + im * c
        return out


def make_controller(name: str) -> _Base:
    return {"osc": Osc, "static": Static, "ema": Ema, "gru": Gru, "nullosc": NullOsc}[name]()

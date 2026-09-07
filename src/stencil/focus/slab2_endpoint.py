"""Amendment 4: episode-paired change adherence and DEV eligibility.

No model, data, or file access at import. Callers supply schedules and saved rows.
Historical final-success tests in slab2 are not used by this endpoint.
"""

from fractions import Fraction
from math import comb, isfinite

from . import slab2 as s

FAMILIES = {"indent": "style", "format": "format", "delivery": "process"}
ARMS = "QRNT"


def change_rounds(episode):
    """First applicable round per effective change, never execution-selected."""
    result = {k: [] for k in FAMILIES}
    for key in FAMILIES:
        changes = [
            t.index
            for t in episode.turns
            if any(
                e.key == key
                and e.action in {"supersedes", "completes", "cancels", "reinstates"}
                for e in t.events
            )
        ]
        if not changes:
            continue
        for start, end in zip(changes, changes[1:] + [len(episode.turns)], strict=True):
            for t in episode.turns[start:end]:
                live = dict(t.live)
                applicable = (
                    key == "indent"
                    or key == "format"
                    and live["format"] == "compact"
                    or key == "delivery"
                    and live["format"] == "verbose"
                    and "delivery" in live
                )
                if applicable:
                    result[key].append(t.index)
                    break
    return result


def _sign(pairs):
    gains = [r - n for r, n in pairs]
    wins, losses = sum(g > 0 for g in gains), sum(g < 0 for g in gains)
    d = wins + losses
    return dict(
        n=len(pairs),
        wins=wins,
        losses=losses,
        ties=len(pairs) - d,
        p=sum(comb(d, j) for j in range(wins, d + 1)) / 2**d,
        mean_gain=float(sum(gains) / len(gains)) if gains else None,
    )


def primary(records, episodes):
    """One sign per episode/family; Holm over all three predeclared families."""
    index = {(r["episode_id"], r["arm"], r["turn"]): r for r in records}
    if len(index) != len(records):
        raise ValueError("duplicate episode/arm/turn")
    schedules = {e.episode_id: change_rounds(e) for e in episodes}
    if len(schedules) != len(episodes) or not episodes:
        raise ValueError("nonempty unique episode schedules required")
    families = {}
    for key, family in FAMILIES.items():
        paired, strict, details = [], [], []
        for episode_id, schedule in schedules.items():
            counts = {a: 0 for a in ARMS}
            denominators = {a: 0 for a in ARMS}
            common = []
            strict_events = []
            missing = []
            for turn in schedule[key]:
                rows = {a: index.get((episode_id, a, turn)) for a in ARMS}
                written = {a: bool(r and s.file_written(r)) for a, r in rows.items()}
                values = {
                    a: int(written[a] and r["outcome"]["satisfied"][key])
                    for a, r in rows.items()
                }
                for a in ARMS:
                    counts[a] += values[a]
                    denominators[a] += written[a]
                if written["R"] and written["N"]:
                    common.append((values["R"], values["N"]))
                else:
                    missing.append(turn)
                strict_events.append((values["R"], values["N"]))
            if common:
                paired.append(
                    tuple(
                        Fraction(sum(v[i] for v in common), len(common)) for i in (0, 1)
                    )
                )
            if strict_events:
                strict.append(
                    tuple(
                        Fraction(sum(v[i] for v in strict_events), len(strict_events))
                        for i in (0, 1)
                    )
                )
            details.append(
                dict(
                    episode_id=episode_id,
                    change_rounds=schedule[key],
                    satisfied=counts,
                    written_denominators=denominators,
                    paired_denominator=len(common),
                    missing_paired_rounds=missing,
                )
            )
        families[key] = dict(
            family=family,
            **_sign(paired),
            strict_failed_attempts=_sign(strict),
            episodes=details,
        )
    adjusted = 0.0
    for rank, key in enumerate(sorted(FAMILIES, key=lambda k: families[k]["p"])):
        f = families[key]
        adjusted = max(adjusted, min(1.0, (len(FAMILIES) - rank) * f["p"]))
        f["holm_p"] = adjusted
        f["pass"] = bool(f["n"] and f["mean_gain"] > 0 and adjusted <= 0.05)
    return dict(
        endpoint="per-obligation change-round adherence",
        unit="episode",
        alternative="R>N",
        families=families,
        primary_evidence=any(f["pass"] for f in families.values()),
        computable_families=sum(f["n"] >= 6 for f in families.values()),
        computable_episodes=sum(
            sum(f["episodes"][i]["paired_denominator"] > 0 for f in families.values())
            >= 2
            for i in range(len(episodes))
        ),
    )


def projection(lane_seconds, load_seconds):
    if (
        set(lane_seconds) != set(ARMS)
        or any(not isfinite(v) or v <= 0 for v in lane_seconds.values())
        or not isfinite(load_seconds)
        or load_seconds < 0
    ):
        raise ValueError("finite measured Q/R/N/T costs and startup required")
    return (
        load_seconds
        + 1.25 * (64 * sum(lane_seconds[a] for a in "RNQ") + 16 * lane_seconds["T"])
    ) / 3600


def strict_floor(records):
    rows = []
    for r in records:
        if r["arm"] == "T":
            rows.append(
                {**r, "outcome": {**r["outcome"], "observed": s.file_written(r)}}
            )
    return s.freeze_t_floor(rows)


def pilot_reading(records, episodes, floor, hours, compact_cells, *, deterministic):
    expected = {
        (e.episode_id, a, t.index) for e in episodes for a in ARMS for t in e.turns
    }
    actual = {(r["episode_id"], r["arm"], r["turn"]) for r in records}
    complete = actual == expected and len(records) == len(expected) == 512
    failures = []
    metrics = s.execution_summary(records, ARMS)
    for a, m in metrics.items():
        if m["round0_executing_lanes"] != 8:
            failures.append(a + " round0 nonwrite")
        if m["executing_lanes"] != 8:
            failures.append(a + " lanes<8/8")
        if m["executed_rounds"] < 0.9 * 128:
            failures.append(a + " rounds<90%")
        if m["caps"] > 0.02 * 128:
            failures.append(a + " caps>2%")
    if not deterministic:
        failures.append("determinism")
    if any(r["prompt_tokens"] + s.REPLY_CAP > 32768 for r in records):
        failures.append("context")
    kinds = [
        k
        for k in ("indent", "delivery")
        if floor
        and floor["traits"][k]["eligible"]
        and len(floor["traits"][k]["opportunity_episodes"]) >= 2
    ]
    if len(kinds) < 2:
        failures.append("T floor substitution kinds<2")
    if len(set(compact_cells)) != 34:
        raise ValueError("fixed 34-cell control required")
    selected = [
        r
        for r in records
        if r["arm"] == "R" and (r["episode_id"], r["turn"]) in compact_cells
    ]
    emissions = sum("delivery=ready" in r["output"] for r in selected)
    adherence = sum(
        s.file_written(r) and r["outcome"]["satisfied"]["format"] for r in selected
    )
    if len(selected) != 34 or emissions > 2:
        failures.append("compact delivery=ready>2/34 or missing")
    if adherence < 26:
        failures.append("compact format<26/34")
    endpoint = primary(records, episodes)
    if endpoint["computable_families"] < 2 or endpoint["computable_episodes"] < 6:
        failures.append("primary denominators<2 obligations in >=6 episodes")
    if hours is None or not isfinite(hours) or not 0 < hours <= 12:
        failures.append("projection unmeasured or >12h")
    return dict(
        reading="INCOMPLETE"
        if not complete
        else "INELIGIBLE"
        if failures
        else "ELIGIBLE",
        failures=failures,
        per_arm=metrics,
        primary=endpoint,
        compact_control=dict(
            total=len(selected), ready_emissions=emissions, format_adherence=adherence
        ),
        projected_gpu_hours=hours,
        floor=floor,
    )

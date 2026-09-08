def as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def compact_cue(payload):
    if not isinstance(payload, list):
        return "invalid"
    
    runs = []
    for sample in payload:
        if not isinstance(sample, int):
            return "invalid"
    
    if not payload:
        return []
    
    current_level = payload[0]
    count = 1
    
    for level in payload[1:]:
        if level == current_level:
            count += 1
        else:
            runs.append([current_level, count])
            current_level = level
            count = 1
    runs.append([current_level, count])
    
    return runs


def schedule_cues(payload):
    if isinstance(payload, dict):
        if "cues" not in payload or "gap" not in payload:
            return "invalid"
        if not isinstance(payload["gap"], int) or payload["gap"] < 0:
            return "invalid"
        payload = payload["cues"]
    elif not isinstance(payload, list):
        return "invalid"
    
    for cue in payload:
        if not isinstance(cue, dict):
            return "invalid"
        if "id" not in cue or not isinstance(cue["id"], str):
            return "invalid"
        if "at" not in cue or not isinstance(cue["at"], int) or cue["at"] < 0:
            return "invalid"
        if "dur" not in cue or not isinstance(cue["dur"], int) or cue["dur"] < 1:
            return "invalid"
    
    if not payload:
        return []
    
    # Sort cues by requested start time, then by duration (longest first) for ties
    sorted_cues = sorted(payload, key=lambda x: (x["at"], -x["dur"], payload.index(x)))
    
    placements = []
    current_time = 0
    
    for cue in sorted_cues:
        start = max(current_time, cue["at"])
        end = start + cue["dur"]
        placements.append({"id": cue["id"], "start": start, "end": end})
        current_time = end
    
    return placements


def render_timeline(payload):
    return None

def as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def compact_cue(payload):
    if isinstance(payload, dict):
        if "samples" not in payload:
            return "invalid"
        if "tol" not in payload:
            return "invalid"
        if not isinstance(payload["tol"], int) or payload["tol"] < 0:
            return "invalid"
        payload = payload["samples"]
    
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
        if abs(level - current_level) <= payload.get("tol", 0):
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
    if not isinstance(payload, dict):
        return "invalid"
    
    # Check for "tol" and "gap" parameters
    tol = payload.get("tol")
    gap = payload.get("gap")
    detail = payload.get("detail")
    
    # Validate "tol" if present
    if "tol" in payload:
        if not isinstance(tol, int) or tol < 0:
            return "invalid"
    
    # Validate "gap" if present
    if "gap" in payload:
        if not isinstance(gap, int) or gap < 0:
            return "invalid"
    
    # Validate "detail" if present
    if "detail" in payload:
        if not isinstance(detail, bool):
            return "invalid"
    
    # Extract samples and cues
    if "samples" not in payload or "cues" not in payload:
        return "invalid"
    
    samples = payload["samples"]
    cues = payload["cues"]
    
    # Compact the samples with tolerance if specified
    if "tol" in payload:
        # Create a temporary payload with "samples" and "tol"
        temp_samples_payload = {"samples": samples, "tol": tol}
        runs = compact_cue(temp_samples_payload)
    else:
        runs = compact_cue(samples)
    
    if runs == "invalid":
        return "invalid"
    
    # Schedule the cues with gap if specified
    if "gap" in payload:
        # Create a temporary payload with "cues" and "gap"
        temp_cues_payload = {"cues": cues, "gap": gap}
        plan = schedule_cues(temp_cues_payload)
    else:
        plan = schedule_cues(cues)
    
    if plan == "invalid":
        return "invalid"
    
    # Handle the "detail" parameter
    if detail is True:
        # Sort cues by requested start time, preserving original order for ties
        sorted_cues = sorted(cues, key=lambda x: (x["at"], cues.index(x)))
        cue_ids = [cue["id"] for cue in sorted_cues]
        
        return {
            "version": 1,
            "runs": runs,
            "plan": plan,
            "order": cue_ids
        }
    else:
        return [runs, plan]
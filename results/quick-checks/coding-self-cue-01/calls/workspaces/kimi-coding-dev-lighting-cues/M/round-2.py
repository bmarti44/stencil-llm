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
    previous_value = None
    count = 0
    
    for value in payload:
        if not isinstance(value, int):
            return "invalid"
        
        if value == previous_value:
            count += 1
        else:
            if previous_value is not None:
                runs.append([previous_value, count])
            previous_value = value
            count = 1
    
    if previous_value is not None:
        runs.append([previous_value, count])
    
    return runs


def schedule_cues(payload):
    if isinstance(payload, dict):
        if "cues" not in payload or "gap" not in payload:
            return "invalid"
        
        gap = payload["gap"]
        if not isinstance(gap, int) or gap < 0:
            return "invalid"
        
        payload = payload["cues"]
    
    if not isinstance(payload, list):
        return "invalid"
    
    # Validate each cue and extract necessary information
    cues = []
    for item in payload:
        if not isinstance(item, dict):
            return "invalid"
        
        if "id" not in item or "at" not in item or "dur" not in item:
            return "invalid"
        
        cue_id = item["id"]
        at = item["at"]
        dur = item["dur"]
        
        # Check if at and dur are integers and meet the requirements
        if not isinstance(at, int) or at < 0:
            return "invalid"
        if not isinstance(dur, int) or dur < 1:
            return "invalid"
        
        cues.append({"id": cue_id, "at": at, "dur": dur})
    
    # Sort cues by requested start time, with tie-breaker: longest duration first
    # For cues with same "at", sort by -dur (so longer durations come first)
    # For cues with same "at" and "dur", preserve input order
    cues.sort(key=lambda x: (x["at"], -x["dur"]))
    
    placements = []
    current_time = 0
    
    for cue in cues:
        # Calculate the earliest possible start time for this cue
        start = max(current_time, cue["at"])
        end = start + cue["dur"]
        
        placements.append({"id": cue["id"], "start": start, "end": end})
        current_time = end
    
    return placements


def render_timeline(payload):
    return None

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
    return None


def render_timeline(payload):
    return None

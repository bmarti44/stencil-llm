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
    return None


def render_timeline(payload):
    return None

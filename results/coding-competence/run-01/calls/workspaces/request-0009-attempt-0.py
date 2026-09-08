def normalize_segment(segment):
    """Validate and canonicalize one route segment dict.

    Valid segments are dicts with exactly the keys mode, origin, dest,
    minutes and fare_cents. mode is one of walk, bus or rail. origin and
    dest are three-letter alphabetic strings and must differ. minutes is
    an integer (not a boolean) from 1 to 600 inclusive. fare_cents is an
    integer (not a boolean) from 0 to 100000 inclusive; walk segments
    must have fare_cents 0. Returns the canonical dict with codes
    uppercased, or None for anything invalid.
    """
    if not isinstance(segment, dict):
        return None
    if set(segment.keys()) != {"mode", "origin", "dest", "minutes", "fare_cents"}:
        return None
    mode = segment["mode"]
    if mode not in ("walk", "bus", "rail"):
        return None
    origin = segment["origin"]
    dest = segment["dest"]
    for code in (origin, dest):
        if not isinstance(code, str) or len(code) != 3 or not code.isalpha():
            return None
    if origin.upper() == dest.upper():
        return None
    minutes = segment["minutes"]
    if isinstance(minutes, bool) or not isinstance(minutes, int):
        return None
    if minutes < 1 or minutes > 600:
        return None
    fare_cents = segment["fare_cents"]
    if isinstance(fare_cents, bool) or not isinstance(fare_cents, int):
        return None
    if fare_cents < 0 or fare_cents > 100000:
        return None
    if mode == "walk" and fare_cents != 0:
        return None
    return {
        "mode": mode,
        "origin": origin.upper(),
        "dest": dest.upper(),
        "minutes": minutes,
        "fare_cents": fare_cents,
    }


def price_segment(segment):
    normalized = normalize_segment(segment)
    if normalized is None:
        return None
    mode = normalized['mode']
    origin = normalized['origin']
    dest = normalized['dest']
    minutes = normalized['minutes']
    fare_cents = normalized['fare_cents']
    
    if mode == 'walk':
        base = 0
        rate = 0
    elif mode == 'bus':
        base = 140
        rate = 12
    elif mode == 'rail':
        base = 320
        rate = 25
    else:
        return None
    
    raw = fare_cents + base + rate * minutes
    if minutes >= 60:
        raw = raw * 0.9
    
    # Round to nearest cent, with half-up rounding
    quote_cents = int(raw + 0.5)
    
    return {
        'mode': mode,
        'origin': origin,
        'dest': dest,
        'minutes': minutes,
        'quote_cents': quote_cents
    }


def combine_segments(segments):
    return None


def build_itinerary(request):
    return None

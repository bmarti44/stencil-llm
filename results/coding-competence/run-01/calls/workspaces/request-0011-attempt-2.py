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
    if not isinstance(segments, list) or len(segments) == 0:
        return None
    normalized_segments = []
    for segment in segments:
        normalized = normalize_segment(segment)
        if normalized is None:
            return None
        normalized_segments.append(normalized)
    
    merged_legs = []
    current_leg = normalized_segments[0]
    
    for i in range(1, len(normalized_segments)):
        next_leg = normalized_segments[i]
        if (current_leg['mode'] == next_leg['mode'] and 
            current_leg['dest'] == next_leg['origin']):
            # Merge legs
            current_leg['dest'] = next_leg['dest']
            current_leg['minutes'] += next_leg['minutes']
            current_leg['fare_cents'] += next_leg['fare_cents']
        else:
            merged_legs.append(current_leg)
            current_leg = next_leg
    merged_legs.append(current_leg)
    
    leg_count = len(merged_legs)
    total_minutes = sum(leg['minutes'] for leg in merged_legs)
    total_fare_cents = sum(leg['fare_cents'] for leg in merged_legs)
    
    return {
        'legs': merged_legs,
        'leg_count': leg_count,
        'total_minutes': total_minutes,
        'total_fare_cents': total_fare_cents
    }


def build_itinerary(request):
    if not isinstance(request, dict) or set(request.keys()) != {"traveler", "segments"}:
        return None
    traveler = request["traveler"]
    if not isinstance(traveler, str) or len(traveler.strip()) == 0:
        return None
    segments = request["segments"]
    
    combined = combine_segments(segments)
    if combined is None:
        return None
    
    # Fold legs across modes
    folded_legs = []
    for leg in combined["legs"]:
        if not folded_legs:
            folded_legs.append(leg)
        else:
            last = folded_legs[-1]
            if last["dest"] == leg["origin"]:
                # Merge legs
                new_leg = {
                    "mode": last["mode"],
                    "origin": last["origin"],
                    "dest": leg["dest"],
                    "minutes": last["minutes"] + leg["minutes"] + (7 if last["mode"] != leg["mode"] else 0),
                    "fare_cents": last["fare_cents"] + leg["fare_cents"]
                }
                folded_legs[-1] = new_leg
            else:
                folded_legs.append(leg)
    
    # Price each leg
    priced_legs = []
    for leg in folded_legs:
        priced = price_segment(leg)
        if priced is None:
            return None
        priced_legs.append(priced)
    
    total_minutes = sum(leg["minutes"] for leg in priced_legs)
    quote_cents = sum(leg["quote_cents"] for leg in priced_legs)
    
    return {
        "traveler": traveler,
        "leg_count": len(priced_legs),
        "legs": priced_legs,
        "total_minutes": total_minutes,
        "quote_cents": quote_cents
    }
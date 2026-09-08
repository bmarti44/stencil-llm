"""Small audio playlist preparation utilities (JSON values in, JSON values out)."""


def parse_track(entry):
    if not isinstance(entry, dict):
        return {"ok": False, "error": "entry must be an object"}
    required = ["title", "artist", "seconds", "explicit"]
    for key in sorted(entry):
        if key not in required:
            return {"ok": False, "error": "unexpected key '" + str(key) + "'"}
    for key in required:
        if key not in entry:
            return {"ok": False, "error": "missing key '" + key + "'"}
    title = entry["title"]
    if not isinstance(title, str):
        return {"ok": False, "error": "'title' must be a string"}
    clean_title = " ".join(title.split())
    if clean_title == "":
        return {"ok": False, "error": "'title' must not be blank"}
    artist = entry["artist"]
    if not isinstance(artist, str):
        return {"ok": False, "error": "'artist' must be a string"}
    clean_artist = " ".join(artist.split())
    if clean_artist == "":
        return {"ok": False, "error": "'artist' must not be blank"}
    seconds = entry["seconds"]
    if isinstance(seconds, bool) or not isinstance(seconds, int):
        return {"ok": False, "error": "'seconds' must be an integer"}
    if seconds < 1:
        return {"ok": False, "error": "'seconds' must be at least 1"}
    explicit = entry["explicit"]
    if not isinstance(explicit, bool):
        return {"ok": False, "error": "'explicit' must be a boolean"}
    return {"ok": True, "track": {"title": clean_title, "artist": clean_artist, "seconds": seconds, "explicit": explicit}}


def format_clock(total_seconds):
    if isinstance(total_seconds, bool) or not isinstance(total_seconds, int):
        return None
    if total_seconds < 0:
        return None
    minutes = total_seconds // 60
    seconds = total_seconds - minutes * 60
    if seconds < 10:
        sec_text = "0" + str(seconds)
    else:
        sec_text = str(seconds)
    return str(minutes) + ":" + sec_text


def normalize_tracklist(payload):
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "error": "payload must be an object with a 'tracks' list"
        }
    
    # Check for unrecognized keys
    recognized_keys = {"tracks", "allow_duplicates"}
    payload_keys = sorted(payload.keys())
    for key in payload_keys:
        if key not in recognized_keys:
            return {
                "ok": False,
                "error": f"unexpected key '{key}'"
            }
    
    # Check 'tracks' presence and type
    if "tracks" not in payload or not isinstance(payload["tracks"], list):
        return {
            "ok": False,
            "error": "payload must be an object with a 'tracks' list"
        }
    
    # Check 'allow_duplicates' if present
    allow_duplicates = payload.get("allow_duplicates", False)
    if "allow_duplicates" in payload:
        if not isinstance(allow_duplicates, bool):
            return {
                "ok": False,
                "error": "'allow_duplicates' must be a boolean when present"
            }
    
    tracks = payload["tracks"]
    validated_tracks = []
    
    # Validate each track
    for i, entry in enumerate(tracks):
        result = parse_track(entry)
        if not result["ok"]:
            return {
                "ok": False,
                "error": f"track {i+1}: {result["error"]}"
            }
        validated_tracks.append(result["track"])
    
    # Check for duplicates
    seen = {}
    for i, track in enumerate(validated_tracks):
        key = (track["artist"].lower(), track["title"].lower())
        if key in seen:
            return {
                "ok": False,
                "error": f"duplicate track {i+1}"
            }
        seen[key] = i+1
    
    # Prepare output
    total_seconds = sum(track["seconds"] for track in validated_tracks)
    total_clock = format_clock(total_seconds)
    
    # Assign IDs and format clock for each track
    result_tracks = []
    for idx, track in enumerate(validated_tracks):
        track_id = f"T{idx+1:02d}"
        clock = format_clock(track["seconds"])
        result_tracks.append({
            "id": track_id,
            "title": track["title"],
            "artist": track["artist"],
            "seconds": track["seconds"],
            "explicit": track["explicit"],
            "clock": clock
        })
    
    return {
        "ok": True,
        "count": len(result_tracks),
        "total_seconds": total_seconds,
        "total_clock": total_clock,
        "tracks": result_tracks
    }


def sequence_playlist(payload):
    if not isinstance(payload, dict):
        return normalize_tracklist(payload)
    
    # Check for unrecognized keys
    recognized_keys = {"tracks", "order", "allow_duplicates"}
    payload_keys = sorted(payload.keys())
    for key in payload_keys:
        if key not in recognized_keys:
            return {
                "ok": False,
                "error": f"unexpected key '{key}'"
            }
    
    # Validate 'order' key
    order = payload.get("order", "artist")
    if order not in {"artist", "duration"}:
        return {
            "ok": False,
            "error": "'order' must be 'artist' or 'duration'"
        }
    
    # Prepare payload for normalize_tracklist
    normalize_payload = {"tracks": payload["tracks"]}
    if "allow_duplicates" in payload:
        normalize_payload["allow_duplicates"] = payload["allow_duplicates"]
    
    # Call normalize_tracklist
    normalize_result = normalize_tracklist(normalize_payload)
    if not normalize_result["ok"]:
        return normalize_result
    
    # Sort tracks
    tracks = normalize_result["tracks"]
    if order == "artist":
        # Sort by artist case-insensitively, preserving original order for ties
        tracks.sort(key=lambda x: x["artist"].lower())
    else:  # order == "duration"
        # Sort by seconds, preserving original order for ties
        tracks.sort(key=lambda x: x["seconds"])
    
    return {
        "ok": True,
        "order": order,
        "count": normalize_result["count"],
        "total_seconds": normalize_result["total_seconds"],
        "tracks": tracks
    }


def build_manifest(payload):
    return None
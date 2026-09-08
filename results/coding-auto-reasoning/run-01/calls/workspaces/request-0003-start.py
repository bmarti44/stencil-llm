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
    return None


def sequence_playlist(payload):
    return None


def build_manifest(payload):
    return None
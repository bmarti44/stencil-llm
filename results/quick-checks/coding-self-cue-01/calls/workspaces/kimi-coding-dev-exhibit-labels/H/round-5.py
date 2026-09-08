"""Museum exhibit label assembly pipeline (development build)."""


def _clean_token(token):
    text = token.strip()
    while text and not text[0].isalnum():
        text = text[1:]
    while text and not text[-1].isalnum():
        text = text[:-1]
    return text.lower()


def label_title(record):
    if not isinstance(record, dict):
        return {"status": "error", "detail": "bad-input"}
    
    if "name" not in record or not isinstance(record["name"], str):
        return {"status": "error", "detail": "bad-input"}
    
    name = record["name"]
    name_tokens = [token for token in name.split() if _clean_token(token)]
    if not name_tokens:
        return {"status": "error", "detail": "bad-input"}
    
    # Process name
    cleaned_name = " ".join([_clean_token(token).capitalize() for token in name.split()])
    
    # Check for subtitle
    if "subtitle" in record:
        subtitle = record["subtitle"]
        if not isinstance(subtitle, str):
            return {"status": "error", "detail": "bad-input"}
        
        subtitle_tokens = [token for token in subtitle.split() if _clean_token(token)]
        if subtitle_tokens:
            cleaned_subtitle = " ".join([_clean_token(token).capitalize() for token in subtitle.split()])
            cleaned_name += f": {cleaned_subtitle}"
    
    return cleaned_name


def index_entry(record):
    if not isinstance(record, dict):
        return {"status": "error", "detail": "bad-input"}
    
    if "number" not in record or "tags" not in record:
        return {"status": "error", "detail": "bad-input"}
    
    number = record["number"]
    tags = record["tags"]
    
    if not isinstance(number, int) or number < 0:
        return {"status": "error", "detail": "bad-input"}
    
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        return {"status": "error", "detail": "bad-input"}
    
    # Check for room
    if "room" in record:
        room = record["room"]
        if not isinstance(room, str):
            return {"status": "error", "detail": "bad-input"}
        
        room_tokens = [token for token in room.split() if _clean_token(token)]
        if not room_tokens:
            return {"status": "error", "detail": "bad-input"}
    
    cleaned_tags = []
    for tag in tags:
        cleaned = _clean_token(tag)
        if cleaned:
            cleaned_tags.append(cleaned)
    
    if not cleaned_tags:
        result = f"{number:03d}"
    else:
        # Sort by length, stable sort
        cleaned_tags.sort(key=lambda x: len(x))
        tag_str = ", ".join(cleaned_tags)
        result = f"{number:03d}: {tag_str}"
    
    # Add room information if present
    if "room" in record:
        room = record["room"]
        room_tokens = [token for token in room.split() if _clean_token(token)]
        cleaned_room = " ".join([_clean_token(token).capitalize() for token in room.split()])
        result += f" ({cleaned_room})"
    
    return result


def label_full(record):
    if not isinstance(record, dict):
        return None
    
    # Check for name validity
    if "name" not in record or not isinstance(record["name"], str):
        return None
    
    name = record["name"]
    name_tokens = [token for token in name.split() if _clean_token(token)]
    if not name_tokens:
        return None
    
    # Check for artist validity
    if "artist" not in record or not isinstance(record["artist"], str):
        return None
    
    artist = record["artist"]
    artist_tokens = [token for token in artist.split() if _clean_token(token)]
    if not artist_tokens:
        return None
    
    # Check for year validity
    if "year" not in record or not isinstance(record["year"], int) or record["year"] <= 0:
        return None
    
    # Check for number and tags validity
    if "number" in record or "tags" in record:
        if "number" not in record or "tags" not in record:
            return None
        
        number = record["number"]
        tags = record["tags"]
        
        if not isinstance(number, int) or number < 0:
            return None
        
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            return None
    
    # Process name
    cleaned_name = " ".join([_clean_token(token).capitalize() for token in name.split()])
    
    # Process artist
    cleaned_artist = " ".join([_clean_token(token).capitalize() for token in artist.split()])
    
    # Build result
    result = [cleaned_name, f"by {cleaned_artist}", str(record["year"])]
    
    # Add index entry if number and tags are present
    if "number" in record and "tags" in record:
        number = record["number"]
        tags = record["tags"]
        
        # Validate number and tags again for index_entry
        if not isinstance(number, int) or number < 0:
            return None
        
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            return None
        
        # Call index_entry to get the index part
        index_part = index_entry(record)
        if isinstance(index_part, dict) and index_part["status"] == "error":
            return None
        
        result.append(f"index {index_part}")
    
    return result
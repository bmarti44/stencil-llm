"""Museum exhibit label assembly pipeline (development build)."""


def _clean_token(token):
    text = token.strip()
    while text and not text[0].isalnum():
        text = text[1:]
    while text and not text[-1].isalnum():
        text = text[:-1]
    return text.lower()


def label_title(record):
    return None


def index_entry(record):
    if not isinstance(record, dict):
        return "ERR"
    
    if "number" not in record or "tags" not in record:
        return "ERR"
    
    number = record["number"]
    tags = record["tags"]
    
    if not isinstance(number, int) or number < 0:
        return "ERR"
    
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        return "ERR"
    
    cleaned_tags = []
    for tag in tags:
        cleaned = _clean_token(tag)
        if cleaned:
            cleaned_tags.append(cleaned)
    
    if not cleaned_tags:
        return f"{number:03d}"
    
    # Sort by length, stable sort
    cleaned_tags.sort(key=lambda x: len(x))
    
    tag_str = ", ".join(cleaned_tags)
    return f"{number:03d}: {tag_str}"


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
    
    # Process name
    cleaned_name = " ".join([_clean_token(token).capitalize() for token in name.split()])
    
    # Process artist
    cleaned_artist = " ".join([_clean_token(token).capitalize() for token in artist.split()])
    
    # Return the result
    return [cleaned_name, f"by {cleaned_artist}", str(record["year"])]
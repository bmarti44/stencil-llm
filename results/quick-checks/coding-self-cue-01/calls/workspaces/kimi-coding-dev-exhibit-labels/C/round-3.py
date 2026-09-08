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
    
    # Check for 'name' and validate it
    if 'name' not in record or not isinstance(record['name'], str):
        return {"status": "error", "detail": "bad-input"}
    
    name = record['name']
    name_tokens = [token for token in name.split() if _clean_token(token)]
    if not name_tokens:
        return {"status": "error", "detail": "bad-input"}
    
    # Capitalize and join name tokens
    cleaned_name = ' '.join([_clean_token(token).capitalize() for token in name.split()])
    
    # Check for 'subtitle' if present
    if 'subtitle' in record:
        subtitle = record['subtitle']
        if not isinstance(subtitle, str):
            return {"status": "error", "detail": "bad-input"}
        
        subtitle_tokens = [token for token in subtitle.split() if _clean_token(token)]
        if subtitle_tokens:
            cleaned_subtitle = ' '.join([_clean_token(token).capitalize() for token in subtitle.split()])
            cleaned_name += f': {cleaned_subtitle}'
    
    return cleaned_name


def index_entry(record):
    if not isinstance(record, dict):
        return 'ERR'
    
    if 'number' not in record or 'tags' not in record:
        return 'ERR'
    
    number = record['number']
    tags = record['tags']
    
    if not isinstance(number, int) or number < 0:
        return 'ERR'
    
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        return 'ERR'
    
    cleaned_tags = []
    for tag in tags:
        cleaned = _clean_token(tag)
        if cleaned:
            cleaned_tags.append(cleaned)
    
    # Sort by length, then by original order (stable sort)
    cleaned_tags.sort(key=lambda x: len(x))
    
    number_str = f"{number:03d}"
    
    if not cleaned_tags:
        return number_str
    
    tags_str = ', '.join(cleaned_tags)
    return f"{number_str}: {tags_str}"


def label_full(record):
    if not isinstance(record, dict):
        return None
    
    # Check for 'name' and validate it
    if 'name' not in record or not isinstance(record['name'], str):
        return None
    
    name = record['name']
    name_tokens = [token for token in name.split() if _clean_token(token)]
    if not name_tokens:
        return None
    
    # Capitalize and join name tokens
    cleaned_name = ' '.join([_clean_token(token).capitalize() for token in name.split()])
    
    # Check for 'artist' and validate it
    if 'artist' not in record or not isinstance(record['artist'], str):
        return None
    
    artist = record['artist']
    artist_tokens = [token for token in artist.split() if _clean_token(token)]
    if not artist_tokens:
        return None
    
    # Capitalize and join artist tokens
    cleaned_artist = ' '.join([_clean_token(token).capitalize() for token in artist.split()])
    
    # Check for 'year' and validate it
    if 'year' not in record or not isinstance(record['year'], int) or record['year'] <= 0:
        return None
    
    year = record['year']
    
    return [cleaned_name, f"by {cleaned_artist}", str(year)]
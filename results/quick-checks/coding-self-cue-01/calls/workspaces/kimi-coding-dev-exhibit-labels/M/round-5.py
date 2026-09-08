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
        return None
    if 'name' not in record or not isinstance(record['name'], str):
        return None
    tokens = record['name'].split()
    cleaned_tokens = [_clean_token(token) for token in tokens]
    if not cleaned_tokens or all(token == '' for token in cleaned_tokens):
        return None
    
    title = ' '.join(token.capitalize() for token in cleaned_tokens)
    
    if 'subtitle' in record:
        if not isinstance(record['subtitle'], str):
            return None
        subtitle_tokens = record['subtitle'].split()
        cleaned_subtitle_tokens = [_clean_token(token) for token in subtitle_tokens]
        if cleaned_subtitle_tokens and not all(token == '' for token in cleaned_subtitle_tokens):
            subtitle = ' '.join(token.capitalize() for token in cleaned_subtitle_tokens)
            title += ': ' + subtitle
    
    return title


def index_entry(record):
    if not isinstance(record, dict):
        return {"status": "error", "detail": "bad-input"}
    if 'number' not in record or not isinstance(record['number'], int) or record['number'] < 0:
        return {"status": "error", "detail": "bad-input"}
    if 'tags' not in record or not isinstance(record['tags'], list) or not all(isinstance(tag, str) for tag in record['tags']):
        return {"status": "error", "detail": "bad-input"}
    
    cleaned_tags = [_clean_token(tag) for tag in record['tags']]
    cleaned_tags = [tag for tag in cleaned_tags if tag]
    
    # Sort by length, preserving original order for ties
    cleaned_tags.sort(key=lambda x: len(x))
    
    number_str = f"{record['number']:03d}"
    
    if 'room' in record:
        if not isinstance(record['room'], str):
            return {"status": "error", "detail": "bad-input"}
        room_tokens = record['room'].split()
        cleaned_room_tokens = [_clean_token(token) for token in room_tokens]
        if not cleaned_room_tokens or all(token == '' for token in cleaned_room_tokens):
            return {"status": "error", "detail": "bad-input"}
        room = ' '.join(token.capitalize() for token in cleaned_room_tokens)
        number_str += f' ({room})'
    
    if not cleaned_tags:
        return number_str
    else:
        return f"{number_str}: {', '.join(cleaned_tags)}"


def label_full(record):
    if not isinstance(record, dict):
        return None
    
    # Check required fields for basic validity
    if 'name' not in record or not isinstance(record['name'], str):
        return None
    if 'artist' not in record or not isinstance(record['artist'], str):
        return None
    if 'year' not in record or not isinstance(record['year'], int) or record['year'] <= 0:
        return None
    
    # Validate name with label_title's requirements
    name_tokens = record['name'].split()
    cleaned_name_tokens = [_clean_token(token) for token in name_tokens]
    if not cleaned_name_tokens or all(token == '' for token in cleaned_name_tokens):
        return None
    
    # Validate artist with label_title's requirements
    artist_tokens = record['artist'].split()
    cleaned_artist_tokens = [_clean_token(token) for token in artist_tokens]
    if not cleaned_artist_tokens or all(token == '' for token in cleaned_artist_tokens):
        return None
    
    # Check for 'number' and 'tags' presence
    if 'number' in record or 'tags' in record:
        # Both must be present and valid
        if 'number' not in record or 'tags' not in record:
            return 'ERR'
        if not isinstance(record['number'], int) or record['number'] < 0:
            return 'ERR'
        if not isinstance(record['tags'], list) or not all(isinstance(tag, str) for tag in record['tags']):
            return 'ERR'
    
    # Construct the label title
    title = ' '.join(token.capitalize() for token in cleaned_name_tokens)
    
    # Construct the artist line
    artist_line = 'by ' + ' '.join(token.capitalize() for token in cleaned_artist_tokens)
    
    # Year as string
    year_line = str(record['year'])
    
    # Add index entry if present
    if 'number' in record and 'tags' in record:
        # Validate and build index entry
        cleaned_tags = [_clean_token(tag) for tag in record['tags']]
        cleaned_tags = [tag for tag in cleaned_tags if tag]
        cleaned_tags.sort(key=lambda x: len(x))
        number_str = f"{record['number']:03d}"
        
        if 'room' in record:
            if isinstance(record['room'], str):
                room_tokens = record['room'].split()
                cleaned_room_tokens = [_clean_token(token) for token in room_tokens]
                if cleaned_room_tokens and not all(token == '' for token in cleaned_room_tokens):
                    room = ' '.join(token.capitalize() for token in cleaned_room_tokens)
                    number_str += f' ({room})'
        
        if not cleaned_tags:
            index_entry = number_str
        else:
            index_entry = f"{number_str}: {', '.join(cleaned_tags)}"
        
        return [title, artist_line, year_line, f"index {index_entry}"]
    
    return [title, artist_line, year_line]
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
    return None
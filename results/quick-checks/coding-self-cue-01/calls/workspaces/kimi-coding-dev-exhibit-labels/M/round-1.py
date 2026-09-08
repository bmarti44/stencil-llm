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
        return 'ERR'
    if 'name' not in record or not isinstance(record['name'], str):
        return 'ERR'
    tokens = record['name'].split()
    cleaned_tokens = [_clean_token(token) for token in tokens]
    if not cleaned_tokens or all(token == '' for token in cleaned_tokens):
        return 'ERR'
    return ' '.join(token.capitalize() for token in cleaned_tokens)


def index_entry(record):
    if not isinstance(record, dict):
        return 'ERR'
    if 'number' not in record or not isinstance(record['number'], int) or record['number'] < 0:
        return 'ERR'
    if 'tags' not in record or not isinstance(record['tags'], list) or not all(isinstance(tag, str) for tag in record['tags']):
        return 'ERR'
    
    cleaned_tags = [_clean_token(tag) for tag in record['tags']]
    cleaned_tags = [tag for tag in cleaned_tags if tag]
    
    # Sort by length, preserving original order for ties
    cleaned_tags.sort(key=lambda x: len(x))
    
    number_str = f"{record['number']:03d}"
    
    if not cleaned_tags:
        return number_str
    else:
        return f"{number_str}: {', '.join(cleaned_tags)}"


def label_full(record):
    return None
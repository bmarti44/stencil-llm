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
    return None


def label_full(record):
    return None
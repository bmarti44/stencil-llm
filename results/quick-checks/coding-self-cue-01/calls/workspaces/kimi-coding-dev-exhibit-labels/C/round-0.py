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
    return None


def label_full(record):
    return None
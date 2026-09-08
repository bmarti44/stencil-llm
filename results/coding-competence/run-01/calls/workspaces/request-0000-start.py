def parse_heading(line):
    if not isinstance(line, str):
        return None
    hashes = 0
    for char in line:
        if char == "#":
            hashes += 1
        else:
            break
    if hashes == 0 or hashes > 6:
        return None
    rest = line[hashes:]
    if not rest.startswith(" "):
        return None
    return {"level": hashes, "title": rest[1:]}


def build_outline(lines):
    return None


def index_sections(outline):
    return None


def query_sections(request):
    return None

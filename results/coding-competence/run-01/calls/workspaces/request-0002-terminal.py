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
    if not isinstance(lines, list):
        return {"error": "invalid input"}
    for line in lines:
        if not isinstance(line, str):
            return {"error": "invalid input"}
    outline = []
    stack = []
    for line in lines:
        heading = parse_heading(line)
        if heading is None:
            continue
        title = heading["title"].strip()
        if not title:
            continue
        level = heading["level"]
        node = {"title": title, "level": level, "children": []}
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            outline.append(node)
        stack.append(node)
    return outline


def index_sections(outline):
    return None


def query_sections(request):
    if not isinstance(request, dict):
        return {"error": "invalid query"}
    if "lines" not in request or "text" not in request:
        return {"error": "invalid query"}
    lines = request["lines"]
    text = request["text"]
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        return {"error": "invalid query"}
    if not isinstance(text, str) or len(text) == 0:
        return {"error": "invalid query"}
    result = index_sections(lines)
    if isinstance(result, dict) and "error" in result:
        return result
    matches = []
    for entry in result:
        if text in entry["title"]:
            matches.append({"number": entry["number"], "title": entry["title"]})
    return {"matches": matches}
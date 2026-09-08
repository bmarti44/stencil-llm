def is_tray(value):
    """Finished helper. True when value is a dict with integer rows >= 1,
    integer cols >= 1, and a blocked list of distinct in-bounds [r, c] integer pairs."""
    if not isinstance(value, dict):
        return False
    rows = value.get("rows")
    cols = value.get("cols")
    blocked = value.get("blocked")
    if not isinstance(rows, int) or not isinstance(cols, int):
        return False
    if rows < 1 or cols < 1:
        return False
    if not isinstance(blocked, list):
        return False
    seen = []
    for cell in blocked:
        if not isinstance(cell, list) or len(cell) != 2:
            return False
        r = cell[0]
        c = cell[1]
        if not isinstance(r, int) or not isinstance(c, int):
            return False
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return False
        if cell in seen:
            return False
        seen.append(cell)
    return True


def assign_slots(payload):
    return None


def summarize_occupancy(payload):
    return None


def plan_report(payload):
    return None

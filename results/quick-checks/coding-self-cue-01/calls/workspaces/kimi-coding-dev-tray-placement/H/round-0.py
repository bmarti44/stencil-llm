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
    if not isinstance(payload, dict):
        return "INVALID"
    if "tray" not in payload or "batch" not in payload:
        return "INVALID"
    
    tray = payload["tray"]
    batch = payload["batch"]
    
    if not is_tray(tray):
        return "INVALID"
    
    if not isinstance(batch, dict):
        return "INVALID"
    if "bid" not in batch or "count" not in batch:
        return "INVALID"
    
    bid = batch["bid"]
    count = batch["count"]
    
    if not isinstance(bid, str) or len(bid) == 0:
        return "INVALID"
    
    if isinstance(count, bool):
        count = 1 if count else 0
    if not isinstance(count, int) or count < 1:
        return "INVALID"
    
    rows = tray["rows"]
    cols = tray["cols"]
    blocked = tray["blocked"]
    
    usable_slots = []
    for r in range(rows):
        for c in range(cols):
            if [r, c] not in blocked:
                usable_slots.append([r, c])
    
    placed = []
    for slot in usable_slots:
        if len(placed) < count:
            placed.append(slot)
        else:
            break
    
    unplaced = count - len(placed)
    
    return {"bid": bid, "placed": placed, "unplaced": unplaced}


def summarize_occupancy(payload):
    return None


def plan_report(payload):
    return None

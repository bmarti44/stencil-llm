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
        return "BAD"
    if "tray" not in payload or "batch" not in payload:
        return "BAD"
    
    tray = payload["tray"]
    batch = payload["batch"]
    
    if not is_tray(tray):
        return "BAD"
    
    if not isinstance(batch, dict):
        return "BAD"
    if "bid" not in batch or "count" not in batch:
        return "BAD"
    
    bid = batch["bid"]
    count = batch["count"]
    
    if not isinstance(bid, str) or len(bid) == 0:
        return "BAD"
    
    if isinstance(count, bool):
        count = 1 if count else 0
    if not isinstance(count, int) or count < 1:
        return "BAD"
    
    # Handle skip list
    skip = batch.get("skip", [])
    if not isinstance(skip, list):
        return "BAD"
    
    rows = tray["rows"]
    cols = tray["cols"]
    blocked = tray["blocked"]
    
    # Validate skip list
    for cell in skip:
        if not isinstance(cell, list) or len(cell) != 2:
            return "BAD"
        r = cell[0]
        c = cell[1]
        if isinstance(r, bool):
            r = 1 if r else 0
        if isinstance(c, bool):
            c = 1 if c else 0
        if not isinstance(r, int) or not isinstance(c, int):
            return "BAD"
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return "BAD"
        if [r, c] in blocked:
            return "BAD"
    
    # Check for duplicates in skip list
    seen = []
    for cell in skip:
        r, c = cell[0], cell[1]
        if [r, c] in seen:
            return "BAD"
        seen.append([r, c])
    
    # Generate usable slots, excluding blocked and skip cells
    usable_slots = []
    for r in range(rows):
        for c in range(cols):
            if [r, c] not in blocked and [r, c] not in skip:
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
    if not isinstance(payload, dict):
        return "INVALID"
    if "tray" not in payload or "placed" not in payload:
        return "INVALID"
    
    tray = payload["tray"]
    placed = payload["placed"]
    
    if not is_tray(tray):
        return "INVALID"
    
    if not isinstance(placed, list):
        return "INVALID"
    
    rows = tray["rows"]
    cols = tray["cols"]
    blocked = tray["blocked"]
    
    # Validate placed cells
    for cell in placed:
        if not isinstance(cell, list) or len(cell) != 2:
            return "INVALID"
        r = cell[0]
        c = cell[1]
        if isinstance(r, bool):
            r = 1 if r else 0
        if isinstance(c, bool):
            c = 1 if c else 0
        if not isinstance(r, int) or not isinstance(c, int):
            return "INVALID"
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return "INVALID"
        if [r, c] in blocked:
            return "INVALID"
    
    # Check for duplicates
    seen = []
    for cell in placed:
        r, c = cell[0], cell[1]
        if [r, c] in seen:
            return "INVALID"
        seen.append([r, c])
    
    # Calculate filled, open, and first_open
    filled = len(placed)
    usable_slots = []
    for r in range(rows):
        for c in range(cols):
            if [r, c] not in blocked:
                usable_slots.append([r, c])
    
    open_count = len(usable_slots) - filled
    
    first_open = None
    for slot in usable_slots:
        if slot not in placed:
            first_open = slot
            break
    
    result = {
        "filled": filled,
        "open": open_count,
        "first_open": first_open
    }
    
    # Handle list_open option
    list_open = payload.get("list_open")
    if list_open is not None:
        if not isinstance(list_open, bool):
            return "INVALID"
        if list_open:
            # Generate open_slots ordered column-first
            open_slots = []
            for c in range(cols):
                for r in range(rows):
                    if [r, c] not in blocked and [r, c] not in placed:
                        open_slots.append([r, c])
            result["open_slots"] = open_slots
    
    return result


def plan_report(payload):
    if not isinstance(payload, dict):
        return "INVALID"
    if "tray" not in payload or "batches" not in payload:
        return "INVALID"
    
    tray = payload["tray"]
    batches = payload["batches"]
    
    if not is_tray(tray):
        return "INVALID"
    
    if not isinstance(batches, list) or len(batches) == 0:
        return "INVALID"
    
    # Validate batches
    for batch in batches:
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
        
        # Handle skip list
        skip = batch.get("skip", [])
        if not isinstance(skip, list):
            return "INVALID"
        
        rows = tray["rows"]
        cols = tray["cols"]
        blocked = tray["blocked"]
        
        # Validate skip list
        for cell in skip:
            if not isinstance(cell, list) or len(cell) != 2:
                return "INVALID"
            r = cell[0]
            c = cell[1]
            if isinstance(r, bool):
                r = 1 if r else 0
            if isinstance(c, bool):
                c = 1 if c else 0
            if not isinstance(r, int) or not isinstance(c, int):
                return "INVALID"
            if r < 0 or c < 0 or r >= rows or c >= cols:
                return "INVALID"
            if [r, c] in blocked:
                return "INVALID"
        
        # Check for duplicates in skip list
        seen = []
        for cell in skip:
            r, c = cell[0], cell[1]
            if [r, c] in seen:
                return "INVALID"
            seen.append([r, c])
    
    # Process batches in order
    results = []
    occupied = []
    for batch in batches:
        # Create a new payload with the current tray and batch
        current_payload = {
            "tray": tray,
            "batch": batch
        }
        
        # Add occupied cells as blocked for this batch
        current_tray = {
            "rows": tray["rows"],
            "cols": tray["cols"],
            "blocked": tray["blocked"] + occupied
        }
        
        # Replace the tray in the payload with the updated one
        current_payload["tray"] = current_tray
        
        # Call assign_slots
        result = assign_slots(current_payload)
        if result == "BAD":
            return "INVALID"
        
        results.append(result)
        occupied.extend(result["placed"])
    
    # Generate summary
    summary_payload = {
        "tray": tray,
        "placed": occupied
    }
    summary = summarize_occupancy(summary_payload)
    if summary == "INVALID":
        return "INVALID"
    
    return {
        "ok": True,
        "results": results,
        "summary": summary
    }
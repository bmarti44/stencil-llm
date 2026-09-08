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
    
    tray = payload.get("tray")
    batch = payload.get("batch")
    
    if not isinstance(tray, dict) or not is_tray(tray):
        return "BAD"
    
    if not isinstance(batch, dict):
        return "BAD"
    
    bid = batch.get("bid")
    count = batch.get("count")
    skip = batch.get("skip")
    
    if not isinstance(bid, str) or len(bid) == 0:
        return "BAD"
    
    if not isinstance(count, int):
        if isinstance(count, bool):
            count = 1 if count else 0
        else:
            return "BAD"
    
    if count < 1:
        return "BAD"
    
    if skip is not None:
        if not isinstance(skip, list):
            return "BAD"
        
        rows = tray["rows"]
        cols = tray["cols"]
        blocked = tray["blocked"]
        
        for cell in skip:
            if not isinstance(cell, list) or len(cell) != 2:
                return "BAD"
            
            r = cell[0]
            c = cell[1]
            
            # Handle boolean values for row and column
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
        
        # Check for duplicate cells in skip
        seen = []
        for cell in skip:
            r, c = cell[0], cell[1]
            if [r, c] in seen:
                return "BAD"
            seen.append([r, c])
    
    rows = tray["rows"]
    cols = tray["cols"]
    blocked = tray["blocked"]
    
    usable_slots = []
    for row in range(rows):
        for col in range(cols):
            if [row, col] not in blocked:
                usable_slots.append([row, col])
    
    # Filter out skip cells
    if skip is not None:
        skip_cells = [[cell[0], cell[1]] for cell in skip]
        usable_slots = [slot for slot in usable_slots if slot not in skip_cells]
    
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
    
    tray = payload.get("tray")
    placed = payload.get("placed")
    list_open = payload.get("list_open")
    
    if not isinstance(tray, dict) or not is_tray(tray):
        return "INVALID"
    
    if not isinstance(placed, list):
        return "INVALID"
    
    if list_open is not None:
        if not isinstance(list_open, bool):
            return "INVALID"
    
    rows = tray["rows"]
    cols = tray["cols"]
    blocked = tray["blocked"]
    
    # Validate each placed cell
    for cell in placed:
        if not isinstance(cell, list) or len(cell) != 2:
            return "INVALID"
        
        r = cell[0]
        c = cell[1]
        
        # Handle boolean values for row and column
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
    
    # Check for duplicate cells
    seen = []
    for cell in placed:
        r, c = cell[0], cell[1]
        if [r, c] in seen:
            return "INVALID"
        seen.append([r, c])
    
    # Calculate filled, open, and first_open
    filled = len(placed)
    usable_slots = []
    for row in range(rows):
        for col in range(cols):
            if [row, col] not in blocked:
                usable_slots.append([row, col])
    
    open_count = len(usable_slots) - filled
    
    # Find first_open in reading order
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
    
    if list_open is True:
        # Generate open_slots list ordered column-first
        open_slots = []
        for col in range(cols):
            for row in range(rows):
                if [row, col] not in blocked and [row, col] not in placed:
                    open_slots.append([row, col])
        result["open_slots"] = open_slots
    
    return result


def plan_report(payload):
    if not isinstance(payload, dict):
        return "INVALID"
    
    tray = payload.get("tray")
    batches = payload.get("batches")
    
    if not isinstance(tray, dict) or not is_tray(tray):
        return "INVALID"
    
    if not isinstance(batches, list) or len(batches) == 0:
        return "INVALID"
    
    results = []
    all_placed = []
    
    for batch in batches:
        if not isinstance(batch, dict):
            return "INVALID"
        
        bid = batch.get("bid")
        count = batch.get("count")
        skip = batch.get("skip")
        
        if not isinstance(bid, str) or len(bid) == 0:
            return "INVALID"
        
        if not isinstance(count, int):
            if isinstance(count, bool):
                count = 1 if count else 0
            else:
                return "INVALID"
        
        if count < 1:
            return "INVALID"
        
        if skip is not None:
            if not isinstance(skip, list):
                return "INVALID"
            
            rows = tray["rows"]
            cols = tray["cols"]
            blocked = tray["blocked"]
            
            for cell in skip:
                if not isinstance(cell, list) or len(cell) != 2:
                    return "INVALID"
                
                r = cell[0]
                c = cell[1]
                
                # Handle boolean values for row and column
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
            
            # Check for duplicate cells in skip
            seen = []
            for cell in skip:
                r, c = cell[0], cell[1]
                if [r, c] in seen:
                    return "INVALID"
                seen.append([r, c])
        
        # Create a new tray with previously placed cells as blocked
        new_tray = {
            "rows": tray["rows"],
            "cols": tray["cols"],
            "blocked": tray["blocked"] + all_placed
        }
        
        # Call assign_slots with the modified tray
        result = assign_slots({
            "tray": new_tray,
            "batch": batch
        })
        
        if not isinstance(result, dict):
            return "INVALID"
        
        results.append(result)
        all_placed.extend(result["placed"])
    
    # Generate summary
    summary_payload = {
        "tray": tray,
        "placed": all_placed
    }
    
    summary = summarize_occupancy(summary_payload)
    
    if not isinstance(summary, dict):
        return "INVALID"
    
    return {
        "ok": True,
        "results": results,
        "summary": summary
    }
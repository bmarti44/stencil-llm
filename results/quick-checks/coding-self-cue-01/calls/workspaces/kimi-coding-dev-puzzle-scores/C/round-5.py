"""Puzzle tournament score aggregation and display pipeline."""


def base_points(place):
    """Base points for a finishing place (1 = winner).

    Non-integer or non-positive places yield 0.
    """
    table = {1: 10, 2: 7, 3: 5, 4: 3}
    if not isinstance(place, int) or isinstance(place, bool):
        return 0
    if place < 1:
        return 0
    return table.get(place, 1)


def solve_total(entry):
    return None


def rank_board(board):
    """Return a leaderboard sorted by total from highest to lowest, with ties broken by original input order."""
    if not isinstance(board, list):
        return None
    
    # Validate each row in the board
    for row in board:
        if not isinstance(row, dict):
            return None
        if "name" not in row or "total" not in row:
            return None
        if not isinstance(row["name"], str) or len(row["name"]) == 0:
            return None
        if not isinstance(row["total"], int) or isinstance(row["total"], bool):
            return None
    
    # Check for duplicate names
    names = [row["name"] for row in board]
    if len(names) != len(set(names)):
        return None
    
    # Sort by total descending, then by original order
    return sorted(board, key=lambda x: (-x["total"], names.index(x["name"])))


def format_summary(data):
    """Return a formatted leaderboard summary from validated data."""
    # Check if data is in entries form
    if isinstance(data, dict) and "entries" in data:
        entries = data["entries"]
        if not isinstance(entries, list):
            return "invalid"
        
        # Calculate totals for each entry
        rows = []
        for entry in entries:
            if not isinstance(entry, dict):
                return "invalid"
            if "name" not in entry or not isinstance(entry["name"], str) or len(entry["name"]) == 0:
                return "invalid"
            
            # Handle legacy "discard" key
            drop = entry.get("drop")
            discard = entry.get("discard")
            if drop is not None and discard is not None:
                return "invalid"  # Both drop and discard present, malformed
            
            # Use drop if present, otherwise discard
            if drop is not None:
                drop_count = drop
            elif discard is not None:
                drop_count = discard
            else:
                drop_count = 0
            
            # Calculate total using solve_total
            total = solve_total(entry)
            if total is None:
                return "invalid"
            
            rows.append({"name": entry["name"], "total": total})
        
        # Validate and order the rows using rank_board
        ranked_board = rank_board(rows)
        if ranked_board is None:
            return "invalid"
    else:
        # Check if data is in board form
        if not isinstance(data, list):
            return "invalid"
        
        # Validate and order the data using rank_board
        ranked_board = rank_board(data)
        if ranked_board is None:
            return "invalid"
    
    # Format the lines and count
    lines = []
    for i, row in enumerate(ranked_board, 1):
        lines.append(f"{i}. {row['name']} - {row['total']}")
    
    # Add champion key for entries form
    result = {
        "lines": lines,
        "count": len(ranked_board)
    }
    if "entries" in data:
        result["champion"] = ranked_board[0]["name"] if ranked_board else None
    
    return result
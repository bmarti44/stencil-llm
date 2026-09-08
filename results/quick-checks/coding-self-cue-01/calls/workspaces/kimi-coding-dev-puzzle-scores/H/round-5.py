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
    """Calculate the total score for a competitor's entry.

    The entry must be a dictionary with "places" (a list of positive integers)
    and an optional "bonus" (a non-negative integer). Any other keys are ignored.
    Malformed input returns None.
    """
    if not isinstance(entry, dict):
        return None

    # Check for both "drop" and "discard" keys
    if "drop" in entry and "discard" in entry:
        return None

    # Handle legacy "discard" key
    drop = entry.get("drop", entry.get("discard", None))

    # Validate drop value
    if drop is not None:
        if not isinstance(drop, int) or drop < 0 or isinstance(drop, bool):
            return None

    places = entry.get("places")
    bonus = entry.get("bonus", 0)

    if not isinstance(places, list) or not all(isinstance(p, int) and p > 0 and not isinstance(p, bool) for p in places):
        return None

    if not isinstance(bonus, int) or bonus < 0 or isinstance(bonus, bool):
        return None

    # Calculate base points
    total = sum(base_points(place) for place in places)

    # Apply drop if specified
    if drop is not None:
        # Sort places in ascending order (lowest first)
        sorted_places = sorted(places)
        # Drop the specified number of lowest places
        adjusted_places = sorted_places[drop:]
        # Recalculate total with dropped places
        total = sum(base_points(place) for place in adjusted_places)

    total += bonus
    return total


def rank_board(board):
    """Rank a leaderboard board according to total scores.

    The board must be a list of dictionaries with "name" (non-empty string) and "total" (integer).
    Returns a new list sorted by total (highest to lowest), with ties preserving original order.
    Malformed input returns None.
    """
    if not isinstance(board, list):
        return None

    names = set()
    ranked = []

    for row in board:
        if not isinstance(row, dict):
            return None

        name = row.get("name")
        total = row.get("total")

        if not isinstance(name, str) or len(name) == 0:
            return None
        if not isinstance(total, int) or isinstance(total, bool):
            return None

        if name in names:
            return None
        names.add(name)

        ranked.append({"name": name, "total": total})

    # Sort by total descending, preserving original order for ties
    ranked.sort(key=lambda x: -x["total"])
    return ranked


def format_summary(data):
    """Generate a formatted summary of the leaderboard.

    Handles two input forms:
    1. A board list (as in rank_board)
    2. A dict with "entries" (list of competitor entries)
    
    Returns a dict with "lines" (formatted strings), "count", and "champion" (for entries form).
    Malformed input returns "invalid".
    """
    if isinstance(data, list):
        # Handle board list form
        ranked = rank_board(data)
        if ranked is None:
            return "invalid"
        
        lines = []
        for i, row in enumerate(ranked, 1):
            lines.append(f"{i}. {row['name']} - {row['total']}")
        
        return {
            "lines": lines,
            "count": len(ranked)
        }
    
    elif isinstance(data, dict) and "entries" in data:
        # Handle entries dict form
        entries = data["entries"]
        if not isinstance(entries, list):
            return "invalid"
        
        # Process each entry
        processed = []
        for entry in entries:
            if not isinstance(entry, dict):
                return "invalid"
            
            name = entry.get("name")
            if not isinstance(name, str) or len(name) == 0:
                return "invalid"
            
            total = solve_total(entry)
            if total is None:
                return "invalid"
            
            processed.append({"name": name, "total": total})
        
        # Rank the processed entries
        ranked = rank_board(processed)
        if ranked is None:
            return "invalid"
        
        # Build lines and find champion
        lines = []
        for i, row in enumerate(ranked, 1):
            lines.append(f"{i}. {row['name']} - {row['total']}")
        
        champion = ranked[0]["name"] if ranked else None
        
        return {
            "lines": lines,
            "count": len(ranked),
            "champion": champion
        }
    
    else:
        return "invalid"
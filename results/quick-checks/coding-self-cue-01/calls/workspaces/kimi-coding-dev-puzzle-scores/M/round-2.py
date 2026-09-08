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
    """Calculate the total score for a competitor's entry."""
    if not isinstance(entry, dict):
        return None
    places = entry.get("places")
    bonus = entry.get("bonus", 0)
    drop = entry.get("drop")
    discard = entry.get("discard")
    
    # Check for both "drop" and "discard" keys
    if drop is not None and discard is not None:
        return None
    
    # Handle legacy "discard" key
    if discard is not None:
        drop = discard
    
    # Validate drop value
    if drop is not None:
        if not isinstance(drop, int) or isinstance(drop, bool) or drop < 0:
            return None
    
    if not isinstance(places, list) or not all(isinstance(p, int) and not isinstance(p, bool) and p > 0 for p in places):
        return None
    if not isinstance(bonus, int) or isinstance(bonus, bool) or bonus < 0:
        return None
    
    # Calculate base points
    total = 0
    for place in places:
        total += base_points(place)
    
    # Apply drop if present
    if drop is not None:
        # Sort places in ascending order (lowest first)
        sorted_places = sorted(places)
        # Drop the specified number of lowest places
        places_to_keep = sorted_places[drop:]
        # Recalculate total with dropped places
        total = 0
        for place in places_to_keep:
            total += base_points(place)
    
    total += bonus
    return total


def rank_board(board):
    """Generate a ranked leaderboard from a list of competitor entries."""
    if not isinstance(board, list):
        return None
    
    # Check each row in the board
    names = set()
    for row in board:
        if not isinstance(row, dict):
            return None
        name = row.get("name")
        total = row.get("total")
        
        # Check name
        if not isinstance(name, str) or len(name) == 0:
            return None
        
        # Check total
        if not isinstance(total, int) or isinstance(total, bool):
            return None
        
        # Check for duplicate names
        if name in names:
            return None
        names.add(name)
    
    # Sort the board by total (descending) and name (ascending)
    sorted_board = sorted(board, key=lambda x: (-x["total"], x["name"]))
    return sorted_board


def format_summary(data):
    return None

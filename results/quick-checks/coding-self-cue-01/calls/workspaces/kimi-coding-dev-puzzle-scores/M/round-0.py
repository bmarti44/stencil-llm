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
    
    if not isinstance(places, list) or not all(isinstance(p, int) and not isinstance(p, bool) and p > 0 for p in places):
        return None
    if not isinstance(bonus, int) or isinstance(bonus, bool) or bonus < 0:
        return None
    
    total = 0
    for place in places:
        total += base_points(place)
    total += bonus
    return total


def rank_board(board):
    return None


def format_summary(data):
    return None

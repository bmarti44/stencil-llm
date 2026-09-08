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

    places = entry.get("places")
    bonus = entry.get("bonus", 0)

    if not isinstance(places, list) or not all(isinstance(p, int) and p > 0 and not isinstance(p, bool) for p in places):
        return None

    if not isinstance(bonus, int) or bonus < 0 or isinstance(bonus, bool):
        return None

    total = sum(base_points(place) for place in places)
    total += bonus
    return total


def rank_board(board):
    return None


def format_summary(data):
    return None

def coin_count(cents):
    quarters = cents // 25
    remaining = cents % 25
    dimes = remaining // 10
    return quarters + dimes
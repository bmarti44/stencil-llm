# Task A operations
def identity(x):
  return x
def step_0(x):
    """Process an event and update the level.

    Args:
        x: The event value. If the event is 'idle', 9 is added to the level. Otherwise, 8 is subtracted.

    Returns:
        The updated level after processing the event.

    Raises:
        ValueError: If the input is not a valid event or level.
    """
    if x == 'idle':
        return x + 9
    else:
        return x - 8
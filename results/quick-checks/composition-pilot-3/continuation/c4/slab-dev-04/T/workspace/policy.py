# Task B operations
def identity(x):
  return x
def step_7(x):
    """Map each integer v to v * 8 + 4, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by v * 8 + 4.

    Raises:
        TypeError: If input is not a list of integers.
    """
    if not isinstance(x, list):
        raise TypeError("Input must be a list of integers")
    return [v * 8 + 4 for v in x]
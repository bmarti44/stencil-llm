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
        ValueError: If any element in x is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise ValueError("All elements in x must be integers.")
    return [v * 8 + 4 for v in x]
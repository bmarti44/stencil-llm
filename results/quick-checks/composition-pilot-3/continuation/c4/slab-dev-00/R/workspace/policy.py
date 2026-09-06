# Task B operations
def identity(x):
  return x
def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by the formula v * 6 + 3.

    Raises:
        TypeError: If any element in the input list is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise TypeError("Input list must contain only integers.")
    return [v * 6 + 3 for v in x]
# Task A operations
def identity(x):
  return x
# core.py

def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by v * 6 + 3.

    Raises:
        ValueError: If any element in x is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise ValueError("All elements in the input list must be integers.")
    return [v * 6 + 3 for v in x]

def step_3(x):
    """Map each integer v to v * 9 + 2, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by v * 9 + 2.

    Raises:
        ValueError: If any element in x is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise ValueError("All elements in the input list must be integers.")
    return [v * 9 + 2 for v in x]
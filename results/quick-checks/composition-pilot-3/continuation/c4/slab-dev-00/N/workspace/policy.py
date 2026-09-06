# Task B operations
def identity(x):
  return x
# policy.py

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

def step_1(x):
    """Map each integer v to v * 4 + 7, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by v * 4 + 7.

    Raises:
        ValueError: If any element in x is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise ValueError("All elements in the input list must be integers.")
    return [v * 4 + 7 for v in x]
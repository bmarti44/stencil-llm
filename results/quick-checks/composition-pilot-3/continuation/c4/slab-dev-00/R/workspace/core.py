# Task A operations
def identity(x):
  return x
def step_3(x):
    """Map each integer v to v * 9 + 2, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by the formula v * 9 + 2.

    Raises:
        TypeError: If any element in the input list is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise TypeError("Input list must contain only integers.")
    return [v * 9 + 2 for v in x]
def step_3(x):
    """Map each integer v to v * 9 + 2, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by the formula v * 9 + 2.

    Raises:
        TypeError: If any element in the input list is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise TypeError("Input list must contain only integers.")
    return [v * 9 + 2 for v in x]

def step_4(x):
    """Map each integer v to v * 5 + 7, preserving order.

    Args:
        x: A list of integers.

    Returns:
        A list of integers where each element is transformed by the formula v * 5 + 7.

    Raises:
        TypeError: If any element in the input list is not an integer.
    """
    if not all(isinstance(v, int) for v in x):
        raise TypeError("Input list must contain only integers.")
    return [v * 5 + 7 for v in x]
# Task B operations
def identity(x):
  return x
# policy.py

def step_0(x):
    """Map each integer v to v * 6 + 6, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 6 + 6.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 6 + 6
# policy.py

def step_0(x):
    """Map each integer v to v * 6 + 6, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 6 + 6.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 6 + 6

def step_1(x):
    """Map each integer v to v * 9 + 1, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 9 + 1.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 9 + 1
# policy.py

def step_0(x):
    """Map each integer v to v * 6 + 6, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 6 + 6.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 6 + 6

def step_1(x):
    """Map each integer v to v * 9 + 1, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 9 + 1.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 9 + 1

def step_2(x):
    """Map each integer v to v * 2 + 2, preserving order.

    Args:
        x (int): Input integer.

    Returns:
        int: Result of x * 2 + 2.

    Raises:
        TypeError: If input is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError("Input must be an integer")
    return x * 2 + 2
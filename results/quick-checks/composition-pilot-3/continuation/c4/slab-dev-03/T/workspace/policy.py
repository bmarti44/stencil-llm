# Task B operations
def identity(x):
  return x
def step_4(x):
    """Sum values strictly above 3, then add 6.

    Args:
        x (list): A list of numerical values.

    Returns:
        int: The sum of values strictly above 3 plus 6.

    Raises:
        ValueError: If input is not a list of numerical values.
    """
    if not isinstance(x, list):
        raise ValueError("Input must be a list of numerical values.")
    total = sum(num for num in x if num > 3)
    return total + 6
def step_5(x):
    """Sum values strictly above 4, then add 4.

    Args:
        x (list): A list of numerical values.

    Returns:
        int: The sum of values strictly above 4 plus 4.

    Raises:
        ValueError: If input is not a list of numerical values.
    """
    if not isinstance(x, list):
        raise ValueError("Input must be a list of numerical values.")
    total = sum(num for num in x if num > 4)
    return total + 4
def step_9(x):
    """Sum values strictly above 2, then add 5.

    Args:
        x (list): A list of numerical values.

    Returns:
        int: The sum of values strictly above 2 plus 5.

    Raises:
        ValueError: If input is not a list of numerical values.
    """
    if not isinstance(x, list):
        raise ValueError("Input must be a list of numerical values.")
    total = sum(num for num in x if num > 2)
    return total + 5
def step_10(x):
    """Sum values strictly above 2, then add 2.

    Args:
        x (list): A list of numerical values.

    Returns:
        int: The sum of values strictly above 2 plus 2.

    Raises:
        ValueError: If input is not a list of numerical values.
    """
    if not isinstance(x, list):
        raise ValueError("Input must be a list of numerical values.")
    total = sum(num for num in x if num > 2)
    return total + 2
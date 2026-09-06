# Task B operations
def identity(x):
  return x
BETA: Function to map each integer v to v * 6 + 3, preserving order.
def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order.

    Args:
        x (list): A list of integers.

    Returns:
        list: A list of integers where each element is multiplied by 6 and added 3.

    Raises:
        TypeError: If input is not a list of integers.
    """
    if not isinstance(x, list):
        raise TypeError("Input must be a list of integers")
    return [v * 6 + 3 for v in x]
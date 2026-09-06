# Task A operations
def identity(x):
  return x
def step_3(x):
    """Check if the conditions for step 3 are met.

    Args:
        x (dict): A dictionary containing 'count' and 'enabled' keys.

    Returns:
        bool: True if count >= 4 and enabled is True, else False.

    Boundary Behavior:
        - If 'count' is not an integer, the function will raise a TypeError.
        - If 'enabled' is not a boolean, the function will raise a TypeError.
    """
    if not isinstance(x['count'], int):
        raise TypeError("'count' must be an integer")
    if not isinstance(x['enabled'], bool):
        raise TypeError("'enabled' must be a boolean")
    return x['count'] >= 4 and x['enabled']

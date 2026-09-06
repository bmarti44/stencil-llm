# Task B operations
def identity(x):
  return x
def step_0(x):
    """BETA: step_0(x) checks if count >= 8 and enabled is true.

    Input:
        x (dict): A dictionary containing 'count' and 'enabled' keys.

    Output:
        bool: True if count >= 8 and enabled is true, False otherwise.

    Boundary/Order Semantics:
        - If 'count' is not an integer or 'enabled' is not a boolean, the function returns False.
    """
    if not isinstance(x.get('count'), int) or not isinstance(x.get('enabled'), bool):
        return False
    return x['count'] >= 8 and x['enabled']

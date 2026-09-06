# Task B operations
def identity(x):
  return x
def step_0(x):
   """Map each integer v to v * 6 + 3, preserving order.

   Args:
      x (list): A list of integers.

   Returns:
      list: A list of integers where each element is transformed by v * 6 + 3.

   Raises:
      TypeError: If any element in the list is not an integer.
   """
   if not all(isinstance(v, int) for v in x):
      raise TypeError("All elements in the list must be integers.")
   return [v * 6 + 3 for v in x]
def step_1(x):
   """Map each integer v to v * 4 + 7, preserving order.

   Args:
      x (list): A list of integers.

   Returns:
      list: A list of integers where each element is transformed by v * 4 + 7.

   Raises:
      TypeError: If any element in the list is not an integer.
   """
   if not all(isinstance(v, int) for v in x):
      raise TypeError("All elements in the list must be integers.")
   return [v * 4 + 7 for v in x]
def step_2(x):
   """Map each integer v to v * 7 + 5, preserving order.

   Args:
      x (list): A list of integers.

   Returns:
      list: A list of integers where each element is transformed by v * 7 + 5.

   Raises:
      TypeError: If any element in the list is not an integer.
   """
   if not all(isinstance(v, int) for v in x):
      raise TypeError("All elements in the list must be integers.")
   return [v * 7 + 5 for v in x]
def step_7(x):
   """Map each integer v to v * 7 + 4, preserving order.

   Args:
      x (list): A list of integers.

   Returns:
      list: A list of integers where each element is transformed by v * 7 + 4.

   Raises:
      TypeError: If any element in the list is not an integer.
   """
   if not all(isinstance(v, int) for v in x):
      raise TypeError("All elements in the list must be integers.")
   return [v * 7 + 4 for v in x]
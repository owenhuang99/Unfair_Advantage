import random

def roll_die():
  """
  Simulates rolling a six-sided die.

  Returns:
      int: A random integer between 1 and 6, inclusive.
  """
  # randint() includes both the start and stop values in the possible outcomes
  result = random.randint(1, 6)
  return result

# Execute the function and print the outcome
if __name__ == "__main__":
  roll = roll_die()
  print(f"You rolled a {roll}")

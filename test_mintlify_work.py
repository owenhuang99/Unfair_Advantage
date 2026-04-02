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


import random

def guess_the_number():
    # 1. Generate a secret number between 1 and 100
    secret_number = random.randint(1, 100)
    attempts = 0
    guessed = False

    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")

    # 2. Start the game loop
    while not guessed:
        try:
            # 3. Get user input and convert to integer
            user_guess = int(input("Enter your guess: "))
            attempts += 1

            # 4. Check the guess and provide feedback
            if user_guess < secret_number:
                print("Too low! Try a higher number.")
            elif user_guess > secret_number:
                print("Too high! Try a lower number.")
            else:
                guessed = True
                print(f"Congratulations! You guessed it in {attempts} attempts.")
        
        except ValueError:
            # Handle cases where input is not a valid number
            print("Please enter a valid whole number.")

if __name__ == "__main__":
    guess_the_number()

import random

def guess_the_number():
    # 1. Generate a secret number between 1 and 100
    secret_number = random.randint(1, 100)
    attempts = 0
    guessed = False

    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")

    # 2. Start the game loop
    while not guessed:
        try:
            # 3. Get user input and convert to integer
            user_guess = int(input("Enter your guess: "))
            attempts += 1

            # 4. Check the guess and provide feedback
            if user_guess < secret_number:
                print("Too low! Try a higher number.")
            elif user_guess > secret_number:
                print("Too high! Try a lower number.")
            else:
                guessed = True
                print(f"Congratulations! You guessed it in {attempts} attempts.")
        
        except ValueError:
            # Handle cases where input is not a valid number
            print("Please enter a valid whole number.")

if __name__ == "__main__":
    guess_the_number()

import random
from pathlib import Path

root = Path(__file__).parent

with open(root / "wordle_answers.txt") as f:
    VALID_ANSWERS = f.read().splitlines()

with open(root / "wordle_guesses.txt") as f:
    VALID_GUESSES = [*VALID_ANSWERS, *f.read().splitlines()]


def random_answer():
    return random.choice(VALID_ANSWERS)


def evaluate_guess(word, guess):
    if len(word) != len(guess):
        raise ValueError("Word and guess must be the same length")

    letters = list(word)
    results = [None] * len(word)

    for i, guessed_letter in enumerate(guess):
        if letters[i] == guessed_letter:
            results[i] = True
            letters[i] = None

    for i, guessed_letter in enumerate(guess):
        if results[i] is not None:
            continue
        for j, letter in enumerate(letters):
            if guessed_letter == letter:
                results[i] = False
                letters[j] = None

    return results

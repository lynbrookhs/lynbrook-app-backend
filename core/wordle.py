import os
import random

PARENT = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(PARENT, "wordle_answers.txt"), "r") as fp:
    VALID_ANSWERS = fp.read().strip().split("\n")
with open(os.path.join(PARENT, "wordle_guesses.txt"), "r") as fp:
    VALID_GUESSES = fp.read().strip().split("\n")


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

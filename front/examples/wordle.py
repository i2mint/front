"""Wordle -- generalized"""

# The core functionality is


def wordle_feedback(guess, word):
    """The wordle score of a guessed word.

    >>> wordle_feedback('woopie', 'wordle')
    [2, 2, 1, 0, 0, 2]

    """
    if len(guess) != len(word):
        return (
            None  # instead of error, so it's less verbose to handle this case outside
        )
    return [
        # 0: no such letter, 1: wrong position, 2: right position
        (guess_letter in word_letter) + (guess_letter in word)
        for guess_letter, word_letter in zip(guess, word)
    ]


# Here's a CLI way the (dynamic) game can be played
# TODO: Better divide these steps into more abstract functions that would be able to
#  be reused
#  both on CLI and GUI for example.
# Note: And yes, we can do all kinds of things like count, or limit the guesses,
# but I'd like to keep it as simple as possible to show minimal code.
# TODO: Include a number (the number of letters) guessing game in this game instead of
#  telling the user how many words it has?
def guessing_game(
    word, prompt='Make a guess: ', char_for_score='.-*', stop_word='exit'
):
    char_for_score = {i: char for i, char in enumerate(char_for_score)}
    n = len(word)
    print(f'--> Type {stop_word} to exit the game')
    print(f'--> The word has {n} letters.')
    while (guess := input(prompt)) not in {word, stop_word}:
        feedback = wordle_feedback(guess, word)
        if feedback is None:
            print(f'--> The word must have {n} letters!')
        else:
            print(' ' * len(prompt) + f"{''.join(map(char_for_score.get, feedback))}")
    if guess != stop_word:
        print('--> Hurray!! The word was indeed {word}')
    print('--> Bye!')


# To play an actual game you have to not know the word to be guessed.
# So the word needs to be random -- but taken from a corpus of possible words.
# Here, we take the actual wordle words (big selection of 5-letter English words).
# TODO: Find source of words of other languages, and have the user chose their
#  language (and number of letters?)
from functools import lru_cache
import urllib.request

# The lru_cache ensures that you won't download the data twice (unless the cell/module
# is reloaded)
@lru_cache
def _get_url_text(url):
    with urllib.request.urlopen(url) as fp:
        return fp.read().decode('utf8')


def wordle_corpus():
    """A list of all wordle words (spoiler alert: past AND future)"""
    url = (
        'https://raw.githubusercontent.com/thorwhalen/content/master/tables/csv'
        '/wordle_words.txt'
    )
    return list(filter(None, _get_url_text(url).split('\n')))


# So here's an actual game (you can play it yourself for real since you don't know the
# word to guess!)
def start_a_game(corpus=None):
    import random

    corpus = corpus or wordle_corpus()
    word = random.choice(corpus)
    guessing_game(word)


if __name__ == '__main__':
    start_a_game()

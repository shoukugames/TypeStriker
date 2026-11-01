import random
import re

from typestriker.config import LEVELS
from typestriker.words import LETTERS, WORDS_BY_LENGTH, Bag, WordDealer

# Checked against the whole word, and as part of a word for the entries that are
# never innocent. This list exists only to protect children and is not in the game.
BLOCKED_EXACT = """
anal anus arse ass bastard bitch bloody blow bomb boob boobs booze bra breast bum butt cock coke cocaine
crack crap cum cunt damn dead death devil dick die dildo drug drunk dumb dyke fag fart fat fuck gay
gun hell hoe horny idiot jerk kill killer knife kkk lesbian loser lust moron murder naked nazi
negro nude nudes nuts opium pee penis pimp piss poo poop porn prick pube pubes pussy queer rape
rapist retard sex sexy shag shit shoot slave slut smoke snort spaz stab stupid suck suicide
tit tits turd twat ugly vagina virgin wank weed whore wine beer vodka whisky
""".split()
BLOCKED_ANYWHERE = "fuck shit cunt bitch whore slut porn nigg rape penis vagina sexy dildo".split()


def all_words():
    return [w for words in WORDS_BY_LENGTH.values() for w in words]


def test_no_bad_words():
    for word in all_words():
        assert word not in BLOCKED_EXACT, word
        for bad in BLOCKED_ANYWHERE:
            # "grape" and "drape" contain "rape" innocently
            if bad == "rape" and word in {"grape", "grapes", "drape", "scrape", "trapeze"}:
                continue
            assert bad not in word, word


def test_words_are_plain_lowercase_of_the_right_length():
    for length, words in WORDS_BY_LENGTH.items():
        assert words, length
        for word in words:
            assert re.fullmatch(r"[a-z]+", word), word
            assert len(word) == length


def test_every_level_has_enough_words_to_never_repeat():
    for level in LEVELS:
        if level.word_length == 1:
            continue
        needed = level.targets + 10  # the wave plus the boss's ten words
        assert len(WORDS_BY_LENGTH[level.word_length]) >= needed, level.name


def test_level_lengths_follow_the_design():
    assert [lv.word_length for lv in LEVELS] == [1, 1, 1, 2, 3, 4, 5, 6, 7, 8]


def test_bag_uses_everything_before_repeating():
    bag = Bag(list("abcdefgh"), random.Random(1))
    assert sorted(bag.draw() for _ in range(8)) == sorted("abcdefgh")


def test_repeats_stay_far_apart_across_reshuffles():
    bag = Bag(LETTERS, random.Random(2))
    seen = [bag.draw() for _ in range(26 * 12)]
    gaps = {}
    for i, letter in enumerate(seen):
        if letter in gaps:
            assert i - gaps[letter] >= 8, letter
        gaps[letter] = i


def test_bag_avoids_requested_first_letters():
    dealer = WordDealer(random.Random(3))
    for _ in range(60):
        assert dealer.deal(5, {"a", "s", "t"})[0] not in "ast"


def test_no_word_repeats_within_a_full_game():
    dealer = WordDealer(random.Random(4))
    for level in LEVELS:
        if level.word_length > 1:
            words = [dealer.deal(level.word_length) for _ in range(level.targets + 10)]
            assert len(set(words)) == len(words), level.name

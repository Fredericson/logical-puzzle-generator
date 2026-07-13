from __future__ import annotations

import argparse

from logical_puzzle_generator.generator import Difficulty, DifficultyPolicy
from logical_puzzle_generator.localization import Language, parse_language


def parse_difficulty_argument(value: str) -> Difficulty:
    try:
        difficulty = DifficultyPolicy().normalize(value)
        if difficulty is None:
            raise argparse.ArgumentTypeError("Difficulty is required.")
        return difficulty
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def parse_language_argument(value: str) -> Language:
    try:
        return parse_language(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc

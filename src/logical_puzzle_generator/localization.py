from __future__ import annotations

from enum import Enum


class Language(str, Enum):
    """Supported presentation languages."""

    ENGLISH = "en"
    GERMAN = "de"


_LANGUAGE_ALIASES = {
    "en": Language.ENGLISH,
    "english": Language.ENGLISH,
    "de": Language.GERMAN,
    "german": Language.GERMAN,
    "deutsch": Language.GERMAN,
}


class TranslationCatalog:
    """Small internal catalog for user-facing PDF and CLI text."""

    _LABELS = {
        Language.ENGLISH: {
            "logical_puzzle": "Logical Puzzle",
            "general": "General",
            "theme": "Theme",
            "difficulty": "Difficulty",
            "clues": "Clues",
            "solving_grid": "Write the names",
            "position": "Position",
            "answer": "Answer",
            "players_items": "Available Names",
            "solution": "Solution",
            "original_clues": "Original Clues",
            "player_item": "Player / Item",
            "puzzle_written": "Puzzle PDF written to",
            "solution_written": "Solution PDF written to",
        },
        Language.GERMAN: {
            "logical_puzzle": "Logikrätsel",
            "general": "Allgemein",
            "theme": "Thema",
            "difficulty": "Schwierigkeit",
            "clues": "Hinweise",
            "solving_grid": "Trage die Namen ein",
            "position": "Position",
            "answer": "Antwort",
            "players_items": "Verfügbare Namen",
            "solution": "Lösung",
            "original_clues": "Hinweise",
            "player_item": "Spielerin / Spieler",
            "puzzle_written": "Rätsel-PDF geschrieben nach",
            "solution_written": "Lösungs-PDF geschrieben nach",
        },
    }

    _DIFFICULTY_LABELS = {
        Language.ENGLISH: {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
        Language.GERMAN: {"easy": "Leicht", "medium": "Mittel", "hard": "Schwierig"},
    }

    _TITLE_TRANSLATIONS = {
        Language.GERMAN: {
            "Tennis Training": "Tennistraining",
            "Logical Puzzle": "Logikrätsel",
        }
    }

    def __init__(self, language: Language | str = Language.ENGLISH) -> None:
        self.language = parse_language(language)

    def label(self, key: str) -> str:
        return self._LABELS[self.language][key]

    def title(self, title: str) -> str:
        return self._TITLE_TRANSLATIONS.get(self.language, {}).get(title, title)

    def difficulty_label(self, value: int) -> str:
        """Return the localized child-facing label for a numeric difficulty value."""

        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"Unsupported difficulty value {value!r}. Expected an integer greater than or equal to 1."
            )
        if value == 1:
            key = "easy"
        elif value == 2:
            key = "medium"
        else:
            key = "hard"
        return self._DIFFICULTY_LABELS[self.language][key]


def parse_language(language: Language | str) -> Language:
    """Normalize public language input to a supported Language value."""

    if isinstance(language, Language):
        return language
    if isinstance(language, str):
        normalized = language.strip().lower()
        if normalized in _LANGUAGE_ALIASES:
            return _LANGUAGE_ALIASES[normalized]
    supported = ", ".join(lang.value for lang in Language)
    raise ValueError(f"Unsupported language {language!r}. Supported languages: {supported}.")


def supported_language_codes() -> tuple[str, ...]:
    return tuple(lang.value for lang in Language)

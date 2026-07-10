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
            "solving_grid": "Solving Grid",
            "position": "Position",
            "answer": "Answer",
            "players_items": "Players / Items",
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
            "solving_grid": "Lösungsraster",
            "position": "Position",
            "answer": "Antwort",
            "players_items": "Spielerinnen / Spieler",
            "solution": "Lösung",
            "original_clues": "Hinweise",
            "player_item": "Spielerin / Spieler",
            "puzzle_written": "Rätsel-PDF geschrieben nach",
            "solution_written": "Lösungs-PDF geschrieben nach",
        },
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

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final, Literal

LanguageCode = Literal["en", "de"]
DEFAULT_THEME_ID: Final = "tennis_training"
RANDOM_THEME_ID: Final = "random"


@dataclass(frozen=True, slots=True)
class LocalizedText:
    en: str
    de: str

    def for_language(self, language: str) -> str:
        return self.de if str(language).endswith("german") or str(language) == "de" else self.en


@dataclass(frozen=True, slots=True)
class ThemeValue:
    id: str
    label: LocalizedText
    short_label: LocalizedText | None = None

    def display(self, language: str, *, short: bool = False) -> str:
        text = self.short_label if short and self.short_label is not None else self.label
        return text.for_language(language)


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    id: str
    title: LocalizedText
    thematic_category_id: str
    category_label: LocalizedText
    values: tuple[ThemeValue, ...]

    def localized_title(self, language: str) -> str:
        return self.title.for_language(language)

    def localized_category_label(self, language: str) -> str:
        return self.category_label.for_language(language)


_THEMES: Final[tuple[ThemeDefinition, ...]] = (
    ThemeDefinition(
        id="tennis_training",
        title=LocalizedText(en="Tennis Training", de="Tennistraining"),
        thematic_category_id="training",
        category_label=LocalizedText(en="Training", de="Training"),
        values=(
            ThemeValue("forehand", LocalizedText(en="Forehand", de="Vorhand")),
            ThemeValue("backhand", LocalizedText(en="Backhand", de="Rückhand")),
            ThemeValue("serve", LocalizedText(en="Serve", de="Aufschlag")),
            ThemeValue("volley", LocalizedText(en="Volley", de="Volley")),
        ),
    ),
    ThemeDefinition(
        id="dance_studio",
        title=LocalizedText(en="Dance Studio", de="Tanzstudio"),
        thematic_category_id="dance_style",
        category_label=LocalizedText(en="Dance Style", de="Tanzstil"),
        values=(
            ThemeValue("waltz", LocalizedText(en="Waltz", de="Walzer")),
            ThemeValue("tango", LocalizedText(en="Tango", de="Tango")),
            ThemeValue("cha_cha_cha", LocalizedText(en="Cha-Cha-Cha", de="Cha-Cha-Cha")),
            ThemeValue("salsa", LocalizedText(en="Salsa", de="Salsa")),
        ),
    ),
    ThemeDefinition(
        id="beach_day",
        title=LocalizedText(en="Beach Day", de="Strandtag"),
        thematic_category_id="activity",
        category_label=LocalizedText(en="Activity", de="Aktivität"),
        values=(
            ThemeValue("sandcastle", LocalizedText(en="builds a sandcastle", de="baut eine Sandburg"), LocalizedText(en="Sandcastle", de="Sandburg")),
            ThemeValue("shells", LocalizedText(en="collects shells", de="sucht Muscheln"), LocalizedText(en="Shells", de="Muscheln")),
            ThemeValue("deck_chair", LocalizedText(en="relaxes on a deck chair", de="liegt im Liegestuhl"), LocalizedText(en="Deck chair", de="Liegestuhl")),
            ThemeValue("water_pistol", LocalizedText(en="plays with a water pistol", de="spielt mit der Wasserpistole"), LocalizedText(en="Water pistol", de="Wasserpistole")),
        ),
    ),
    ThemeDefinition(
        id="athletics_training",
        title=LocalizedText(en="Athletics Training", de="Leichtathletiktraining"),
        thematic_category_id="event",
        category_label=LocalizedText(en="Event", de="Disziplin"),
        values=(
            ThemeValue("shot_put", LocalizedText(en="Shot Put", de="Kugelstossen")),
            ThemeValue("running", LocalizedText(en="Running", de="Lauftraining")),
            ThemeValue("pole_vault", LocalizedText(en="Pole Vault", de="Stabhochsprung")),
            ThemeValue("hurdles", LocalizedText(en="Hurdles", de="Hürdenlauf")),
        ),
    ),
    ThemeDefinition(
        id="zoo_visit",
        title=LocalizedText(en="Zoo Visit", de="Zoobesuch"),
        thematic_category_id="animal_area",
        category_label=LocalizedText(en="Animal Area", de="Tierbereich"),
        values=(
            ThemeValue("flamingos", LocalizedText(en="Flamingos", de="Flamingos")),
            ThemeValue("fish", LocalizedText(en="Fish", de="Fische")),
            ThemeValue("monkeys", LocalizedText(en="Monkeys", de="Affen")),
            ThemeValue("crocodiles", LocalizedText(en="Crocodiles", de="Krokodile")),
        ),
    ),
)


class ThemeRegistry:
    def __init__(self, themes: tuple[ThemeDefinition, ...] = _THEMES) -> None:
        self._themes = {theme.id: theme for theme in themes}

    def supported_theme_ids(self) -> tuple[str, ...]:
        return tuple(self._themes)

    def resolve(self, theme_id: str | None = None, random_source: random.Random | None = None) -> ThemeDefinition:
        canonical = DEFAULT_THEME_ID if theme_id is None else theme_id
        if canonical == RANDOM_THEME_ID:
            rng = random_source if random_source is not None else random.Random()
            canonical = rng.choice(self.supported_theme_ids())
        try:
            return self._themes[canonical]
        except KeyError as exc:
            supported = ", ".join((*self.supported_theme_ids(), RANDOM_THEME_ID))
            raise ValueError(f"Unsupported theme '{canonical}'. Supported themes: {supported}.") from exc


DEFAULT_THEME_REGISTRY: Final = ThemeRegistry()

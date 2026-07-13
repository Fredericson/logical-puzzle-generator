from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from logical_puzzle_generator.localization import Language, parse_language

DEFAULT_THEME_ID: Final = "tennis_training"
RANDOM_THEME_ID: Final = "random"


@dataclass(frozen=True, slots=True)
class LocalizedText:
    en: str
    de: str

    def for_language(self, language: Language | str) -> str:
        parsed = parse_language(language)
        return self.de if parsed is Language.GERMAN else self.en


@dataclass(frozen=True, slots=True)
class ThemeValue:
    id: str
    label: LocalizedText
    short_label: LocalizedText | None = None
    subject_phrase: LocalizedText | None = None

    def display(self, language: Language | str, *, short: bool = False) -> str:
        text = self.short_label if short and self.short_label is not None else self.label
        return text.for_language(language)

    def subject(self, language: Language | str) -> str:
        text = self.subject_phrase if self.subject_phrase is not None else self.label
        return text.for_language(language)


@dataclass(frozen=True, slots=True)
class ThemeWording:
    direct_assignment: LocalizedText
    child_with_theme: LocalizedText
    theme_subject: LocalizedText


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    id: str
    title: LocalizedText
    thematic_category_id: str
    category_label: LocalizedText
    values: tuple[ThemeValue, ...]
    wording: ThemeWording

    def localized_title(self, language: Language | str) -> str:
        return self.title.for_language(language)

    def localized_category_label(self, language: Language | str) -> str:
        return self.category_label.for_language(language)

    def value_by_id(self, value_id: str) -> ThemeValue:
        for value in self.values:
            if value.id == value_id:
                return value
        raise ValueError(f"Theme '{self.id}' has no thematic value '{value_id}'.")


_THEMES: Final[tuple[ThemeDefinition, ...]] = (
    ThemeDefinition(
        id="tennis_training",
        title=LocalizedText(en="Tennis Training", de="Tennistraining"),
        thematic_category_id="training",
        category_label=LocalizedText(en="Training", de="Training"),
        values=(
            ThemeValue("forehand", LocalizedText(en="the forehand", de="die Vorhand"), LocalizedText(en="Forehand", de="Vorhand")),
            ThemeValue("backhand", LocalizedText(en="the backhand", de="die Rückhand"), LocalizedText(en="Backhand", de="Rückhand")),
            ThemeValue("serve", LocalizedText(en="the serve", de="den Aufschlag"), LocalizedText(en="Serve", de="Aufschlag")),
            ThemeValue("volley", LocalizedText(en="the volley", de="den Volley"), LocalizedText(en="Volley", de="Volley")),
        ),
        wording=ThemeWording(
            direct_assignment=LocalizedText(en="{child} practises {theme}.", de="{child} trainiert {theme}."),
            child_with_theme=LocalizedText(en="the child practising {theme}", de="das Kind, das {theme} trainiert"),
            theme_subject=LocalizedText(en="{theme}", de="{theme}"),
        ),
    ),
    ThemeDefinition(
        id="dance_studio",
        title=LocalizedText(en="Dance Studio", de="Tanzstudio"),
        thematic_category_id="dance_style",
        category_label=LocalizedText(en="Dance Style", de="Tanzstil"),
        values=(
            ThemeValue("waltz", LocalizedText(en="waltz", de="Walzer"), LocalizedText(en="Waltz", de="Walzer")),
            ThemeValue("tango", LocalizedText(en="tango", de="Tango"), LocalizedText(en="Tango", de="Tango")),
            ThemeValue("cha_cha_cha", LocalizedText(en="Cha-Cha-Cha", de="Cha-Cha-Cha"), LocalizedText(en="Cha-Cha-Cha", de="Cha-Cha-Cha")),
            ThemeValue("salsa", LocalizedText(en="salsa", de="Salsa"), LocalizedText(en="Salsa", de="Salsa")),
        ),
        wording=ThemeWording(
            direct_assignment=LocalizedText(en="{child} dances {theme}.", de="{child} tanzt {theme}."),
            child_with_theme=LocalizedText(en="the child dancing {theme}", de="das Kind, das {theme} tanzt"),
            theme_subject=LocalizedText(en="{theme}", de="{theme}"),
        ),
    ),
    ThemeDefinition(
        id="beach_day",
        title=LocalizedText(en="Beach Day", de="Strandtag"),
        thematic_category_id="activity",
        category_label=LocalizedText(en="Activity", de="Aktivität"),
        values=(
            ThemeValue("sand_castle", LocalizedText(en="builds a sandcastle", de="baut eine Sandburg"), LocalizedText(en="Sandcastle", de="Sandburg"), LocalizedText(en="building a sandcastle", de="eine Sandburg baut")),
            ThemeValue("shells", LocalizedText(en="collects shells", de="sucht Muscheln"), LocalizedText(en="Shells", de="Muscheln"), LocalizedText(en="collecting shells", de="Muscheln sucht")),
            ThemeValue("deck_chair", LocalizedText(en="relaxes on a deck chair", de="liegt im Liegestuhl"), LocalizedText(en="Deck chair", de="Liegestuhl"), LocalizedText(en="relaxing on a deck chair", de="im Liegestuhl liegt")),
            ThemeValue("water_pistol", LocalizedText(en="plays with a water pistol", de="spielt mit der Wasserpistole"), LocalizedText(en="Water pistol", de="Wasserpistole"), LocalizedText(en="playing with a water pistol", de="mit der Wasserpistole spielt")),
        ),
        wording=ThemeWording(
            direct_assignment=LocalizedText(en="{child} {theme}.", de="{child} {theme}."),
            child_with_theme=LocalizedText(en="the child {theme_subject}", de="das Kind, das {theme_subject}"),
            theme_subject=LocalizedText(en="{theme}", de="{theme}"),
        ),
    ),
    ThemeDefinition(
        id="athletics_training",
        title=LocalizedText(en="Athletics Training", de="Leichtathletiktraining"),
        thematic_category_id="event",
        category_label=LocalizedText(en="Event", de="Disziplin"),
        values=(
            ThemeValue("shot_put", LocalizedText(en="shot put", de="Kugelstossen"), LocalizedText(en="Shot Put", de="Kugelstossen")),
            ThemeValue("running", LocalizedText(en="running", de="Lauftraining"), LocalizedText(en="Running", de="Lauftraining")),
            ThemeValue("pole_vault", LocalizedText(en="pole vault", de="Stabhochsprung"), LocalizedText(en="Pole Vault", de="Stabhochsprung")),
            ThemeValue("hurdles", LocalizedText(en="hurdles", de="Hürdenlauf"), LocalizedText(en="Hurdles", de="Hürdenlauf")),
        ),
        wording=ThemeWording(
            direct_assignment=LocalizedText(en="{child} practises {theme}.", de="{child} übt {theme}."),
            child_with_theme=LocalizedText(en="the child practising {theme}", de="das Kind beim {theme}"),
            theme_subject=LocalizedText(en="{theme}", de="{theme}"),
        ),
    ),
    ThemeDefinition(
        id="zoo_visit",
        title=LocalizedText(en="Zoo Visit", de="Zoobesuch"),
        thematic_category_id="animal_area",
        category_label=LocalizedText(en="Animal Area", de="Tierbereich"),
        values=(
            ThemeValue("flamingos", LocalizedText(en="the flamingos", de="die Flamingos"), LocalizedText(en="Flamingos", de="Flamingos"), LocalizedText(en="the flamingos", de="den Flamingos")),
            ThemeValue("fish", LocalizedText(en="the fish", de="die Fische"), LocalizedText(en="Fish", de="Fische"), LocalizedText(en="the fish", de="den Fischen")),
            ThemeValue("monkeys", LocalizedText(en="the monkeys", de="die Affen"), LocalizedText(en="Monkeys", de="Affen"), LocalizedText(en="the monkeys", de="den Affen")),
            ThemeValue("crocodiles", LocalizedText(en="the crocodiles", de="die Krokodile"), LocalizedText(en="Crocodiles", de="Krokodile"), LocalizedText(en="the crocodiles", de="den Krokodilen")),
        ),
        wording=ThemeWording(
            direct_assignment=LocalizedText(en="{child} visits {theme}.", de="{child} besucht {theme}."),
            child_with_theme=LocalizedText(en="the child visiting {theme}", de="das Kind bei {theme_subject}"),
            theme_subject=LocalizedText(en="{theme}", de="{theme}"),
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

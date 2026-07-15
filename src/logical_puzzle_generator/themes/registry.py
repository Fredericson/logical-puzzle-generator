from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.themes.numeric import build_numeric_value_id, parse_numeric_value_id

DEFAULT_THEME_ID: Final = "tennis_training"
RANDOM_THEME_ID: Final = "random"
DEFAULT_CATEGORY_INSTANCE_INDEX: Final = 1


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
    numeric_value: int | None = None
    position_subject_phrase: LocalizedText | None = None
    position_anchor_sentence: LocalizedText | None = None

    def display(self, language: Language | str, *, short: bool = False) -> str:
        text = self.short_label if short and self.short_label is not None else self.label
        return text.for_language(language)

    def subject(self, language: Language | str) -> str:
        text = self.subject_phrase if self.subject_phrase is not None else self.label
        return text.for_language(language)

    def position_subject(self, language: Language | str) -> str:
        text = (
            self.position_subject_phrase
            if self.position_subject_phrase is not None
            else self.subject_phrase if self.subject_phrase is not None else self.label
        )
        return text.for_language(language)

    def position_anchor(self, language: Language | str, position: int | str) -> str | None:
        if self.position_anchor_sentence is None:
            return None
        return self.position_anchor_sentence.for_language(language).format(position=position)


@dataclass(frozen=True, slots=True)
class ThemeWording:
    direct_assignment: LocalizedText
    child_with_theme_nominative: LocalizedText
    child_with_theme_dative: LocalizedText
    numeric_exact: LocalizedText | None = None
    numeric_position_exact: LocalizedText | None = None
    numeric_more: LocalizedText | None = None
    numeric_fewer: LocalizedText | None = None
    numeric_twice: LocalizedText | None = None
    unit_singular: LocalizedText | None = None
    unit_plural: LocalizedText | None = None


@dataclass(frozen=True, slots=True)
class ThemeCategoryDefinition:
    id: str
    label: LocalizedText
    values: tuple[ThemeValue, ...]
    wording: ThemeWording
    is_numeric: bool = False
    numeric_minimum: int = 2
    numeric_maximum: int = 24

    def __post_init__(self) -> None:
        if self.is_numeric:
            self._validate_numeric_definition()
        elif len(self.values) < 4:
            raise ValueError(f"Theme category '{self.id}' requires at least four values.")

    def _validate_numeric_definition(self) -> None:
        if not isinstance(self.numeric_minimum, int) or isinstance(self.numeric_minimum, bool):
            raise TypeError("Numeric category minimum must be an integer.")
        if not isinstance(self.numeric_maximum, int) or isinstance(self.numeric_maximum, bool):
            raise TypeError("Numeric category maximum must be an integer.")
        if self.numeric_minimum < 0:
            raise ValueError("Numeric category minimum must be non-negative.")
        if self.numeric_maximum <= self.numeric_minimum:
            raise ValueError("Numeric category maximum must be greater than minimum.")
        if self.numeric_maximum - self.numeric_minimum + 1 < 4:
            raise ValueError("Numeric category range must contain at least four values.")
        if not any(
            value * 2 <= self.numeric_maximum
            for value in range(self.numeric_minimum, self.numeric_maximum + 1)
        ):
            raise ValueError("Numeric category range must allow a factor-2 relationship.")
        required = (
            self.wording.numeric_exact,
            self.wording.numeric_position_exact,
            self.wording.numeric_more,
            self.wording.numeric_fewer,
            self.wording.numeric_twice,
            self.wording.unit_singular,
            self.wording.unit_plural,
        )
        if any(text is None for text in required):
            raise ValueError("Numeric category wording is incomplete.")
        if self.values:
            raise ValueError("Generated numeric categories must not define fixed values.")

    def localized_label(self, language: Language | str) -> str:
        return self.label.for_language(language)

    def value_by_id(self, value_id: str) -> ThemeValue:
        for value in self.values:
            if value.id == value_id:
                return value
        raise ValueError(f"Category '{self.id}' has no thematic value '{value_id}'.")

    def parse_generated_numeric_value_id(self, value_id: str, *, instance_id: str) -> ThemeValue:
        """Reconstruct a generated numeric value after validating ID syntax, instance, and range."""
        if not self.is_numeric:
            raise ValueError(f"Category '{self.id}' is not numeric.")
        parsed = parse_numeric_value_id(
            value_id,
            instance_id=instance_id,
            minimum=self.numeric_minimum,
            maximum=self.numeric_maximum,
        )
        return _numeric_value(self, parsed.numeric_value, instance_id)


@dataclass(frozen=True, slots=True)
class ThemeCategoryInstance:
    definition: ThemeCategoryDefinition
    instance_id: str
    selected_values: tuple[ThemeValue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.instance_id, str) or not self.instance_id:
            raise ValueError("Theme category instance ID must be a non-empty string.")
        value_ids = [value.id for value in self.selected_values]
        if len(set(value_ids)) != len(value_ids):
            raise ValueError("Theme category instances require unique selected value IDs.")
        if self.definition.is_numeric:
            for value in self.selected_values:
                if not isinstance(value.numeric_value, int) or isinstance(
                    value.numeric_value, bool
                ):
                    raise ValueError("Numeric category instances require integer selected values.")
                canonical = self.definition.parse_generated_numeric_value_id(
                    value.id, instance_id=self.instance_id
                )
                if canonical.numeric_value != value.numeric_value:
                    raise ValueError("Numeric value ID does not match its numeric value.")
                if value != canonical:
                    raise ValueError(
                        "Numeric category instances require canonical generated values."
                    )
        else:
            for value in self.selected_values:
                canonical = self.definition.value_by_id(value.id)
                if value.numeric_value is not None:
                    raise ValueError("Text category values must not carry numeric values.")
                if value != canonical:
                    raise ValueError("Text category instances require canonical registered values.")

    @property
    def category_id(self) -> str:
        return self.definition.id

    @property
    def selected_value_ids(self) -> tuple[str, ...]:
        return tuple(value.id for value in self.selected_values)

    def value_by_id(self, value_id: str) -> ThemeValue:
        for value in self.selected_values:
            if value.id == value_id:
                return value
        raise ValueError(
            f"Category instance '{self.instance_id}' has no thematic value '{value_id}'."
        )


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    id: str
    title: LocalizedText
    categories: tuple[ThemeCategoryDefinition, ...]

    def localized_title(self, language: Language | str) -> str:
        return self.title.for_language(language)

    def category_by_id(self, category_id: str) -> ThemeCategoryDefinition:
        for category in self.categories:
            if category.id == category_id:
                return category
        supported = ", ".join(category.id for category in self.categories)
        raise ValueError(
            f"Theme '{self.id}' has no category '{category_id}'. Supported categories: {supported}."
        )

    def select_category(
        self,
        category_id: str | None,
        random_source: random.Random,
    ) -> ThemeCategoryDefinition:
        if category_id is not None:
            return self.category_by_id(category_id)
        return random_source.choice(self.categories)

    def create_category_instance(
        self,
        *,
        category_id: str | None,
        random_source: random.Random,
        instance_index: int = DEFAULT_CATEGORY_INSTANCE_INDEX,
    ) -> ThemeCategoryInstance:
        category = self.select_category(category_id, random_source)
        if category.is_numeric:
            selected_values = _generate_numeric_values(category, random_source, instance_index)
        else:
            values = list(category.values)
            if len(values) < 4:
                raise ValueError(
                    f"Theme category '{self.id}.{category.id}' requires at least four values."
                )
            selected_values = (
                tuple(random_source.sample(values, k=4)) if len(values) > 4 else tuple(values)
            )
        return ThemeCategoryInstance(
            definition=category,
            instance_id=f"{category.id}_{instance_index}",
            selected_values=selected_values,
        )


def _text(en: str, de: str) -> LocalizedText:
    return LocalizedText(en=en, de=de)


def _value(
    value_id: str,
    en: str,
    de: str,
    short_en: str | None = None,
    short_de: str | None = None,
    subject_en: str | None = None,
    subject_de: str | None = None,
    numeric_value: int | None = None,
    position_subject_en: str | None = None,
    position_subject_de: str | None = None,
    position_anchor_en: str | None = None,
    position_anchor_de: str | None = None,
) -> ThemeValue:
    return ThemeValue(
        id=value_id,
        label=_text(en, de),
        short_label=_text(short_en or en, short_de or de),
        subject_phrase=_text(subject_en or en, subject_de or de),
        numeric_value=numeric_value,
        position_subject_phrase=(
            _text(position_subject_en, position_subject_de)
            if position_subject_en is not None and position_subject_de is not None
            else None
        ),
        position_anchor_sentence=(
            _text(position_anchor_en, position_anchor_de)
            if position_anchor_en is not None and position_anchor_de is not None
            else None
        ),
    )


def _wording(
    en_direct: str,
    de_direct: str,
    en_child: str,
    de_child: str,
    en_dative: str | None = None,
    de_dative: str | None = None,
) -> ThemeWording:
    return ThemeWording(
        direct_assignment=_text(en_direct, de_direct),
        child_with_theme_nominative=_text(en_child, de_child),
        child_with_theme_dative=_text(en_dative or en_child, de_dative or de_child),
    )


def _category(
    category_id: str,
    label_en: str,
    label_de: str,
    values: tuple[ThemeValue, ...],
    wording: ThemeWording,
    *,
    is_numeric: bool = False,
    numeric_minimum: int = 2,
    numeric_maximum: int = 24,
) -> ThemeCategoryDefinition:
    return ThemeCategoryDefinition(
        category_id,
        _text(label_en, label_de),
        values,
        wording,
        is_numeric,
        numeric_minimum,
        numeric_maximum,
    )


def _numeric_value(category: ThemeCategoryDefinition, value: int, instance_id: str) -> ThemeValue:
    value_id = build_numeric_value_id(instance_id=instance_id, numeric_value=value)
    text = str(value)
    return ThemeValue(value_id, _text(text, text), _text(text, text), _text(text, text), value)


def _generate_numeric_values(
    category: ThemeCategoryDefinition, random_source: random.Random, instance_index: int
) -> tuple[ThemeValue, ...]:
    low, high = category.numeric_minimum, category.numeric_maximum
    bases = [n for n in range(low, high // 2 + 1) if n * 2 <= high]
    random_source.shuffle(bases)
    for base in bases:
        double = base * 2
        candidates = [n for n in range(low, high + 1) if n not in {base, double}]
        random_source.shuffle(candidates)
        for third in candidates:
            diffs = [abs(third - base), abs(third - double)]
            fourths = [
                n
                for n in candidates
                if n != third
                and any(
                    abs(n - x) in diffs or abs(n - x) in (2, 3, 4, 5, 6)
                    for x in (base, double, third)
                )
            ]
            if fourths:
                values = [base, double, third, random_source.choice(fourths)]
                if len(set(values)) == 4 and all(isinstance(v, int) and v >= 0 for v in values):
                    random_source.shuffle(values)
                    instance_id = f"{category.id}_{instance_index}"
                    generated = tuple(_numeric_value(category, v, instance_id) for v in values)
                    _validate_generated_numeric_values(category, generated, instance_id)
                    return generated
    raise ValueError(f"Unable to generate four distinct numeric values for {category.id}.")


def _validate_generated_numeric_values(
    category: ThemeCategoryDefinition, values: tuple[ThemeValue, ...], instance_id: str
) -> None:
    if len(values) != 4:
        raise ValueError("Numeric category generation must produce exactly four values.")
    ids = [value.id for value in values]
    numeric_numbers: list[int] = []
    for value in values:
        number = value.numeric_value
        if not isinstance(number, int) or isinstance(number, bool):
            raise TypeError("Numeric category generation must produce integer values.")
        if number < 0:
            raise ValueError("Numeric category generation must produce non-negative values.")
        if not category.numeric_minimum <= number <= category.numeric_maximum:
            raise ValueError("Numeric category generation produced an out-of-range value.")
        numeric_numbers.append(number)
    if len(set(ids)) != 4:
        raise ValueError("Numeric category generation produced duplicate value IDs.")
    if len(set(numeric_numbers)) != 4:
        raise ValueError("Numeric category generation produced duplicate numeric values.")
    if not any(a == 2 * b for a in numeric_numbers for b in numeric_numbers if a != b):
        raise ValueError("Numeric category generation must include a factor-2 relationship.")
    for value in values:
        assert value.numeric_value is not None
        parsed = parse_numeric_value_id(
            value.id,
            instance_id=instance_id,
            minimum=category.numeric_minimum,
            maximum=category.numeric_maximum,
        )
        if parsed.instance_id != instance_id or parsed.numeric_value != value.numeric_value:
            raise ValueError("Numeric category generated IDs must roundtrip to their values.")
        if (
            build_numeric_value_id(instance_id=instance_id, numeric_value=value.numeric_value)
            != value.id
        ):
            raise ValueError("Numeric category generated IDs must use the canonical format.")


TRAINING_WORDING = _wording(
    "{child} practises {theme}.",
    "{child} trainiert {theme}.",
    "the child practising {theme}",
    "das Kind, das {theme} trainiert",
    "the child practising {theme}",
    "dem Kind, das {theme} trainiert",
)
BACKHAND_WORDING = _wording(
    "{child} plays a {theme}.",
    "{child} spielt eine {theme}.",
    "the child with the {theme}",
    "das Kind mit der {theme}",
    "the child with the {theme}",
    "dem Kind mit der {theme}",
)
PLAYING_STYLE_WORDING = _wording(
    "{child} {theme}.",
    "{child} {theme}.",
    "the child who {theme_subject}",
    "das Kind, das {theme_subject}",
    "the child who {theme_subject}",
    "dem Kind, das {theme_subject}",
)

DANCE_WORDING = _wording(
    "{child} dances {theme}.",
    "{child} tanzt {theme}.",
    "the child dancing {theme}",
    "das Kind, das {theme} tanzt",
    "the child dancing {theme}",
    "dem Kind, das {theme} tanzt",
)
ACTIVITY_WORDING = _wording(
    "{child} {theme}.",
    "{child} {theme}.",
    "the child {theme_subject}",
    "das Kind, das {theme_subject}",
    "the child {theme_subject}",
    "dem Kind, das {theme_subject}",
)
PRACTISE_WORDING = _wording(
    "{child} practises {theme}.",
    "{child} übt {theme}.",
    "the child practising {theme}",
    "das Kind beim {theme}",
    "the child practising {theme}",
    "dem Kind beim {theme}",
)
ZOO_WORDING = _wording(
    "{child} visits {theme}.",
    "{child} besucht {theme}.",
    "the child visiting {theme}",
    "das Kind bei {theme_subject}",
    "the child visiting {theme}",
    "dem Kind bei {theme_subject}",
)
WITH_WORDING = _wording(
    "{child} has {theme}.",
    "{child} hat {theme}.",
    "the child with {theme}",
    "das Kind mit {theme}",
    "the child with {theme}",
    "dem Kind mit {theme}",
)
SURFACE_WORDING = _wording(
    "{child} prefers {theme}.",
    "{child} spielt am liebsten auf {theme}.",
    "the child who prefers {theme}",
    "das Kind, das am liebsten auf {theme} spielt",
    "the child who prefers {theme}",
    "dem Kind, das am liebsten auf {theme} spielt",
)
AT_WORDING = _wording(
    "{child} has {theme}.",
    "{child} hat {theme}.",
    "the child at {theme}",
    "das Kind bei {theme}",
    "the child at {theme}",
    "dem Kind bei {theme}",
)

TOURNAMENT_WINS_WORDING = ThemeWording(
    direct_assignment=_text("{child} won {theme}.", "{child} gewann {theme}."),
    child_with_theme_nominative=_text("the child with {theme}", "das Kind mit {theme}"),
    child_with_theme_dative=_text("the child with {theme}", "dem Kind mit {theme}"),
    numeric_exact=_text("{child} won {value} {unit}.", "{child} gewann {value} {unit}."),
    numeric_position_exact=_text(
        "The child in Position {position} won {value} {unit}.",
        "Das Kind auf Position {position} gewann {value} {unit}.",
    ),
    numeric_more=_text(
        "{greater} won {difference} {unit} more than {lesser}.",
        "{greater} gewann {difference} {unit} mehr als {lesser}.",
    ),
    numeric_fewer=_text(
        "{lesser} won {difference} {unit} fewer than {greater}.",
        "{lesser} gewann {difference} {unit} weniger als {greater}.",
    ),
    numeric_twice=_text(
        "{multiple} won twice as many tournaments as {base}.",
        "{multiple} gewann doppelt so viele Turniere wie {base}.",
    ),
    unit_singular=_text("tournament", "Turnier"),
    unit_plural=_text("tournaments", "Turniere"),
)


RACKET_COLOUR_WORDING = _wording(
    "{child} has {theme}.",
    "{child} hat {theme}.",
    "the child with {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child with {theme_subject}",
    "dem Kind mit {theme_subject}",
)
STRING_COLOUR_WORDING = _wording(
    "{child} plays with {theme}.",
    "{child} spielt mit {theme}.",
    "the child with {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child with {theme_subject}",
    "dem Kind mit {theme_subject}",
)
FOREHAND_GRIP_WORDING = _wording(
    "{child} uses {theme}.",
    "{child} spielt die Vorhand mit {theme}.",
    "the child using {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child using {theme_subject}",
    "dem Kind mit {theme_subject}",
)
LUCKY_CHARM_WORDING = _wording(
    "{child} carries {theme} as her lucky charm.",
    "{child} hat {theme} als Glücksbringer dabei.",
    "the child with {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child with {theme_subject}",
    "dem Kind mit {theme_subject}",
)
FOOTWORK_WORDING = _wording(
    "{child} {theme}.",
    "{child} {theme}.",
    "the child {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child {theme_subject}",
    "dem Kind mit {theme_subject}",
)
BODY_BUILD_WORDING = _wording(
    "{child} {theme}.",
    "{child} {theme}.",
    "{theme_subject}",
    "{theme_subject}",
    "{theme_subject}",
    "{theme_subject}",
)
ACCESSORY_WORDING = _wording(
    "{child} wears {theme}.",
    "{child} trägt {theme}.",
    "the child wearing {theme_subject}",
    "das Kind mit {theme_subject}",
    "the child wearing {theme_subject}",
    "dem Kind mit {theme_subject}",
)

RACKET_COUNT_WORDING = ThemeWording(
    direct_assignment=_text(
        "{child} has {theme} in the bag.", "{child} hat {theme} in der Tasche."
    ),
    child_with_theme_nominative=_text(
        "the child with {theme} rackets in her bag", "das Kind mit {theme} Schlägern in der Tasche"
    ),
    child_with_theme_dative=_text(
        "the child with {theme} rackets in her bag",
        "dem Kind mit {theme} Schlägern in der Tasche",
    ),
    numeric_exact=_text(
        "{child} has {value} {unit} in her bag.",
        "{child} hat {value} {unit} in ihrer Tasche.",
    ),
    numeric_position_exact=_text(
        "The child in Position {position} has {value} {unit} in her bag.",
        "Das Kind auf Position {position} hat {value} {unit} in ihrer Tasche.",
    ),
    numeric_more=_text(
        "{greater} has {difference} more {unit} in her bag than {lesser}.",
        "{greater} hat {difference} {unit} mehr in ihrer Tasche als {lesser}.",
    ),
    numeric_fewer=_text(
        "{lesser} has {difference} fewer {unit} in her bag than {greater}.",
        "{lesser} hat {difference} {unit} weniger in ihrer Tasche als {greater}.",
    ),
    numeric_twice=_text(
        "{multiple} has twice as many rackets in her bag as {base}.",
        "{multiple} hat doppelt so viele Schläger in ihrer Tasche wie {base}.",
    ),
    unit_singular=_text("racket", "Schläger"),
    unit_plural=_text("rackets", "Schläger"),
)

_THEMES: Final[tuple[ThemeDefinition, ...]] = (
    ThemeDefinition(
        id="tennis_training",
        title=_text("Tennis Training", "Tennistraining"),
        categories=(
            _category(
                "training",
                "Training",
                "Training",
                (
                    _value("forehand", "the forehand", "die Vorhand", "Forehand", "Vorhand"),
                    _value("backhand", "the backhand", "die Rückhand", "Backhand", "Rückhand"),
                    _value("serve", "the serve", "den Aufschlag", "Serve", "Aufschlag"),
                    _value("volley", "the volley", "den Volley", "Volley", "Volley"),
                ),
                TRAINING_WORDING,
            ),
            _category(
                "backhand_type",
                "Backhand Type",
                "Rückhandart",
                (
                    _value(
                        "two_handed",
                        "two-handed backhand",
                        "beidhändige Rückhand",
                        "Two-handed",
                        "Beidhändig",
                    ),
                    _value(
                        "one_handed",
                        "one-handed backhand",
                        "einhändige Rückhand",
                        "One-handed",
                        "Einhändig",
                    ),
                    _value("slice", "slice", "Slice", "Slice", "Slice"),
                    _value("topspin", "topspin", "Topspin", "Topspin", "Topspin"),
                ),
                BACKHAND_WORDING,
            ),
            _category(
                "bag_colour",
                "Bag Colour",
                "Taschenfarbe",
                (
                    _value(
                        "red",
                        "the red bag",
                        "der roten Tasche",
                        "Red",
                        "Rot",
                        position_subject_en="The red tennis bag",
                        position_subject_de="Die rote Tennistasche",
                    ),
                    _value(
                        "green",
                        "the green bag",
                        "der grünen Tasche",
                        "Green",
                        "Grün",
                        position_subject_en="The green tennis bag",
                        position_subject_de="Die grüne Tennistasche",
                    ),
                    _value(
                        "yellow",
                        "the yellow bag",
                        "der gelben Tasche",
                        "Yellow",
                        "Gelb",
                        position_subject_en="The yellow tennis bag",
                        position_subject_de="Die gelbe Tennistasche",
                    ),
                    _value(
                        "blue",
                        "the blue bag",
                        "der blauen Tasche",
                        "Blue",
                        "Blau",
                        position_subject_en="The blue tennis bag",
                        position_subject_de="Die blaue Tennistasche",
                    ),
                ),
                WITH_WORDING,
            ),
            _category(
                "playing_style",
                "Playing Style",
                "Spielstil",
                (
                    _value(
                        "serve_and_volley",
                        "plays a lot of serve-and-volley",
                        "spielt viel Serve-and-Volley",
                        "Serve-and-Volley",
                        "Serve-and-Volley",
                        subject_en="plays a lot of serve-and-volley",
                        subject_de="viel Serve-and-Volley spielt",
                    ),
                    _value(
                        "chip_and_charge",
                        "plays a lot of chip-and-charge",
                        "spielt viel Chip-and-Charge",
                        "Chip-and-Charge",
                        "Chip-and-Charge",
                        subject_en="plays a lot of chip-and-charge",
                        subject_de="viel Chip-and-Charge spielt",
                    ),
                    _value(
                        "high_balls",
                        "plays many high balls",
                        "spielt viele hohe Bälle",
                        "High Balls",
                        "Hohe Bälle",
                        subject_en="plays many high balls",
                        subject_de="viele hohe Bälle spielt",
                    ),
                    _value(
                        "drop_shot",
                        "plays many drop shots",
                        "spielt viele Stopbälle",
                        "Drop Shots",
                        "Stopbälle",
                        subject_en="plays many drop shots",
                        subject_de="viele Stopbälle spielt",
                    ),
                ),
                PLAYING_STYLE_WORDING,
            ),
            _category(
                "favourite_surface",
                "Favourite Surface",
                "Lieblingsunterlage",
                (
                    _value("clay", "clay", "Sand", "Clay", "Sand"),
                    _value("hard_court", "hard court", "Hartplatz", "Hard Court", "Hartplatz"),
                    _value("grass", "grass", "Rasen", "Grass", "Rasen"),
                    _value("carpet", "carpet", "Teppich", "Carpet", "Teppich"),
                ),
                SURFACE_WORDING,
            ),
            _category(
                "tournament_wins",
                "Tournament Wins",
                "Turniersiege",
                (),
                TOURNAMENT_WINS_WORDING,
                is_numeric=True,
                numeric_minimum=2,
                numeric_maximum=24,
            ),
            _category(
                "racket_count",
                "Rackets in Bag",
                "Schläger in der Tasche",
                (),
                RACKET_COUNT_WORDING,
                is_numeric=True,
                numeric_minimum=1,
                numeric_maximum=8,
            ),
            _category(
                "racket_colour",
                "Racket Colour",
                "Schlägerfarbe",
                (
                    _value(
                        "blue",
                        "a blue racket",
                        "einen blauen Schläger",
                        "Blue",
                        "Blau",
                        "the blue racket",
                        "dem blauen Schläger",
                        position_subject_en="The blue racket",
                        position_subject_de="Der blaue Schläger",
                    ),
                    _value(
                        "red",
                        "a red racket",
                        "einen roten Schläger",
                        "Red",
                        "Rot",
                        "the red racket",
                        "dem roten Schläger",
                        position_subject_en="The red racket",
                        position_subject_de="Der rote Schläger",
                    ),
                    _value(
                        "green",
                        "a green racket",
                        "einen grünen Schläger",
                        "Green",
                        "Grün",
                        "the green racket",
                        "dem grünen Schläger",
                        position_subject_en="The green racket",
                        position_subject_de="Der grüne Schläger",
                    ),
                    _value(
                        "yellow",
                        "a yellow racket",
                        "einen gelben Schläger",
                        "Yellow",
                        "Gelb",
                        "the yellow racket",
                        "dem gelben Schläger",
                        position_subject_en="The yellow racket",
                        position_subject_de="Der gelbe Schläger",
                    ),
                    _value(
                        "black",
                        "a black racket",
                        "einen schwarzen Schläger",
                        "Black",
                        "Schwarz",
                        "the black racket",
                        "dem schwarzen Schläger",
                        position_subject_en="The black racket",
                        position_subject_de="Der schwarze Schläger",
                    ),
                    _value(
                        "white",
                        "a white racket",
                        "einen weissen Schläger",
                        "White",
                        "Weiss",
                        "the white racket",
                        "dem weissen Schläger",
                        position_subject_en="The white racket",
                        position_subject_de="Der weisse Schläger",
                    ),
                    _value(
                        "pink",
                        "a pink racket",
                        "einen pinken Schläger",
                        "Pink",
                        "Pink",
                        "the pink racket",
                        "dem pinken Schläger",
                        position_subject_en="The pink racket",
                        position_subject_de="Der pinke Schläger",
                    ),
                    _value(
                        "orange",
                        "an orange racket",
                        "einen orangen Schläger",
                        "Orange",
                        "Orange",
                        "the orange racket",
                        "dem orangen Schläger",
                        position_subject_en="The orange racket",
                        position_subject_de="Der orange Schläger",
                    ),
                ),
                RACKET_COLOUR_WORDING,
            ),
            _category(
                "string_colour",
                "String Colour",
                "Saitenfarbe",
                (
                    _value(
                        "white",
                        "white strings",
                        "weissen Saiten",
                        "White",
                        "Weiss",
                        "the white strings",
                        "den weissen Saiten",
                        position_subject_en="The white strings",
                        position_subject_de="Die weissen Saiten",
                        position_anchor_en="The white strings are in Position {position}.",
                        position_anchor_de="Die weissen Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "black",
                        "black strings",
                        "schwarzen Saiten",
                        "Black",
                        "Schwarz",
                        "the black strings",
                        "den schwarzen Saiten",
                        position_subject_en="The black strings",
                        position_subject_de="Die schwarzen Saiten",
                        position_anchor_en="The black strings are in Position {position}.",
                        position_anchor_de="Die schwarzen Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "yellow",
                        "yellow strings",
                        "gelben Saiten",
                        "Yellow",
                        "Gelb",
                        "the yellow strings",
                        "den gelben Saiten",
                        position_subject_en="The yellow strings",
                        position_subject_de="Die gelben Saiten",
                        position_anchor_en="The yellow strings are in Position {position}.",
                        position_anchor_de="Die gelben Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "red",
                        "red strings",
                        "roten Saiten",
                        "Red",
                        "Rot",
                        "the red strings",
                        "den roten Saiten",
                        position_subject_en="The red strings",
                        position_subject_de="Die roten Saiten",
                        position_anchor_en="The red strings are in Position {position}.",
                        position_anchor_de="Die roten Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "blue",
                        "blue strings",
                        "blauen Saiten",
                        "Blue",
                        "Blau",
                        "the blue strings",
                        "den blauen Saiten",
                        position_subject_en="The blue strings",
                        position_subject_de="Die blauen Saiten",
                        position_anchor_en="The blue strings are in Position {position}.",
                        position_anchor_de="Die blauen Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "green",
                        "green strings",
                        "grünen Saiten",
                        "Green",
                        "Grün",
                        "the green strings",
                        "den grünen Saiten",
                        position_subject_en="The green strings",
                        position_subject_de="Die grünen Saiten",
                        position_anchor_en="The green strings are in Position {position}.",
                        position_anchor_de="Die grünen Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "orange",
                        "orange strings",
                        "orangen Saiten",
                        "Orange",
                        "Orange",
                        "the orange strings",
                        "den orangen Saiten",
                        position_subject_en="The orange strings",
                        position_subject_de="Die orangen Saiten",
                        position_anchor_en="The orange strings are in Position {position}.",
                        position_anchor_de="Die orangen Saiten befinden sich auf Position {position}.",
                    ),
                    _value(
                        "pink",
                        "pink strings",
                        "pinken Saiten",
                        "Pink",
                        "Pink",
                        "the pink strings",
                        "den pinken Saiten",
                        position_subject_en="The pink strings",
                        position_subject_de="Die pinken Saiten",
                        position_anchor_en="The pink strings are in Position {position}.",
                        position_anchor_de="Die pinken Saiten befinden sich auf Position {position}.",
                    ),
                ),
                STRING_COLOUR_WORDING,
            ),
            _category(
                "forehand_grip",
                "Forehand Grip",
                "Vorhandgriff",
                (
                    _value(
                        "continental",
                        "a Continental forehand grip",
                        "einem Kontinentalgriff",
                        "Continental",
                        "Kontinental",
                        "a Continental forehand grip",
                        "dem Kontinentalgriff",
                        position_subject_en="The Continental forehand grip",
                        position_subject_de="Der Kontinentalgriff",
                    ),
                    _value(
                        "eastern",
                        "an Eastern forehand grip",
                        "einem Eastern-Griff",
                        "Eastern",
                        "Eastern",
                        "an Eastern forehand grip",
                        "dem Eastern-Vorhandgriff",
                        position_subject_en="The Eastern forehand grip",
                        position_subject_de="Der Eastern-Vorhandgriff",
                    ),
                    _value(
                        "semi_western",
                        "a Semi-Western forehand grip",
                        "einem Semi-Western-Griff",
                        "Semi-Western",
                        "Semi-Western",
                        "a Semi-Western forehand grip",
                        "dem Semi-Western-Vorhandgriff",
                        position_subject_en="The Semi-Western forehand grip",
                        position_subject_de="Der Semi-Western-Vorhandgriff",
                    ),
                    _value(
                        "western",
                        "a Western forehand grip",
                        "einem Western-Griff",
                        "Western",
                        "Western",
                        "a Western forehand grip",
                        "dem Western-Vorhandgriff",
                        position_subject_en="The Western forehand grip",
                        position_subject_de="Der Western-Vorhandgriff",
                    ),
                ),
                FOREHAND_GRIP_WORDING,
            ),
            _category(
                "lucky_charm",
                "Lucky Charm",
                "Glücksbringer",
                (
                    _value(
                        "bracelet",
                        "a bracelet",
                        "ein Armband",
                        "Bracelet",
                        "Armband",
                        "the bracelet",
                        "dem Armband",
                        position_subject_en="The bracelet",
                        position_subject_de="Das Armband",
                    ),
                    _value(
                        "small_teddy",
                        "a small teddy",
                        "einen kleinen Teddybär",
                        "Small Teddy",
                        "Kleiner Teddybär",
                        "the small teddy",
                        "dem kleinen Teddybär",
                        position_subject_en="The small teddy",
                        position_subject_de="Der kleine Teddybär",
                    ),
                    _value(
                        "keyring",
                        "a keyring",
                        "einen Schlüsselanhänger",
                        "Keyring",
                        "Schlüsselanhänger",
                        "the keyring",
                        "dem Schlüsselanhänger",
                        position_subject_en="The keyring",
                        position_subject_de="Der Schlüsselanhänger",
                    ),
                    _value(
                        "lucky_coin",
                        "a lucky coin",
                        "eine Glücksmünze",
                        "Lucky Coin",
                        "Glücksmünze",
                        "the lucky coin",
                        "der Glücksmünze",
                        position_subject_en="The lucky coin",
                        position_subject_de="Die Glücksmünze",
                    ),
                    _value(
                        "hair_ribbon",
                        "a hair ribbon",
                        "ein Haarband",
                        "Hair Ribbon",
                        "Haarband",
                        "the hair ribbon",
                        "dem Haarband",
                        position_subject_en="The hair ribbon",
                        position_subject_de="Das Haarband",
                    ),
                    _value(
                        "mini_tennis_ball",
                        "a mini tennis ball",
                        "einen Mini-Tennisball",
                        "Mini Tennis Ball",
                        "Mini-Tennisball",
                        "the mini tennis ball",
                        "dem Mini-Tennisball",
                        position_subject_en="The mini tennis ball",
                        position_subject_de="Der Mini-Tennisball",
                    ),
                    _value(
                        "four_leaf_clover",
                        "a four-leaf clover",
                        "ein vierblättriges Kleeblatt",
                        "Four-Leaf Clover",
                        "Vierblättriges Kleeblatt",
                        "the four-leaf clover",
                        "dem vierblättrigen Kleeblatt",
                        position_subject_en="The four-leaf clover",
                        position_subject_de="Das vierblättrige Kleeblatt",
                    ),
                    _value(
                        "mascot",
                        "a mascot",
                        "ein Maskottchen",
                        "Mascot",
                        "Maskottchen",
                        "the mascot",
                        "dem Maskottchen",
                        position_subject_en="The mascot",
                        position_subject_de="Das Maskottchen",
                    ),
                ),
                LUCKY_CHARM_WORDING,
            ),
            _category(
                "footwork",
                "Footwork",
                "Schritttechnik",
                (
                    _value(
                        "short_steps",
                        "uses short steps",
                        "macht kurze Schritte",
                        "Short Steps",
                        "Kurze Schritte",
                        "using short steps",
                        "den kurzen Schritten",
                        position_subject_en="Short steps",
                        position_subject_de="Die kurzen Schritte",
                        position_anchor_en="Short steps belong to Position {position}.",
                        position_anchor_de="Die kurzen Schritte gehören zu Position {position}.",
                    ),
                    _value(
                        "long_steps",
                        "uses long steps",
                        "macht lange Schritte",
                        "Long Steps",
                        "Lange Schritte",
                        "using long steps",
                        "den langen Schritten",
                        position_subject_en="Long steps",
                        position_subject_de="Die langen Schritte",
                        position_anchor_en="Long steps belong to Position {position}.",
                        position_anchor_de="Die langen Schritte gehören zu Position {position}.",
                    ),
                    _value(
                        "quick_steps",
                        "uses quick steps",
                        "macht schnelle Schritte",
                        "Quick Steps",
                        "Schnelle Schritte",
                        "using quick steps",
                        "den schnellen Schritten",
                        position_subject_en="Quick steps",
                        position_subject_de="Die schnellen Schritte",
                        position_anchor_en="Quick steps belong to Position {position}.",
                        position_anchor_de="Die schnellen Schritte gehören zu Position {position}.",
                    ),
                    _value(
                        "split_step",
                        "has a strong split step",
                        "hat einen guten Split-Step",
                        "Strong Split Step",
                        "Guter Split-Step",
                        "with the strong split step",
                        "dem guten Split-Step",
                        position_subject_en="The strong split step",
                        position_subject_de="Der gute Split-Step",
                    ),
                ),
                FOOTWORK_WORDING,
            ),
            _category(
                "body_build",
                "Player Build",
                "Spielerstatur",
                (
                    _value(
                        "tall",
                        "is tall",
                        "ist gross",
                        "Tall",
                        "Gross",
                        "the tall child",
                        "das grosse Kind",
                        position_subject_en="The tall child",
                        position_subject_de="Das grosse Kind",
                    ),
                    _value(
                        "medium_height",
                        "is medium height",
                        "ist mittelgross",
                        "Medium Height",
                        "Mittelgross",
                        "the medium-height child",
                        "das mittelgrosse Kind",
                        position_subject_en="The medium-height child",
                        position_subject_de="Das mittelgrosse Kind",
                    ),
                    _value(
                        "small",
                        "is small",
                        "ist klein",
                        "Small",
                        "Klein",
                        "the small child",
                        "das kleine Kind",
                        position_subject_en="The small child",
                        position_subject_de="Das kleine Kind",
                    ),
                    _value(
                        "slim",
                        "is slim",
                        "ist schlank",
                        "Slim",
                        "Schlank",
                        "the slim child",
                        "das schlanke Kind",
                        position_subject_en="The slim child",
                        position_subject_de="Das schlanke Kind",
                    ),
                    _value(
                        "athletic",
                        "has an athletic build",
                        "ist athletisch gebaut",
                        "Athletic",
                        "Athletisch",
                        "the child with the athletic build",
                        "das athletisch gebaute Kind",
                        position_subject_en="The athletic child",
                        position_subject_de="Das athletisch gebaute Kind",
                    ),
                    _value(
                        "strong",
                        "has a strong build",
                        "ist kräftig",
                        "Strong Build",
                        "Kräftig",
                        "the child with the strong build",
                        "das kräftige Kind",
                        position_subject_en="The strong child",
                        position_subject_de="Das kräftige Kind",
                    ),
                ),
                BODY_BUILD_WORDING,
            ),
            _category(
                "accessory",
                "Accessory",
                "Accessoire",
                (
                    _value(
                        "baseball_cap",
                        "a baseball cap",
                        "eine Baseballcap",
                        "Baseball Cap",
                        "Baseballcap",
                        "the baseball cap",
                        "der Baseballcap",
                        position_subject_en="The baseball cap",
                        position_subject_de="Die Baseballcap",
                    ),
                    _value(
                        "visor",
                        "a visor",
                        "einen Visor",
                        "Visor",
                        "Visor",
                        "the visor",
                        "dem Visor",
                        position_subject_en="The visor",
                        position_subject_de="Der Visor",
                    ),
                    _value(
                        "sunglasses",
                        "sunglasses",
                        "eine Sonnenbrille",
                        "Sunglasses",
                        "Sonnenbrille",
                        "sunglasses",
                        "der Sonnenbrille",
                        position_subject_en="The sunglasses",
                        position_subject_de="Die Sonnenbrille",
                    ),
                    _value(
                        "headband",
                        "a headband",
                        "ein Stirnband",
                        "Headband",
                        "Stirnband",
                        "the headband",
                        "dem Stirnband",
                        position_subject_en="The headband",
                        position_subject_de="Das Stirnband",
                    ),
                ),
                ACCESSORY_WORDING,
            ),
        ),
    ),
    ThemeDefinition(
        id="dance_studio",
        title=_text("Dance Studio", "Tanzstudio"),
        categories=(
            _category(
                "dance_style",
                "Dance Style",
                "Tanzstil",
                (
                    _value("waltz", "waltz", "Walzer", "Waltz", "Walzer"),
                    _value("tango", "tango", "Tango", "Tango", "Tango"),
                    _value(
                        "cha_cha_cha", "Cha-Cha-Cha", "Cha-Cha-Cha", "Cha-Cha-Cha", "Cha-Cha-Cha"
                    ),
                    _value("salsa", "salsa", "Salsa", "Salsa", "Salsa"),
                ),
                DANCE_WORDING,
            ),
            _category(
                "costume_colour",
                "Costume Colour",
                "Kostümfarbe",
                (
                    _value("pink", "pink", "Rosa", "Pink", "Rosa"),
                    _value("purple", "purple", "Violett", "Purple", "Violett"),
                    _value("silver", "silver", "Silber", "Silver", "Silber"),
                    _value("gold", "gold", "Gold", "Gold", "Gold"),
                ),
                WITH_WORDING,
            ),
            _category(
                "dance_move",
                "Dance Move",
                "Tanzschritt",
                (
                    _value("turn", "a turn", "eine Drehung", "Turn", "Drehung"),
                    _value("jump", "a jump", "einen Sprung", "Jump", "Sprung"),
                    _value("clap", "a clap", "Klatschen", "Clap", "Klatschen"),
                    _value("spin", "a spin", "einen Wirbel", "Spin", "Wirbel"),
                ),
                DANCE_WORDING,
            ),
            _category(
                "music",
                "Music",
                "Musik",
                (
                    _value("piano", "piano music", "Klaviermusik", "Piano", "Klavier"),
                    _value("drums", "drum music", "Trommelmusik", "Drums", "Trommeln"),
                    _value("guitar", "guitar music", "Gitarrenmusik", "Guitar", "Gitarre"),
                    _value("flute", "flute music", "Flötenmusik", "Flute", "Flöte"),
                ),
                WITH_WORDING,
            ),
        ),
    ),
    ThemeDefinition(
        id="beach_day",
        title=_text("Beach Day", "Strandtag"),
        categories=(
            _category(
                "activity",
                "Activity",
                "Aktivität",
                (
                    _value(
                        "sand_castle",
                        "builds a sandcastle",
                        "baut eine Sandburg",
                        "Sandcastle",
                        "Sandburg",
                        "building a sandcastle",
                        "eine Sandburg baut",
                    ),
                    _value(
                        "shells",
                        "collects shells",
                        "sucht Muscheln",
                        "Shells",
                        "Muscheln",
                        "collecting shells",
                        "Muscheln sucht",
                    ),
                    _value(
                        "deck_chair",
                        "relaxes on a deck chair",
                        "liegt im Liegestuhl",
                        "Deck chair",
                        "Liegestuhl",
                        "relaxing on a deck chair",
                        "im Liegestuhl liegt",
                    ),
                    _value(
                        "water_pistol",
                        "plays with a water pistol",
                        "spielt mit der Wasserpistole",
                        "Water pistol",
                        "Wasserpistole",
                        "playing with a water pistol",
                        "mit der Wasserpistole spielt",
                    ),
                ),
                ACTIVITY_WORDING,
            ),
            _category(
                "towel_colour",
                "Towel Colour",
                "Badetuchfarbe",
                (
                    _value("red", "the red towel", "dem roten Badetuch", "Red", "Rot"),
                    _value("blue", "the blue towel", "dem blauen Badetuch", "Blue", "Blau"),
                    _value("green", "the green towel", "dem grünen Badetuch", "Green", "Grün"),
                    _value("yellow", "the yellow towel", "dem gelben Badetuch", "Yellow", "Gelb"),
                ),
                WITH_WORDING,
            ),
            _category(
                "drink",
                "Drink",
                "Getränk",
                (
                    _value("water", "water", "Wasser", "Water", "Wasser"),
                    _value("juice", "juice", "Saft", "Juice", "Saft"),
                    _value("lemonade", "lemonade", "Limonade", "Lemonade", "Limonade"),
                    _value("cocoa", "cocoa", "Kakao", "Cocoa", "Kakao"),
                ),
                WITH_WORDING,
            ),
            _category(
                "beach_toy",
                "Beach Toy",
                "Strandspielzeug",
                (
                    _value("bucket", "a bucket", "einen Eimer", "Bucket", "Eimer"),
                    _value("shovel", "a shovel", "eine Schaufel", "Shovel", "Schaufel"),
                    _value("ball", "a ball", "einen Ball", "Ball", "Ball"),
                    _value("kite", "a kite", "einen Drachen", "Kite", "Drachen"),
                ),
                WITH_WORDING,
            ),
        ),
    ),
    ThemeDefinition(
        id="athletics_training",
        title=_text("Athletics Training", "Leichtathletiktraining"),
        categories=(
            _category(
                "event",
                "Event",
                "Disziplin",
                (
                    _value("shot_put", "shot put", "Kugelstossen", "Shot Put", "Kugelstossen"),
                    _value("running", "running", "Lauftraining", "Running", "Lauftraining"),
                    _value(
                        "pole_vault", "pole vault", "Stabhochsprung", "Pole Vault", "Stabhochsprung"
                    ),
                    _value("hurdles", "hurdles", "Hürdenlauf", "Hurdles", "Hürdenlauf"),
                ),
                PRACTISE_WORDING,
            ),
            _category(
                "shoe_colour",
                "Shoe Colour",
                "Schuhfarbe",
                (
                    _value("white", "white shoes", "weissen Schuhen", "White", "Weiss"),
                    _value("black", "black shoes", "schwarzen Schuhen", "Black", "Schwarz"),
                    _value("orange", "orange shoes", "orangen Schuhen", "Orange", "Orange"),
                    _value("blue", "blue shoes", "blauen Schuhen", "Blue", "Blau"),
                ),
                WITH_WORDING,
            ),
            _category(
                "training_focus",
                "Training Focus",
                "Trainingsziel",
                (
                    _value("speed", "speed", "Tempo", "Speed", "Tempo"),
                    _value("balance", "balance", "Gleichgewicht", "Balance", "Gleichgewicht"),
                    _value("strength", "strength", "Kraft", "Strength", "Kraft"),
                    _value("jumping", "jumping", "Springen", "Jumping", "Springen"),
                ),
                PRACTISE_WORDING,
            ),
            _category(
                "equipment",
                "Equipment",
                "Gerät",
                (
                    _value("ball", "a ball", "einen Ball", "Ball", "Ball"),
                    _value("rope", "a rope", "ein Seil", "Rope", "Seil"),
                    _value("cone", "a cone", "einen Kegel", "Cone", "Kegel"),
                    _value("mat", "a mat", "eine Matte", "Mat", "Matte"),
                ),
                WITH_WORDING,
            ),
        ),
    ),
    ThemeDefinition(
        id="zoo_visit",
        title=_text("Zoo Visit", "Zoobesuch"),
        categories=(
            _category(
                "animal_area",
                "Animal Area",
                "Tierbereich",
                (
                    _value(
                        "flamingos",
                        "the flamingos",
                        "die Flamingos",
                        "Flamingos",
                        "Flamingos",
                        "the flamingos",
                        "den Flamingos",
                    ),
                    _value(
                        "fish",
                        "the fish",
                        "die Fische",
                        "Fish",
                        "Fische",
                        "the fish",
                        "den Fischen",
                    ),
                    _value(
                        "monkeys",
                        "the monkeys",
                        "die Affen",
                        "Monkeys",
                        "Affen",
                        "the monkeys",
                        "den Affen",
                    ),
                    _value(
                        "crocodiles",
                        "the crocodiles",
                        "die Krokodile",
                        "Crocodiles",
                        "Krokodile",
                        "the crocodiles",
                        "den Krokodilen",
                    ),
                ),
                ZOO_WORDING,
            ),
            _category(
                "snack",
                "Snack",
                "Znüni",
                (
                    _value("apple", "an apple", "einen Apfel", "Apple", "Apfel"),
                    _value("pretzel", "a pretzel", "eine Brezel", "Pretzel", "Brezel"),
                    _value("sandwich", "a sandwich", "ein Sandwich", "Sandwich", "Sandwich"),
                    _value("banana", "a banana", "eine Banane", "Banana", "Banane"),
                ),
                WITH_WORDING,
            ),
            _category(
                "souvenir",
                "Souvenir",
                "Andenken",
                (
                    _value("sticker", "a sticker", "einen Sticker", "Sticker", "Sticker"),
                    _value("postcard", "a postcard", "eine Postkarte", "Postcard", "Postkarte"),
                    _value("pencil", "a pencil", "einen Bleistift", "Pencil", "Bleistift"),
                    _value("badge", "a badge", "einen Anstecker", "Badge", "Anstecker"),
                ),
                WITH_WORDING,
            ),
            _category(
                "meeting_point",
                "Meeting Point",
                "Treffpunkt",
                (
                    _value("gate", "the gate", "dem Tor", "Gate", "Tor"),
                    _value("fountain", "the fountain", "dem Brunnen", "Fountain", "Brunnen"),
                    _value("map", "the map", "dem Plan", "Map", "Plan"),
                    _value("bench", "the bench", "der Bank", "Bench", "Bank"),
                ),
                AT_WORDING,
            ),
        ),
    ),
)


class ThemeRegistry:
    def __init__(self, themes: tuple[ThemeDefinition, ...] = _THEMES) -> None:
        self._themes = {theme.id: theme for theme in themes}

    def supported_theme_ids(self) -> tuple[str, ...]:
        return tuple(self._themes)

    def resolve(
        self, theme_id: str | None = None, random_source: random.Random | None = None
    ) -> ThemeDefinition:
        canonical = DEFAULT_THEME_ID if theme_id is None else theme_id
        if canonical == RANDOM_THEME_ID:
            rng = random_source if random_source is not None else random.Random()
            canonical = rng.choice(self.supported_theme_ids())
        try:
            return self._themes[canonical]
        except KeyError as exc:
            supported = ", ".join((*self.supported_theme_ids(), RANDOM_THEME_ID))
            raise ValueError(
                f"Unsupported theme '{canonical}'. Supported themes: {supported}."
            ) from exc


DEFAULT_THEME_REGISTRY: Final = ThemeRegistry()

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from logical_puzzle_generator.localization import Language, parse_language

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

    def display(self, language: Language | str, *, short: bool = False) -> str:
        text = self.short_label if short and self.short_label is not None else self.label
        return text.for_language(language)

    def subject(self, language: Language | str) -> str:
        text = self.subject_phrase if self.subject_phrase is not None else self.label
        return text.for_language(language)


@dataclass(frozen=True, slots=True)
class ThemeWording:
    direct_assignment: LocalizedText
    child_with_theme_nominative: LocalizedText
    child_with_theme_dative: LocalizedText


@dataclass(frozen=True, slots=True)
class ThemeCategoryDefinition:
    id: str
    label: LocalizedText
    values: tuple[ThemeValue, ...]
    wording: ThemeWording

    def localized_label(self, language: Language | str) -> str:
        return self.label.for_language(language)

    def value_by_id(self, value_id: str) -> ThemeValue:
        for value in self.values:
            if value.id == value_id:
                return value
        raise ValueError(f"Category '{self.id}' has no thematic value '{value_id}'.")


@dataclass(frozen=True, slots=True)
class ThemeCategoryInstance:
    definition: ThemeCategoryDefinition
    instance_id: str
    selected_values: tuple[ThemeValue, ...]

    @property
    def category_id(self) -> str:
        return self.definition.id

    @property
    def selected_value_ids(self) -> tuple[str, ...]:
        return tuple(value.id for value in self.selected_values)


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
        values = list(category.values)
        if len(values) < 4:
            raise ValueError(f"Theme category '{self.id}.{category.id}' requires at least four values.")
        selected_values = tuple(random_source.sample(values, k=4)) if len(values) > 4 else tuple(values)
        return ThemeCategoryInstance(
            definition=category,
            instance_id=f"{category.id}_{instance_index}",
            selected_values=selected_values,
        )


def _text(en: str, de: str) -> LocalizedText:
    return LocalizedText(en=en, de=de)


def _value(value_id: str, en: str, de: str, short_en: str | None = None, short_de: str | None = None, subject_en: str | None = None, subject_de: str | None = None) -> ThemeValue:
    return ThemeValue(
        id=value_id,
        label=_text(en, de),
        short_label=_text(short_en or en, short_de or de),
        subject_phrase=_text(subject_en or en, subject_de or de),
    )


def _wording(en_direct: str, de_direct: str, en_child: str, de_child: str, en_dative: str | None = None, de_dative: str | None = None) -> ThemeWording:
    return ThemeWording(
        direct_assignment=_text(en_direct, de_direct),
        child_with_theme_nominative=_text(en_child, de_child),
        child_with_theme_dative=_text(en_dative or en_child, de_dative or de_child),
    )


def _category(category_id: str, label_en: str, label_de: str, values: tuple[ThemeValue, ...], wording: ThemeWording) -> ThemeCategoryDefinition:
    return ThemeCategoryDefinition(category_id, _text(label_en, label_de), values, wording)


TRAINING_WORDING = _wording(
    "{child} practises {theme}.",
    "{child} trainiert {theme}.",
    "the child practising {theme}",
    "das Kind, das {theme} trainiert",
    "the child practising {theme}",
    "dem Kind, das {theme} trainiert",
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
AT_WORDING = _wording(
    "{child} has {theme}.",
    "{child} hat {theme}.",
    "the child at {theme}",
    "das Kind bei {theme}",
    "the child at {theme}",
    "dem Kind bei {theme}",
)

_THEMES: Final[tuple[ThemeDefinition, ...]] = (
    ThemeDefinition(
        id="tennis_training",
        title=_text("Tennis Training", "Tennistraining"),
        categories=(
            _category("training", "Training", "Training", (
                _value("forehand", "the forehand", "die Vorhand", "Forehand", "Vorhand"),
                _value("backhand", "the backhand", "die Rückhand", "Backhand", "Rückhand"),
                _value("serve", "the serve", "den Aufschlag", "Serve", "Aufschlag"),
                _value("volley", "the volley", "den Volley", "Volley", "Volley"),
            ), TRAINING_WORDING),
            _category("backhand_type", "Backhand Type", "Rückhandart", (
                _value("two_handed", "two-handed backhand", "Doppelhändig", "Two-handed", "Doppelhändig"),
                _value("one_handed", "one-handed backhand", "Einhändig", "One-handed", "Einhändig"),
                _value("slice", "slice", "Slice", "Slice", "Slice"),
                _value("topspin", "topspin", "Topspin", "Topspin", "Topspin"),
            ), WITH_WORDING),
            _category("bag_colour", "Bag Colour", "Taschenfarbe", (
                _value("red", "the red bag", "der roten Tasche", "Red", "Rot"),
                _value("green", "the green bag", "der grünen Tasche", "Green", "Grün"),
                _value("yellow", "the yellow bag", "der gelben Tasche", "Yellow", "Gelb"),
                _value("blue", "the blue bag", "der blauen Tasche", "Blue", "Blau"),
            ), WITH_WORDING),
            _category("playing_style", "Playing Style", "Spielweise", (
                _value("drop_shot", "drop shots", "Stopball", "Drop shot", "Stopball"),
                _value("serve_and_volley", "serve and volley", "Serve and Volley", "Serve & Volley", "Serve & Volley"),
                _value("crosscourt", "crosscourt", "Cross", "Crosscourt", "Cross"),
                _value("down_the_line", "down the line", "Longline", "Line", "Longline"),
                _value("flat", "flat shots", "Flach", "Flat", "Flach"),
                _value("high_balls", "high balls", "Hohe Bälle", "High balls", "Hohe Bälle"),
            ), TRAINING_WORDING),
        ),
    ),
    ThemeDefinition(
        id="dance_studio",
        title=_text("Dance Studio", "Tanzstudio"),
        categories=(
            _category("dance_style", "Dance Style", "Tanzstil", (
                _value("waltz", "waltz", "Walzer", "Waltz", "Walzer"),
                _value("tango", "tango", "Tango", "Tango", "Tango"),
                _value("cha_cha_cha", "Cha-Cha-Cha", "Cha-Cha-Cha", "Cha-Cha-Cha", "Cha-Cha-Cha"),
                _value("salsa", "salsa", "Salsa", "Salsa", "Salsa"),
            ), DANCE_WORDING),
            _category("costume_colour", "Costume Colour", "Kostümfarbe", (
                _value("pink", "pink", "Rosa", "Pink", "Rosa"),
                _value("purple", "purple", "Violett", "Purple", "Violett"),
                _value("silver", "silver", "Silber", "Silver", "Silber"),
                _value("gold", "gold", "Gold", "Gold", "Gold"),
            ), WITH_WORDING),
            _category("dance_move", "Dance Move", "Tanzschritt", (
                _value("turn", "a turn", "eine Drehung", "Turn", "Drehung"),
                _value("jump", "a jump", "einen Sprung", "Jump", "Sprung"),
                _value("clap", "a clap", "Klatschen", "Clap", "Klatschen"),
                _value("spin", "a spin", "einen Wirbel", "Spin", "Wirbel"),
            ), DANCE_WORDING),
            _category("music", "Music", "Musik", (
                _value("piano", "piano music", "Klaviermusik", "Piano", "Klavier"),
                _value("drums", "drum music", "Trommelmusik", "Drums", "Trommeln"),
                _value("guitar", "guitar music", "Gitarrenmusik", "Guitar", "Gitarre"),
                _value("flute", "flute music", "Flötenmusik", "Flute", "Flöte"),
            ), WITH_WORDING),
        ),
    ),
    ThemeDefinition(
        id="beach_day",
        title=_text("Beach Day", "Strandtag"),
        categories=(
            _category("activity", "Activity", "Aktivität", (
                _value("sand_castle", "builds a sandcastle", "baut eine Sandburg", "Sandcastle", "Sandburg", "building a sandcastle", "eine Sandburg baut"),
                _value("shells", "collects shells", "sucht Muscheln", "Shells", "Muscheln", "collecting shells", "Muscheln sucht"),
                _value("deck_chair", "relaxes on a deck chair", "liegt im Liegestuhl", "Deck chair", "Liegestuhl", "relaxing on a deck chair", "im Liegestuhl liegt"),
                _value("water_pistol", "plays with a water pistol", "spielt mit der Wasserpistole", "Water pistol", "Wasserpistole", "playing with a water pistol", "mit der Wasserpistole spielt"),
            ), ACTIVITY_WORDING),
            _category("towel_colour", "Towel Colour", "Badetuchfarbe", (
                _value("red", "the red towel", "dem roten Badetuch", "Red", "Rot"),
                _value("blue", "the blue towel", "dem blauen Badetuch", "Blue", "Blau"),
                _value("green", "the green towel", "dem grünen Badetuch", "Green", "Grün"),
                _value("yellow", "the yellow towel", "dem gelben Badetuch", "Yellow", "Gelb"),
            ), WITH_WORDING),
            _category("drink", "Drink", "Getränk", (
                _value("water", "water", "Wasser", "Water", "Wasser"),
                _value("juice", "juice", "Saft", "Juice", "Saft"),
                _value("lemonade", "lemonade", "Limonade", "Lemonade", "Limonade"),
                _value("cocoa", "cocoa", "Kakao", "Cocoa", "Kakao"),
            ), WITH_WORDING),
            _category("beach_toy", "Beach Toy", "Strandspielzeug", (
                _value("bucket", "a bucket", "einen Eimer", "Bucket", "Eimer"),
                _value("shovel", "a shovel", "eine Schaufel", "Shovel", "Schaufel"),
                _value("ball", "a ball", "einen Ball", "Ball", "Ball"),
                _value("kite", "a kite", "einen Drachen", "Kite", "Drachen"),
            ), WITH_WORDING),
        ),
    ),
    ThemeDefinition(
        id="athletics_training",
        title=_text("Athletics Training", "Leichtathletiktraining"),
        categories=(
            _category("event", "Event", "Disziplin", (
                _value("shot_put", "shot put", "Kugelstossen", "Shot Put", "Kugelstossen"),
                _value("running", "running", "Lauftraining", "Running", "Lauftraining"),
                _value("pole_vault", "pole vault", "Stabhochsprung", "Pole Vault", "Stabhochsprung"),
                _value("hurdles", "hurdles", "Hürdenlauf", "Hurdles", "Hürdenlauf"),
            ), PRACTISE_WORDING),
            _category("shoe_colour", "Shoe Colour", "Schuhfarbe", (
                _value("white", "white shoes", "weissen Schuhen", "White", "Weiss"),
                _value("black", "black shoes", "schwarzen Schuhen", "Black", "Schwarz"),
                _value("orange", "orange shoes", "orangen Schuhen", "Orange", "Orange"),
                _value("blue", "blue shoes", "blauen Schuhen", "Blue", "Blau"),
            ), WITH_WORDING),
            _category("training_focus", "Training Focus", "Trainingsziel", (
                _value("speed", "speed", "Tempo", "Speed", "Tempo"),
                _value("balance", "balance", "Gleichgewicht", "Balance", "Gleichgewicht"),
                _value("strength", "strength", "Kraft", "Strength", "Kraft"),
                _value("jumping", "jumping", "Springen", "Jumping", "Springen"),
            ), PRACTISE_WORDING),
            _category("equipment", "Equipment", "Gerät", (
                _value("ball", "a ball", "einen Ball", "Ball", "Ball"),
                _value("rope", "a rope", "ein Seil", "Rope", "Seil"),
                _value("cone", "a cone", "einen Kegel", "Cone", "Kegel"),
                _value("mat", "a mat", "eine Matte", "Mat", "Matte"),
            ), WITH_WORDING),
        ),
    ),
    ThemeDefinition(
        id="zoo_visit",
        title=_text("Zoo Visit", "Zoobesuch"),
        categories=(
            _category("animal_area", "Animal Area", "Tierbereich", (
                _value("flamingos", "the flamingos", "die Flamingos", "Flamingos", "Flamingos", "the flamingos", "den Flamingos"),
                _value("fish", "the fish", "die Fische", "Fish", "Fische", "the fish", "den Fischen"),
                _value("monkeys", "the monkeys", "die Affen", "Monkeys", "Affen", "the monkeys", "den Affen"),
                _value("crocodiles", "the crocodiles", "die Krokodile", "Crocodiles", "Krokodile", "the crocodiles", "den Krokodilen"),
            ), ZOO_WORDING),
            _category("snack", "Snack", "Znüni", (
                _value("apple", "an apple", "einen Apfel", "Apple", "Apfel"),
                _value("pretzel", "a pretzel", "eine Brezel", "Pretzel", "Brezel"),
                _value("sandwich", "a sandwich", "ein Sandwich", "Sandwich", "Sandwich"),
                _value("banana", "a banana", "eine Banane", "Banana", "Banane"),
            ), WITH_WORDING),
            _category("souvenir", "Souvenir", "Andenken", (
                _value("sticker", "a sticker", "einen Sticker", "Sticker", "Sticker"),
                _value("postcard", "a postcard", "eine Postkarte", "Postcard", "Postkarte"),
                _value("pencil", "a pencil", "einen Bleistift", "Pencil", "Bleistift"),
                _value("badge", "a badge", "einen Anstecker", "Badge", "Anstecker"),
            ), WITH_WORDING),
            _category("meeting_point", "Meeting Point", "Treffpunkt", (
                _value("gate", "the gate", "dem Tor", "Gate", "Tor"),
                _value("fountain", "the fountain", "dem Brunnen", "Fountain", "Brunnen"),
                _value("map", "the map", "dem Plan", "Map", "Plan"),
                _value("bench", "the bench", "der Bank", "Bench", "Bank"),
            ), AT_WORDING),
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

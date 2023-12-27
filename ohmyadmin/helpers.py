def snake_to_sentence(text: str) -> str:
    """Convert snake_case string into 'Snake case' sentence."""
    return text.replace("_", " ").lower().capitalize()


uncountable = [
    "audio",
    "bison",
    "cattle",
    "chassis",
    "compensation",
    "coreopsis",
    "data",
    "deer",
    "education",
    "emoji",
    "equipment",
    "evidence",
    "feedback",
    "firmware",
    "fish",
    "furniture",
    "gold",
    "hardware",
    "information",
    "jedi",
    "kin",
    "knowledge",
    "love",
    "metadata",
    "money",
    "moose",
    "news",
    "nutrition",
    "offspring",
    "plankton",
    "pokemon",
    "police",
    "rain",
    "rice",
    "series",
    "sheep",
    "software",
    "species",
    "swine",
    "traffic",
    "wheat",
]


def pluralize(text: str) -> str:
    """
    A simple pluralization utility.

    It adds -ies suffix to any noun that ends with -y, it adds -es suffix to any noun that ends with -s. For all other
    cases it appends -s.
    """
    if text in uncountable:
        return text

    # is already plural?
    if text.endswith("ies") or text.endswith("rs") or text.endswith("ds"):
        return text

    if text.endswith("y"):
        return text[:-1] + "ies"
    if text.endswith("s"):
        return text + "es"
    return text + "s"

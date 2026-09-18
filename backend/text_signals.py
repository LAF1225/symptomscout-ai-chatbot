import re


DONE_PHRASES = {
    "done",
    "that's all",
    "that is all",
    "thats all",
    "nothing else",
    "that's everything",
    "that is everything",
    "thats everything",
    "i'm finished",
    "im finished",
    "i am finished",
    "i'm done",
    "im done",
    "i am done",
    "i think that's all",
    "i think that is all",
    "i think thats all",
    "that's all for now",
    "that is all for now",
    "thats all for now",
}


CORRECTION_PATTERNS = [
    r"^correction$",
    r"^correction\b",

    r"^that's wrong\b",
    r"^thats wrong\b",
    r"^that is wrong\b",

    r"^i meant\b",

    r"^i need to change\b",
    r"^i want to change\b",
    r"^i would like to change\b",

    r"^i need to correct\b",
    r"^i want to correct\b",
    r"^i would like to correct\b",

    r"^let me change\b",
    r"^let me correct\b",

    r"^can i change\b",
    r"^can i correct\b",
]


NEGATION_PATTERNS = [
    r"\bno\b",
    r"\bnone\b",
    r"\bnothing\b",
    r"\bnever\b",
    r"\bwithout\b",
    r"\bdoesn't\b",
    r"\bdoesnt\b",
    r"\bdon't\b",
    r"\bdont\b",
    r"\bisn't\b",
    r"\bisnt\b",
    r"\baren't\b",
    r"\barent\b",
    r"\bhaven't\b",
    r"\bhavent\b",
    r"\bhasn't\b",
    r"\bhasnt\b",
    r"\bcannot\b",
    r"\bcan't\b",
    r"\bcant\b",
    r"\bgone\b",
    r"\bresolved\b",
]


UNCERTAINTY_PATTERNS = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bprobably\b",
    r"\bpossibly\b",
    r"\bi think\b",
    r"\bi guess\b",
    r"\bnot sure\b",
    r"\bunsure\b",
    r"\bapproximately\b",
    r"\broughly\b",
    r"\babout\b",
]


AMBIGUITY_PATTERNS = [
    r"\bsomewhere\b",
    r"\baround there\b",
    r"\bweird\b",
    r"\bstrange\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bsomething like that\b",
    r"\bhard to describe\b",
    r"\bhard to say\b",
]


LOW_INFORMATION_PHRASES = {
    "somewhere",
    "somewhere around there",
    "around there",
    "weird",
    "strange",
    "kind of weird",
    "sort of weird",
    "something like that",
    "hard to say",
    "not sure where",
}


def normalize_text(text: str) -> str:
    """
    Normalize text without changing its clinical meaning.
    """

    normalized = text.lower().strip()
    normalized = normalized.replace("’", "'")

    normalized = re.sub(
        r"[^\w\s']",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def is_done_signal(text: str) -> bool:
    """
    Detect an explicit whole-message conversation-ending signal.

    Crucially, this does NOT use substring matching.
    """

    normalized = normalize_text(text)

    return normalized in DONE_PHRASES


def is_correction_signal(text: str) -> bool:
    """
    Detect explicit correction requests.

    Common conversational prefixes such as:
    - actually
    - sorry
    - wait

    are removed before matching.

    Plain 'no' is deliberately not treated as a correction.
    """

    normalized = normalize_text(text)

    # Remove common conversational prefixes.
    normalized = re.sub(
        r"^(actually|sorry|wait|oh|okay|ok)\s+",
        "",
        normalized,
    )

    return any(
        re.search(pattern, normalized)
        for pattern in CORRECTION_PATTERNS
    )


def contains_any_pattern(
    text: str,
    patterns: list[str],
) -> bool:
    normalized = normalize_text(text)

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


def detect_flags(text: str) -> dict[str, bool]:
    """
    Preserve language characteristics as metadata rather
    than discarding clinically useful information.
    """

    return {
        "negated": contains_any_pattern(
            text,
            NEGATION_PATTERNS,
        ),
        "uncertain": contains_any_pattern(
            text,
            UNCERTAINTY_PATTERNS,
        ),
        "ambiguous": contains_any_pattern(
            text,
            AMBIGUITY_PATTERNS,
        ),
    }


def should_request_clarification(
    text: str,
    flags: dict[str, bool],
) -> bool:
    """
    Only request clarification when the response is both
    ambiguous and very low-information.

    We intentionally do NOT clarify every uncertain or
    imprecise sentence.
    """

    if not flags.get("ambiguous", False):
        return False

    normalized = normalize_text(text)

    if normalized in LOW_INFORMATION_PHRASES:
        return True

    word_count = len(normalized.split())

    if word_count <= 2:
        return True

    return False

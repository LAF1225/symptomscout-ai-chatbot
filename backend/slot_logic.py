from typing import Any

from dialogflow_contract import PageInfo


SLOT_ORDER = [
    "main_symptom",
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity",
]


def is_filled(value: Any) -> bool:
    """
    Return True when a parameter contains useful data.
    """

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0

    return True


def get_missing_slots(
    session_parameters: dict[str, Any],
) -> list[str]:
    """
    Return symptom slots that have not yet been populated.
    """

    return [
        slot
        for slot in SLOT_ORDER
        if not is_filled(session_parameters.get(slot))
    ]


def get_next_slot(
    session_parameters: dict[str, Any],
) -> str | None:
    """
    Return the first unanswered slot.
    """

    missing = get_missing_slots(session_parameters)

    if not missing:
        return None

    return missing[0]


def get_just_collected_slot(
    page_info: PageInfo | None,
) -> tuple[str | None, Any]:
    """
    Find the form parameter Dialogflow says was collected
    during the immediately preceding turn.
    """

    if page_info is None:
        return None, None

    if page_info.form_info is None:
        return None, None

    for parameter in page_info.form_info.parameter_info:
        if parameter.just_collected:
            return parameter.display_name, parameter.value

    return None, None


def slot_from_webhook_tag(tag: str) -> str | None:
    """
    Convert:

        slot.updated.site

    into:

        site
    """

    prefix = "slot.updated."

    if not tag.startswith(prefix):
        return None

    slot = tag[len(prefix):]

    if slot not in SLOT_ORDER:
        return None

    return slot


def apply_updates(
    original: dict[str, Any],
    updates: dict[str, Any],
) -> dict[str, Any]:
    """
    Produce a local simulation of the session after
    webhook updates have been applied.

    Dialogflow interprets None/null as removing a parameter.
    """

    result = dict(original)

    for key, value in updates.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value

    return result
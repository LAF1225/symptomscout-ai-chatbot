from __future__ import annotations

import hashlib
import json
from typing import Any

from slot_logic import SLOT_ORDER


SUMMARY_SCHEMA_VERSION = 1


SLOT_LABELS: dict[str, str] = {
    "main_symptom": "Main symptom",
    "site": "Location",
    "onset": "When it started",
    "character": "What it feels like",
    "radiation": "Whether it spreads or moves",
    "associated": "Other symptoms mentioned",
    "timing": "Timing or pattern",
    "exacerbating": "What makes it worse",
    "relieving": "What makes it better",
    "severity": "Severity",
}


PATIENT_FACING_FLAG_NOTES: dict[str, str] = {
    "negated": "negative statement",
    "uncertain": "patient expressed uncertainty",
    "ambiguous": "wording may need clarification",
}


def _has_value(value: Any) -> bool:
    """
    Return True only when a slot contains meaningful information.

    None, an empty string, or an empty collection counts as missing.
    """

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)

    return True


def _display_value(value: Any) -> str:
    """
    Convert a stored parameter into safe display text.

    We do not medically reinterpret the value.
    """

    if value is None:
        return "Not provided"

    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else "Not provided"

    if isinstance(value, (list, tuple, set)):
        return (
            ", ".join(str(item) for item in value)
            if value
            else "Not provided"
        )

    if isinstance(value, dict):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
        )

    return str(value)


def _normalise_flags(raw_flags: Any) -> list[str]:
    """
    Accept Phase 7 flag data defensively.

    Supported examples:

        ["uncertain", "negated"]

        {
            "uncertain": True,
            "negated": False
        }

        {
            "flags": ["uncertain"]
        }

        "uncertain"
    """

    flags: list[str] = []

    if isinstance(raw_flags, str):
        flags = [raw_flags]

    elif isinstance(raw_flags, (list, tuple, set)):
        flags = [
            str(item)
            for item in raw_flags
        ]

    elif isinstance(raw_flags, dict):
        nested = raw_flags.get("flags")

        if isinstance(
            nested,
            (list, tuple, set),
        ):
            flags.extend(
                str(item)
                for item in nested
            )

        for key, value in raw_flags.items():

            if key == "flags":
                continue

            if value is True:
                flags.append(str(key))

    seen: set[str] = set()
    normalised: list[str] = []

    for flag in flags:
        cleaned = flag.strip().lower()

        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalised.append(cleaned)

    return normalised


def _slot_flags(
    parameters: dict[str, Any],
    slot: str,
) -> list[str]:
    """
    Read one slot's Phase 7 flags.
    """

    all_flags = parameters.get(
        "p7_slot_flags",
        {},
    )

    if not isinstance(all_flags, dict):
        return []

    return _normalise_flags(
        all_flags.get(slot)
    )


def build_summary_data(
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the machine-readable summary structure.

    Only the canonical symptom slots are included.
    Internal p7_* and p8_* state variables are never
    treated as clinical information.
    """

    fields: list[dict[str, Any]] = []

    provided_count = 0

    for slot in SLOT_ORDER:

        raw_value = parameters.get(slot)

        provided = _has_value(raw_value)

        if provided:
            provided_count += 1

        fields.append(
            {
                "slot": slot,
                "label": SLOT_LABELS[slot],
                "value": (
                    raw_value
                    if provided
                    else None
                ),
                "provided": provided,
                "flags": _slot_flags(
                    parameters,
                    slot,
                ),
            }
        )

    return {
        "schema_version": (
            SUMMARY_SCHEMA_VERSION
        ),
        "fields": fields,
        "provided_count": provided_count,
        "missing_count": (
            len(SLOT_ORDER)
            - provided_count
        ),
    }


def render_summary_body(
    summary_data: dict[str, Any],
) -> str:
    """
    Convert the structured summary into patient-readable text.
    """

    lines = [
        "Symptom communication summary",
        "",
    ]

    for field in summary_data["fields"]:

        value_text = _display_value(
            field["value"]
        )

        notes = [
            PATIENT_FACING_FLAG_NOTES[flag]
            for flag in field.get(
                "flags",
                [],
            )
            if flag
            in PATIENT_FACING_FLAG_NOTES
        ]

        if notes:
            value_text = (
                f"{value_text} "
                f"({'; '.join(notes)})"
            )

        lines.append(
            f"• {field['label']}: "
            f"{value_text}"
        )

    lines.extend(
        [
            "",
            (
                "This summary only reflects "
                "the information you provided. "
                "It does not diagnose a condition "
                "or give medical advice."
            ),
        ]
    )

    return "\n".join(lines)


def build_review_message(
    summary_body: str,
) -> str:
    """
    Add explicit patient confirmation to the summary.
    """

    return (
        f"{summary_body}\n\n"
        "Please check it carefully. "
        "Is this an accurate summary of what "
        "you want to tell a healthcare professional?"
    )


def summary_fingerprint(
    summary_data: dict[str, Any],
) -> str:
    """
    Create a deterministic fingerprint of the summary.

    This prevents an old summary from being confirmed
    after one of the symptom values has changed.

    Internal control parameters are excluded because
    build_summary_data() reads only canonical symptom
    slots and Phase 7 flags.
    """

    canonical_json = json.dumps(
        summary_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def build_summary(
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Main Phase 8 summary-building function.
    """

    data = build_summary_data(parameters)

    body = render_summary_body(data)

    return {
        "data": data,
        "body": body,
        "review_message": (
            build_review_message(body)
        ),
        "fingerprint": (
            summary_fingerprint(data)
        ),
        "ready": (
            data["provided_count"] > 0
        ),
    }

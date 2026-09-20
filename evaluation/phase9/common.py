from __future__ import annotations

import ast
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

TEST_CSV = (
    ROOT
    / "data"
    / "processed"
    / "phase5"
    / "test.csv"
)

REPORT_DIR = (
    ROOT
    / "reports"
    / "phase9"
)


# ---------------------------------------------------------------------------
# Canonical symptom slots
# ---------------------------------------------------------------------------

CANONICAL_SLOTS = [
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


# These page names are used later by the Dialogflow CX evaluator.
PAGE_FOR_SLOT = {
    "main_symptom": "Collect Main Symptom",
    "site": "Collect Site",
    "onset": "Collect Onset",
    "character": "Collect Character",
    "radiation": "Collect Radiation",
    "associated": "Collect Associated Symptoms",
    "timing": "Collect Timing",
    "exacerbating": "Collect Exacerbating Factors",
    "relieving": "Collect Relieving Factors",
    "severity": "Collect Severity",
}


# ---------------------------------------------------------------------------
# Frozen Phase 5 TEST-set integrity values
# ---------------------------------------------------------------------------

EXPECTED_TEST_ROW_COUNT = 57

EXPECTED_FLAG_COUNTS = {
    "ambiguous": 7,
    "negated": 8,
    "uncertain": 2,
    "context_dependent": 21,
}


# ---------------------------------------------------------------------------
# Dataset column aliases
#
# IMPORTANT:
# The real Phase 5 dataset uses:
#
#   annotation_id
#   utterance
#   final_slots
#   slot_count
#   ...
#
# final_slots may contain more than one canonical slot.
# ---------------------------------------------------------------------------

COLUMN_ALIASES = {
    "id": [
        "annotation_id",
        "id",
        "row_id",
        "example_id",
        "utterance_id",
        "sample_id",
    ],

    "text": [
        "utterance",
        "text",
        "sentence",
        "patient_text",
        "example",
        "phrase",
    ],

    "slots": [
        "final_slots",
        "final_slot",
        "slots",
        "slot",
        "slot_label",
        "slot_name",
        "label",
        "attribute",
        "category",
        "final_label",
    ],

    "slot_count": [
        "slot_count",
        "number_of_slots",
        "num_slots",
    ],

    "ambiguous": [
        "ambiguous",
        "is_ambiguous",
        "flag_ambiguous",
    ],

    "negated": [
        "negated",
        "is_negated",
        "flag_negated",
    ],

    "uncertain": [
        "uncertain",
        "is_uncertain",
        "flag_uncertain",
    ],

    "context_dependent": [
        "context_dependent",
        "is_context_dependent",
        "contextdependent",
    ],

    "split": [
        "split",
        "dataset_split",
    ],

    "review_status": [
        "review_status",
        "status",
    ],
}


# ---------------------------------------------------------------------------
# Slot aliases
# ---------------------------------------------------------------------------

SLOT_ALIASES = {
    "main symptom": "main_symptom",
    "main_symptom": "main_symptom",
    "symptom": "main_symptom",

    "site": "site",
    "location": "site",

    "onset": "onset",

    "character": "character",
    "quality": "character",

    "radiation": "radiation",

    "associated": "associated",
    "associated symptom": "associated",
    "associated symptoms": "associated",
    "associated_symptom": "associated",
    "associated_symptoms": "associated",

    "timing": "timing",

    "exacerbating": "exacerbating",
    "exacerbating factor": "exacerbating",
    "exacerbating factors": "exacerbating",
    "aggravating": "exacerbating",
    "aggravating factor": "exacerbating",
    "aggravating factors": "exacerbating",

    "relieving": "relieving",
    "relieving factor": "relieving",
    "relieving factors": "relieving",

    "severity": "severity",
}


TRUE_VALUES = {
    "true",
    "1",
    "yes",
    "y",
    "t",
}

FALSE_VALUES = {
    "false",
    "0",
    "no",
    "n",
    "f",
}


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def normalize_column_name(value: str) -> str:
    value = value.strip().lower()

    value = re.sub(
        r"[\s\-]+",
        "_",
        value,
    )

    return value


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    value = str(value)

    return re.sub(
        r"\s+",
        " ",
        value.strip().lower(),
    )


def parse_bool(value: Any) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if not text:
        return None

    if text in TRUE_VALUES:
        return True

    if text in FALSE_VALUES:
        return False

    raise ValueError(
        f"Cannot interpret boolean value {value!r}."
    )


# ---------------------------------------------------------------------------
# Slot parsing
# ---------------------------------------------------------------------------

def canonical_slot(value: Any) -> str | None:
    """
    Convert one raw slot label into one of the ten canonical names.
    """

    if value is None:
        return None

    raw = str(value).strip().lower()

    if not raw:
        return None

    normalized = (
        raw
        .replace("-", " ")
        .replace("_", " ")
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    if normalized in SLOT_ALIASES:
        return SLOT_ALIASES[normalized]

    underscored = normalized.replace(
        " ",
        "_",
    )

    if underscored in CANONICAL_SLOTS:
        return underscored

    return None


def _extract_raw_slot_items(
    value: Any,
) -> list[str]:
    """
    Parse final_slots robustly.

    Supports common representations such as:

        ['site', 'onset']
        ["site", "onset"]
        site|onset
        site;onset
        site,onset
        site
    """

    if value is None:
        return []

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    raw = str(value).strip()

    if not raw:
        return []

    # First try genuine JSON.
    try:
        parsed = json.loads(raw)

        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item).strip()
            ]

        if isinstance(parsed, str):
            return [parsed.strip()]

    except (json.JSONDecodeError, TypeError):
        pass

    # Then try Python-style list strings:
    #
    # ['site', 'onset']
    #
    try:
        parsed = ast.literal_eval(raw)

        if isinstance(
            parsed,
            (list, tuple, set),
        ):
            return [
                str(item).strip()
                for item in parsed
                if str(item).strip()
            ]

        if isinstance(parsed, str):
            return [parsed.strip()]

    except (
        ValueError,
        SyntaxError,
        TypeError,
    ):
        pass

    # Finally support ordinary delimited text.
    cleaned = raw.strip("[](){}")

    pieces = re.split(
        r"[|;,]+",
        cleaned,
    )

    return [
        piece.strip().strip("'\"")
        for piece in pieces
        if piece.strip().strip("'\"")
    ]


def parse_slots(
    value: Any,
) -> list[str]:
    """
    Parse a final_slots value into canonical slot names.

    Raises ValueError instead of silently dropping an unknown label.
    """

    raw_items = _extract_raw_slot_items(
        value
    )

    parsed: list[str] = []

    for raw_item in raw_items:
        slot = canonical_slot(raw_item)

        if slot is None:
            raise ValueError(
                f"Unrecognized slot label: {raw_item!r}"
            )

        if slot not in parsed:
            parsed.append(slot)

    return parsed


# ---------------------------------------------------------------------------
# Column resolution
# ---------------------------------------------------------------------------

def resolve_columns(
    fieldnames: list[str],
) -> dict[str, str | None]:

    normalized_lookup = {
        normalize_column_name(field): field
        for field in fieldnames
    }

    resolved: dict[str, str | None] = {}

    for logical_name, aliases in COLUMN_ALIASES.items():
        resolved[logical_name] = None

        for alias in aliases:
            normalized_alias = (
                normalize_column_name(alias)
            )

            if (
                normalized_alias
                in normalized_lookup
            ):
                resolved[logical_name] = (
                    normalized_lookup[
                        normalized_alias
                    ]
                )

                break

    return resolved


# ---------------------------------------------------------------------------
# TEST-set loading
# ---------------------------------------------------------------------------

def load_test_rows() -> tuple[
    list[dict[str, str]],
    dict[str, str | None],
]:
    if not TEST_CSV.exists():
        raise FileNotFoundError(
            "Frozen Phase 5 TEST split was not found at:\n"
            f"{TEST_CSV}"
        )

    with TEST_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:

        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise RuntimeError(
                "test.csv has no header row."
            )

        rows = list(reader)

        columns = resolve_columns(
            reader.fieldnames
        )

        fieldnames = list(
            reader.fieldnames
        )

    if columns["text"] is None:
        raise RuntimeError(
            "Could not identify the utterance/text "
            "column in test.csv.\n"
            f"Columns found: {fieldnames}"
        )

    if columns["slots"] is None:
        raise RuntimeError(
            "Could not identify the final_slots "
            "column in test.csv.\n"
            f"Columns found: {fieldnames}"
        )

    return rows, columns


# ---------------------------------------------------------------------------
# Row ID
# ---------------------------------------------------------------------------

def row_id(
    row: dict[str, str],
    columns: dict[str, str | None],
    fallback_index: int,
) -> str:

    id_column = columns.get("id")

    if id_column:
        value = row.get(id_column)

        if value and value.strip():
            return value.strip()

    return (
        f"test-row-{fallback_index:03d}"
    )


# ---------------------------------------------------------------------------
# Frozen TEST-set audit
# ---------------------------------------------------------------------------

def audit_test_rows(
    rows: list[dict[str, str]],
    columns: dict[str, str | None],
) -> dict:

    errors: list[str] = []
    warnings: list[str] = []

    # -------------------------------------------------------
    # Row count
    # -------------------------------------------------------

    if len(rows) != EXPECTED_TEST_ROW_COUNT:
        errors.append(
            "Expected exactly "
            f"{EXPECTED_TEST_ROW_COUNT} "
            "frozen TEST rows; "
            f"found {len(rows)}."
        )

    text_column = columns["text"]
    slots_column = columns["slots"]

    empty_text_rows: list[int] = []
    invalid_slot_rows: list[dict] = []
    empty_slot_rows: list[int] = []
    slot_count_mismatches: list[dict] = []

    slot_frequency: Counter[str] = Counter()

    multi_slot_rows = 0
    total_slot_annotations = 0

    # -------------------------------------------------------
    # Row-by-row schema validation
    # -------------------------------------------------------

    for index, row in enumerate(
        rows,
        start=1,
    ):
        text = row.get(
            text_column or "",
            "",
        )

        if not str(text).strip():
            empty_text_rows.append(index)

        raw_slots = row.get(
            slots_column or "",
            "",
        )

        try:
            slots = parse_slots(
                raw_slots
            )

        except ValueError as exc:
            invalid_slot_rows.append(
                {
                    "row": index,
                    "value": raw_slots,
                    "error": str(exc),
                }
            )

            continue

        if not slots:
            empty_slot_rows.append(index)
            continue

        total_slot_annotations += len(
            slots
        )

        if len(slots) > 1:
            multi_slot_rows += 1

        slot_frequency.update(
            slots
        )

        # Validate the existing slot_count column if present.
        slot_count_column = columns.get(
            "slot_count"
        )

        if slot_count_column:
            raw_count = str(
                row.get(
                    slot_count_column,
                    "",
                )
            ).strip()

            if raw_count:
                try:
                    expected_count = int(
                        float(raw_count)
                    )

                except ValueError:
                    slot_count_mismatches.append(
                        {
                            "row": index,
                            "declared": raw_count,
                            "parsed": len(slots),
                            "reason": (
                                "slot_count is not numeric"
                            ),
                        }
                    )

                else:
                    if expected_count != len(slots):
                        slot_count_mismatches.append(
                            {
                                "row": index,
                                "declared": expected_count,
                                "parsed": len(slots),
                            }
                        )

    if empty_text_rows:
        errors.append(
            "Rows with empty utterance text: "
            f"{empty_text_rows}"
        )

    if invalid_slot_rows:
        errors.append(
            "Rows with unrecognized final_slots: "
            f"{invalid_slot_rows}"
        )

    if empty_slot_rows:
        errors.append(
            "Rows with no final slot annotations: "
            f"{empty_slot_rows}"
        )

    if slot_count_mismatches:
        errors.append(
            "slot_count does not match parsed "
            "final_slots for: "
            f"{slot_count_mismatches}"
        )

    # -------------------------------------------------------
    # Verify split column
    # -------------------------------------------------------

    split_column = columns.get(
        "split"
    )

    split_values: Counter[str] = Counter()

    if split_column:
        for row in rows:
            value = str(
                row.get(
                    split_column,
                    "",
                )
            ).strip().lower()

            split_values[value] += 1

        non_test_values = {
            value: count
            for value, count
            in split_values.items()
            if value != "test"
        }

        if non_test_values:
            errors.append(
                "Frozen test.csv contains rows whose "
                "split is not 'test': "
                f"{non_test_values}"
            )

    else:
        warnings.append(
            "No split column was detected, so "
            "split='test' could not be verified."
        )

    # -------------------------------------------------------
    # Verify frozen safety-flag counts
    # -------------------------------------------------------

    flag_counts: dict[
        str,
        int | None,
    ] = {}

    for (
        flag,
        expected_count,
    ) in EXPECTED_FLAG_COUNTS.items():

        column = columns.get(flag)

        if column is None:
            flag_counts[flag] = None

            warnings.append(
                f"No column detected for {flag}; "
                "its frozen count could not be verified."
            )

            continue

        actual_count = 0

        for row in rows:
            value = parse_bool(
                row.get(column)
            )

            if value is True:
                actual_count += 1

        flag_counts[flag] = actual_count

        if actual_count != expected_count:
            errors.append(
                f"{flag}: expected frozen count "
                f"{expected_count}, "
                f"found {actual_count}."
            )

    return {
        "row_count": len(rows),

        "expected_row_count": (
            EXPECTED_TEST_ROW_COUNT
        ),

        "multi_slot_rows": multi_slot_rows,

        "total_slot_annotations": (
            total_slot_annotations
        ),

        "slot_frequency": dict(
            slot_frequency
        ),

        "flag_counts": flag_counts,

        "expected_flag_counts": (
            EXPECTED_FLAG_COUNTS
        ),

        "split_values": dict(
            split_values
        ),

        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def ensure_report_directory() -> Path:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return REPORT_DIR

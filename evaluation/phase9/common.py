from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

TEST_CSV = ROOT / "data" / "processed" / "phase5" / "test.csv"
REPORT_DIR = ROOT / "reports" / "phase9"


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


# These are the locked Phase 5 TEST-set totals from the split.
EXPECTED_FLAG_COUNTS = {
    "ambiguous": 7,
    "negated": 8,
    "uncertain": 2,
    "context_dependent": 21,
}


COLUMN_ALIASES = {
    "id": [
        "id",
        "row_id",
        "example_id",
        "utterance_id",
        "sample_id",
    ],
    "text": [
        "text",
        "utterance",
        "sentence",
        "patient_text",
        "example",
        "phrase",
    ],
    "slot": [
        "slot",
        "slot_label",
        "slot_name",
        "label",
        "attribute",
        "category",
        "final_label",
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
}


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


def normalize_column_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[\s\-]+", "_", value)
    return value


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    value = str(value)
    value = re.sub(r"\s+", " ", value.strip().lower())

    return value


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


def canonical_slot(value: Any) -> str | None:
    if value is None:
        return None

    raw = str(value).strip().lower()

    if not raw:
        return None

    normalized = raw.replace("-", " ").replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    if normalized in SLOT_ALIASES:
        return SLOT_ALIASES[normalized]

    underscored = normalized.replace(" ", "_")

    if underscored in CANONICAL_SLOTS:
        return underscored

    return None


def resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    normalized_lookup = {
        normalize_column_name(field): field
        for field in fieldnames
    }

    resolved: dict[str, str | None] = {}

    for logical_name, aliases in COLUMN_ALIASES.items():
        resolved[logical_name] = None

        for alias in aliases:
            normalized_alias = normalize_column_name(alias)

            if normalized_alias in normalized_lookup:
                resolved[logical_name] = normalized_lookup[normalized_alias]
                break

    return resolved


def load_test_rows() -> tuple[list[dict[str, str]], dict[str, str | None]]:
    if not TEST_CSV.exists():
        raise FileNotFoundError(
            f"Frozen Phase 5 TEST split was not found at:\n{TEST_CSV}"
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
        columns = resolve_columns(reader.fieldnames)

    if columns["text"] is None:
        raise RuntimeError(
            "Could not identify the text column in test.csv.\n"
            f"Columns found: {reader.fieldnames}"
        )

    if columns["slot"] is None:
        raise RuntimeError(
            "Could not identify the slot-label column in test.csv.\n"
            f"Columns found: {reader.fieldnames}"
        )

    return rows, columns


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

    return f"test-row-{fallback_index:03d}"


def audit_test_rows(
    rows: list[dict[str, str]],
    columns: dict[str, str | None],
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if len(rows) != 57:
        errors.append(
            f"Expected exactly 57 frozen TEST rows; found {len(rows)}."
        )

    slot_column = columns["slot"]
    text_column = columns["text"]

    invalid_slots: list[dict] = []
    empty_text_rows: list[int] = []

    for index, row in enumerate(rows, start=1):
        text = row.get(text_column or "", "")

        if not str(text).strip():
            empty_text_rows.append(index)

        slot = canonical_slot(
            row.get(slot_column or "")
        )

        if slot not in CANONICAL_SLOTS:
            invalid_slots.append(
                {
                    "row": index,
                    "raw_slot": row.get(slot_column or ""),
                }
            )

    if empty_text_rows:
        errors.append(
            f"Rows with empty text: {empty_text_rows}"
        )

    if invalid_slots:
        errors.append(
            f"Rows with unrecognized slot labels: {invalid_slots}"
        )

    flag_counts: dict[str, int | None] = {}

    for flag, expected_count in EXPECTED_FLAG_COUNTS.items():
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
            value = parse_bool(row.get(column))

            if value is True:
                actual_count += 1

        flag_counts[flag] = actual_count

        if actual_count != expected_count:
            errors.append(
                f"{flag}: expected frozen count "
                f"{expected_count}, found {actual_count}."
            )

    return {
        "row_count": len(rows),
        "expected_row_count": 57,
        "flag_counts": flag_counts,
        "expected_flag_counts": EXPECTED_FLAG_COUNTS,
        "errors": errors,
        "warnings": warnings,
    }


def ensure_report_directory() -> Path:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return REPORT_DIR

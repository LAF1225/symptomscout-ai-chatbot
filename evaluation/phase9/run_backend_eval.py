from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Import Phase 9 shared helpers
# ---------------------------------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(CURRENT_DIR),
    )

from common import (  # noqa: E402
    CANONICAL_SLOTS,
    ROOT,
    audit_test_rows,
    ensure_report_directory,
    load_test_rows,
    parse_bool,
    parse_slots,
    row_id,
)


# ---------------------------------------------------------------------------
# Import backend
# ---------------------------------------------------------------------------

BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIR),
    )

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


client = TestClient(app)


# ---------------------------------------------------------------------------
# Safety flags evaluated by the Phase 7 backend
# ---------------------------------------------------------------------------

FLAGS_TO_EVALUATE = [
    "ambiguous",
    "negated",
    "uncertain",
]


# ---------------------------------------------------------------------------
# Dialogflow webhook request
# ---------------------------------------------------------------------------

def make_request(
    slot: str,
    text: str,
) -> dict:
    """
    Build one Dialogflow CX webhook request.

    For multi-label corpus rows, slot is one deterministic
    representative annotated slot.

    This evaluator is testing Phase 7 text-signal handling,
    NOT Dialogflow multi-slot extraction.
    """

    return {
        "fulfillmentInfo": {
            "tag": f"slot.updated.{slot}",
        },

        "text": text,

        "sessionInfo": {
            "session": (
                "projects/test-project/"
                "locations/global/"
                "agents/test-agent/"
                "sessions/phase9-corpus-evaluation"
            ),

            "parameters": {
                slot: text,
            },
        },

        "pageInfo": {
            "formInfo": {
                "parameterInfo": [
                    {
                        "displayName": slot,
                        "value": text,
                        "justCollected": True,
                    }
                ]
            }
        },
    }


# ---------------------------------------------------------------------------
# Extract Phase 7 predicted flags
# ---------------------------------------------------------------------------

def extract_predicted_flag(
    parameters: dict[str, Any],
    slot: str,
    flag: str,
) -> bool:

    all_flags = parameters.get(
        "p7_slot_flags",
        {},
    )

    if not isinstance(
        all_flags,
        dict,
    ):
        return False

    slot_flags = all_flags.get(
        slot,
        {},
    )

    if isinstance(
        slot_flags,
        dict,
    ):
        value = slot_flags.get(
            flag,
            False,
        )

        if isinstance(value, bool):
            return value

        return bool(value)

    if isinstance(
        slot_flags,
        (list, tuple, set),
    ):
        return flag in slot_flags

    if isinstance(
        slot_flags,
        str,
    ):
        return flag == slot_flags

    return False


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def empty_confusion_matrix() -> dict[str, int]:
    return {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "tn": 0,
    }


def update_confusion_matrix(
    matrix: dict[str, int],
    expected: bool,
    predicted: bool,
) -> None:

    if expected and predicted:
        matrix["tp"] += 1

    elif not expected and predicted:
        matrix["fp"] += 1

    elif expected and not predicted:
        matrix["fn"] += 1

    else:
        matrix["tn"] += 1


def safe_divide(
    numerator: float,
    denominator: float,
) -> float | None:

    if denominator == 0:
        return None

    return numerator / denominator


def calculate_metrics(
    matrix: dict[str, int],
) -> dict[str, float | int | None]:

    tp = matrix["tp"]
    fp = matrix["fp"]
    fn = matrix["fn"]
    tn = matrix["tn"]

    precision = safe_divide(
        tp,
        tp + fp,
    )

    recall = safe_divide(
        tp,
        tp + fn,
    )

    if (
        precision is None
        or recall is None
        or precision + recall == 0
    ):
        f1 = None

    else:
        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )

    accuracy = safe_divide(
        tp + tn,
        tp + fp + fn + tn,
    )

    return {
        **matrix,

        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def percentage(
    value: float | None,
) -> str:

    if value is None:
        return "N/A"

    return f"{value * 100:.2f}%"


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def main() -> int:

    # -------------------------------------------------------
    # Load the frozen TEST split
    # -------------------------------------------------------

    rows, columns = load_test_rows()

    audit = audit_test_rows(
        rows,
        columns,
    )

    print()
    print(
        "Phase 9 frozen TEST-set audit"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Rows: {audit['row_count']} "
        f"(expected "
        f"{audit['expected_row_count']})"
    )

    print(
        "Total slot annotations: "
        f"{audit['total_slot_annotations']}"
    )

    print(
        "Multi-slot rows: "
        f"{audit['multi_slot_rows']}"
    )

    print()

    print("Slot frequencies:")

    for slot in CANONICAL_SLOTS:
        print(
            f"  {slot}: "
            f"{audit['slot_frequency'].get(slot, 0)}"
        )

    print()

    print("Frozen safety flags:")

    for (
        flag,
        count,
    ) in audit["flag_counts"].items():

        print(
            f"  {flag}: {count}"
        )

    for warning in audit["warnings"]:
        print(
            f"WARNING: {warning}"
        )

    if audit["errors"]:
        print()

        for error in audit["errors"]:
            print(
                f"ERROR: {error}"
            )

        print()
        print(
            "Evaluation stopped because the frozen "
            "TEST split did not pass its integrity audit."
        )

        return 2

    # -------------------------------------------------------
    # Initialize evaluation state
    # -------------------------------------------------------

    confusion = {
        flag: empty_confusion_matrix()
        for flag in FLAGS_TO_EVALUATE
    }

    evaluated_per_flag = {
        flag: 0
        for flag in FLAGS_TO_EVALUATE
    }

    results: list[dict] = []

    successful_requests = 0

    target_value_returned_unchanged = 0

    slots_column = columns["slots"]
    text_column = columns["text"]

    # -------------------------------------------------------
    # Evaluate each frozen row ONCE
    # -------------------------------------------------------

    for index, row in enumerate(
        rows,
        start=1,
    ):

        annotated_slots = parse_slots(
            row.get(
                slots_column or "",
                "",
            )
        )

        if not annotated_slots:
            raise RuntimeError(
                "TEST row "
                f"{index} has no annotated slots."
            )

        # ---------------------------------------------------
        # IMPORTANT:
        #
        # The safety labels are row-level.
        #
        # Therefore a multi-slot utterance must not be
        # counted repeatedly just because it contains
        # multiple symptom attributes.
        #
        # The first canonical annotation is used as the
        # deterministic webhook target.
        # ---------------------------------------------------

        target_slot = annotated_slots[0]

        text = str(
            row.get(
                text_column or "",
                "",
            )
        ).strip()

        response = client.post(
            "/dialogflow/webhook",

            json=make_request(
                slot=target_slot,
                text=text,
            ),
        )

        response_record = {
            "row_id": row_id(
                row,
                columns,
                index,
            ),

            "utterance": text,

            "annotated_slots": (
                annotated_slots
            ),

            "evaluation_target_slot": (
                target_slot
            ),

            "http_status": (
                response.status_code
            ),
        }

        # ---------------------------------------------------
        # HTTP failure
        # ---------------------------------------------------

        if response.status_code != 200:
            response_record["error"] = (
                response.text[:500]
            )

            results.append(
                response_record
            )

            print(
                f"[{index:02d}/{len(rows)}] "
                f"{target_slot}: HTTP "
                f"{response.status_code}"
            )

            continue

        successful_requests += 1

        # ---------------------------------------------------
        # Read webhook output parameters
        # ---------------------------------------------------

        body = response.json()

        parameters = (
            body
            .get(
                "sessionInfo",
                {},
            )
            .get(
                "parameters",
                {},
            )
        )

        # This is descriptive only.
        #
        # Ambiguous/control handling may intentionally clear
        # a slot, so this is NOT treated as an accuracy score.
        value_unchanged = (
            parameters.get(
                target_slot
            )
            == text
        )

        if value_unchanged:
            target_value_returned_unchanged += 1

        # ---------------------------------------------------
        # Evaluate row-level safety flags
        # ---------------------------------------------------

        expected_flags: dict[
            str,
            bool | None,
        ] = {}

        predicted_flags: dict[
            str,
            bool,
        ] = {}

        for flag in FLAGS_TO_EVALUATE:

            column = columns.get(
                flag
            )

            if column is None:
                expected = None

            else:
                expected = parse_bool(
                    row.get(column)
                )

            predicted = (
                extract_predicted_flag(
                    parameters=parameters,
                    slot=target_slot,
                    flag=flag,
                )
            )

            expected_flags[flag] = (
                expected
            )

            predicted_flags[flag] = (
                predicted
            )

            if expected is not None:

                evaluated_per_flag[
                    flag
                ] += 1

                update_confusion_matrix(
                    confusion[flag],
                    expected=expected,
                    predicted=predicted,
                )

        # ---------------------------------------------------
        # Save row result
        # ---------------------------------------------------

        response_record.update(
            {
                "p7_action": parameters.get(
                    "p7_action"
                ),

                "target_value_returned_unchanged": (
                    value_unchanged
                ),

                "expected_flags": (
                    expected_flags
                ),

                "predicted_flags": (
                    predicted_flags
                ),
            }
        )

        results.append(
            response_record
        )

        print(
            f"[{index:02d}/{len(rows)}] "
            f"{target_slot} "
            f"slots={annotated_slots} "
            f"action={parameters.get('p7_action')}"
        )

    # -------------------------------------------------------
    # Calculate metrics
    # -------------------------------------------------------

    metrics = {
        flag: calculate_metrics(
            confusion[flag]
        )
        for flag in FLAGS_TO_EVALUATE
    }

    summary = {
        "frozen_test_rows": len(rows),

        "total_slot_annotations": (
            audit[
                "total_slot_annotations"
            ]
        ),

        "multi_slot_rows": (
            audit[
                "multi_slot_rows"
            ]
        ),

        "successful_webhook_requests": (
            successful_requests
        ),

        "target_value_returned_unchanged_count": (
            target_value_returned_unchanged
        ),

        "flag_metrics": metrics,
    }

    # -------------------------------------------------------
    # Full machine-readable report
    # -------------------------------------------------------

    report = {
        "phase": 9,

        "evaluation": (
            "backend_signal_evaluation"
        ),

        "method": (
            "Each frozen TEST utterance is evaluated "
            "once. For multi-label rows, the first "
            "canonical final_slots annotation is used "
            "as a deterministic webhook target. "
            "Safety labels remain row-level."
        ),

        "audit": audit,

        "columns_detected": columns,

        "summary": summary,

        "rows": results,
    }

    report_dir = (
        ensure_report_directory()
    )

    json_path = (
        report_dir
        / "backend_eval.json"
    )

    markdown_path = (
        report_dir
        / "backend_eval.md"
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),

        encoding="utf-8",
    )

    # -------------------------------------------------------
    # Human-readable Markdown report
    # -------------------------------------------------------

    lines = [
        "# Phase 9 Backend Evaluation",
        "",
        "## Frozen TEST split",
        "",
        f"- Rows: {len(rows)}",
        (
            "- Total annotated symptom slots: "
            f"{audit['total_slot_annotations']}"
        ),
        (
            "- Multi-slot utterances: "
            f"{audit['multi_slot_rows']}"
        ),
        (
            "- Successful webhook requests: "
            f"{successful_requests}/{len(rows)}"
        ),
        "",
        "## Slot distribution",
        "",
        "| Slot | Annotations |",
        "|---|---:|",
    ]

    for slot in CANONICAL_SLOTS:
        lines.append(
            f"| {slot} "
            f"| {audit['slot_frequency'].get(slot, 0)} |"
        )

    lines.extend(
        [
            "",
            "## Safety-signal classification",
            "",
            (
                "| Flag | Precision | Recall | F1 "
                "| Accuracy | TP | FP | FN | TN |"
            ),
            (
                "|---|---:|---:|---:|---:|"
                "---:|---:|---:|---:|"
            ),
        ]
    )

    for flag in FLAGS_TO_EVALUATE:

        metric = metrics[flag]

        lines.append(
            "| "
            + flag
            + " | "
            + percentage(
                metric["precision"]
            )
            + " | "
            + percentage(
                metric["recall"]
            )
            + " | "
            + percentage(
                metric["f1"]
            )
            + " | "
            + percentage(
                metric["accuracy"]
            )
            + f" | {metric['tp']}"
            + f" | {metric['fp']}"
            + f" | {metric['fn']}"
            + f" | {metric['tn']} |"
        )

    lines.extend(
        [
            "",
            "## Evaluation method",
            "",
            (
                "The Phase 5 corpus is multi-label: "
                "one utterance may contain more than one "
                "symptom attribute in final_slots."
            ),
            "",
            (
                "The ambiguity, negation and uncertainty "
                "labels are evaluated once per utterance. "
                "For the webhook call, the first annotated "
                "canonical slot is used as a deterministic "
                "target. This avoids weighting a multi-slot "
                "utterance multiple times."
            ),
            "",
            (
                "This evaluation measures Phase 7 backend "
                "signal handling. It does not measure "
                "Dialogflow CX slot extraction or "
                "conversation-level multi-slot extraction."
            ),
            "",
        ]
    )

    markdown_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # -------------------------------------------------------
    # Console summary
    # -------------------------------------------------------

    print()
    print(
        "Backend evaluation complete."
    )

    print()

    print(
        f"JSON: {json_path}"
    )

    print(
        f"Markdown: {markdown_path}"
    )

    print()
    print("Metrics:")

    for (
        flag,
        metric,
    ) in metrics.items():

        print(
            f"  {flag}: "
            f"precision="
            f"{percentage(metric['precision'])}, "
            f"recall="
            f"{percentage(metric['recall'])}, "
            f"F1="
            f"{percentage(metric['f1'])}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from common import (  # noqa: E402
    CANONICAL_SLOTS,
    ROOT,
    audit_test_rows,
    canonical_slot,
    ensure_report_directory,
    load_test_rows,
    parse_bool,
    row_id,
)


BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


client = TestClient(app)


FLAGS_TO_EVALUATE = [
    "ambiguous",
    "negated",
    "uncertain",
]


def make_request(
    slot: str,
    text: str,
) -> dict:
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


def extract_predicted_flag(
    parameters: dict[str, Any],
    slot: str,
    flag: str,
) -> bool:
    all_flags = parameters.get(
        "p7_slot_flags",
        {},
    )

    if not isinstance(all_flags, dict):
        return False

    slot_flags = all_flags.get(slot, {})

    if isinstance(slot_flags, dict):
        value = slot_flags.get(flag, False)

        if isinstance(value, bool):
            return value

        return bool(value)

    if isinstance(slot_flags, (list, tuple, set)):
        return flag in slot_flags

    if isinstance(slot_flags, str):
        return flag == slot_flags

    return False


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


def percentage(value: float | None) -> str:
    if value is None:
        return "N/A"

    return f"{value * 100:.2f}%"


def main() -> int:
    rows, columns = load_test_rows()
    audit = audit_test_rows(
        rows,
        columns,
    )

    print("Phase 9 frozen TEST-set audit")
    print("--------------------------------")

    print(
        f"Rows: {audit['row_count']} "
        f"(expected {audit['expected_row_count']})"
    )

    for flag, count in audit["flag_counts"].items():
        print(
            f"{flag}: {count}"
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

        print(
            "\nEvaluation stopped because the frozen "
            "TEST split did not pass its integrity audit."
        )

        return 2

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
    preserved_values = 0

    slot_column = columns["slot"]
    text_column = columns["text"]

    for index, row in enumerate(
        rows,
        start=1,
    ):
        slot = canonical_slot(
            row.get(slot_column or "")
        )

        text = str(
            row.get(text_column or "", "")
        ).strip()

        if slot not in CANONICAL_SLOTS:
            raise RuntimeError(
                f"Invalid slot in TEST row {index}: "
                f"{row.get(slot_column or '')!r}"
            )

        response = client.post(
            "/dialogflow/webhook",
            json=make_request(
                slot=slot,
                text=text,
            ),
        )

        response_record = {
            "row_id": row_id(
                row,
                columns,
                index,
            ),
            "slot": slot,
            "http_status": response.status_code,
        }

        if response.status_code != 200:
            response_record["error"] = (
                response.text[:500]
            )

            results.append(
                response_record
            )

            continue

        successful_requests += 1

        body = response.json()

        parameters = (
            body.get("sessionInfo", {})
            .get("parameters", {})
        )

        if parameters.get(slot) == text:
            preserved_values += 1

        expected_flags: dict[str, bool | None] = {}
        predicted_flags: dict[str, bool] = {}

        for flag in FLAGS_TO_EVALUATE:
            column = columns.get(flag)

            if column is None:
                expected = None
            else:
                expected = parse_bool(
                    row.get(column)
                )

            predicted = extract_predicted_flag(
                parameters=parameters,
                slot=slot,
                flag=flag,
            )

            expected_flags[flag] = expected
            predicted_flags[flag] = predicted

            if expected is not None:
                evaluated_per_flag[flag] += 1

                update_confusion_matrix(
                    confusion[flag],
                    expected=expected,
                    predicted=predicted,
                )

        response_record.update(
            {
                "p7_action": parameters.get(
                    "p7_action"
                ),
                "expected_flags": expected_flags,
                "predicted_flags": predicted_flags,
            }
        )

        results.append(
            response_record
        )

    metrics = {
        flag: calculate_metrics(
            confusion[flag]
        )
        for flag in FLAGS_TO_EVALUATE
    }

    summary = {
        "frozen_test_rows": len(rows),
        "successful_webhook_requests": successful_requests,
        "slot_value_preserved_count": preserved_values,
        "slot_value_preservation_rate": safe_divide(
            preserved_values,
            len(rows),
        ),
        "flag_metrics": metrics,
    }

    report = {
        "phase": 9,
        "evaluation": "backend_signal_evaluation",
        "audit": audit,
        "columns_detected": columns,
        "summary": summary,
        "rows": results,
    }

    report_dir = ensure_report_directory()

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
        ),
        encoding="utf-8",
    )

    lines = [
        "# Phase 9 Backend Evaluation",
        "",
        "## Frozen TEST split",
        "",
        f"- Rows: {len(rows)}",
        (
            "- Successful webhook requests: "
            f"{successful_requests}/{len(rows)}"
        ),
        (
            "- Slot-value preservation: "
            f"{percentage(summary['slot_value_preservation_rate'])}"
        ),
        "",
        "## Safety-signal classification",
        "",
        "| Flag | Precision | Recall | F1 | Accuracy | TP | FP | FN | TN |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for flag in FLAGS_TO_EVALUATE:
        metric = metrics[flag]

        lines.append(
            "| "
            + flag
            + " | "
            + percentage(metric["precision"])
            + " | "
            + percentage(metric["recall"])
            + " | "
            + percentage(metric["f1"])
            + " | "
            + percentage(metric["accuracy"])
            + f" | {metric['tp']}"
            + f" | {metric['fp']}"
            + f" | {metric['fn']}"
            + f" | {metric['tn']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This evaluation tests the Phase 7 backend signal "
                "handling against the frozen Phase 5 TEST split. "
                "It does not independently measure Dialogflow CX "
                "form/entity extraction; that is evaluated separately."
            ),
            "",
        ]
    )

    markdown_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("Backend evaluation complete.")
    print(
        f"JSON: {json_path}"
    )
    print(
        f"Markdown: {markdown_path}"
    )

    print()
    print("Metrics:")

    for flag, metric in metrics.items():
        print(
            f"{flag}: "
            f"precision={percentage(metric['precision'])}, "
            f"recall={percentage(metric['recall'])}, "
            f"F1={percentage(metric['f1'])}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

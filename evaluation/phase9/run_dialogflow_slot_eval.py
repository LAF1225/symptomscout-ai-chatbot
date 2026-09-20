from __future__ import annotations

import json
import os
import sys
import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from google.api_core.client_options import ClientOptions
from google.cloud import dialogflowcx_v3 as dialogflow
from google.protobuf.json_format import MessageToDict


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
    PAGE_FOR_SLOT,
    audit_test_rows,
    ensure_report_directory,
    load_test_rows,
    normalize_text,
    parse_slots,
    row_id,
)


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def required_environment_variable(
    name: str,
) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Environment variable {name} is required."
        )

    return value


def dialogflow_endpoint(
    location: str,
) -> str:
    """
    Dialogflow CX uses the global endpoint for global agents and
    region-specific endpoints for regional agents.
    """

    if location == "global":
        return "dialogflow.googleapis.com"

    return (
        f"{location}-dialogflow.googleapis.com"
    )


# ---------------------------------------------------------------------------
# Dialogflow clients
# ---------------------------------------------------------------------------

def build_clients(
    location: str,
):
    options = ClientOptions(
        api_endpoint=dialogflow_endpoint(
            location
        )
    )

    flows_client = dialogflow.FlowsClient(
        client_options=options
    )

    pages_client = dialogflow.PagesClient(
        client_options=options
    )

    sessions_client = dialogflow.SessionsClient(
        client_options=options
    )

    return (
        flows_client,
        pages_client,
        sessions_client,
    )


# ---------------------------------------------------------------------------
# Discover Dialogflow pages
# ---------------------------------------------------------------------------

def discover_pages(
    project_id: str,
    location: str,
    agent_id: str,
    flows_client: dialogflow.FlowsClient,
    pages_client: dialogflow.PagesClient,
) -> dict[str, str]:
    """
    Return a mapping of Dialogflow page display names to resource names.

    Example:

        {
            "Collect Site": ".../pages/<id>",
            "Collect Onset": ".../pages/<id>",
            ...
        }
    """

    agent_path = (
        f"projects/{project_id}/"
        f"locations/{location}/"
        f"agents/{agent_id}"
    )

    page_lookup: dict[str, str] = {}

    duplicate_names: dict[
        str,
        list[str],
    ] = defaultdict(list)

    flows = flows_client.list_flows(
        request={
            "parent": agent_path,
        }
    )

    for flow in flows:
        pages = pages_client.list_pages(
            request={
                "parent": flow.name,
            }
        )

        for page in pages:
            display_name = (
                page.display_name.strip()
            )

            duplicate_names[
                display_name
            ].append(
                page.name
            )

            if (
                display_name
                not in page_lookup
            ):
                page_lookup[
                    display_name
                ] = page.name

    actual_duplicates = {
        name: resources
        for name, resources
        in duplicate_names.items()
        if len(resources) > 1
    }

    if actual_duplicates:
        required_duplicate_pages = {
            name: resources
            for name, resources
            in actual_duplicates.items()
            if name in PAGE_FOR_SLOT.values()
        }

        if required_duplicate_pages:
            raise RuntimeError(
                "Duplicate required collection-page "
                "display names were found:\n"
                + json.dumps(
                    required_duplicate_pages,
                    indent=2,
                )
            )

    return page_lookup


# ---------------------------------------------------------------------------
# Proto Plus / protobuf conversion helpers
# ---------------------------------------------------------------------------

def protobuf_value_to_python(
    value: Any,
) -> Any:
    """
    Convert values returned by the current Google Cloud client
    into ordinary Python values.

    Dialogflow CX query_result.parameters may be returned as a
    proto-plus MapComposite rather than a raw protobuf Struct.
    """

    if value is None:
        return None

    # -------------------------------------------------------
    # MapComposite, dict, and other mapping-style objects
    # -------------------------------------------------------

    if isinstance(value, Mapping) or hasattr(
        value,
        "items",
    ):
        try:
            return {
                str(key): protobuf_value_to_python(
                    item
                )
                for key, item in value.items()
            }
        except (
            TypeError,
            AttributeError,
        ):
            pass

    # -------------------------------------------------------
    # Sequence / repeated values
    # -------------------------------------------------------

    if (
        isinstance(
            value,
            Sequence,
        )
        and not isinstance(
            value,
            (
                str,
                bytes,
                bytearray,
            ),
        )
    ):
        return [
            protobuf_value_to_python(
                item
            )
            for item in value
        ]

    class_name = (
        type(value).__name__.lower()
    )

    if (
        "repeated" in class_name
        or "listcomposite" in class_name
    ):
        try:
            return [
                protobuf_value_to_python(
                    item
                )
                for item in value
            ]
        except TypeError:
            pass

    # -------------------------------------------------------
    # Raw protobuf Message
    # -------------------------------------------------------

    if hasattr(
        value,
        "DESCRIPTOR",
    ):
        converted = MessageToDict(
            value,
            preserving_proto_field_name=True,
        )

        return protobuf_value_to_python(
            converted
        )

    # -------------------------------------------------------
    # Proto Plus wrapper exposing raw protobuf via _pb
    # -------------------------------------------------------

    underlying_pb = getattr(
        value,
        "_pb",
        None,
    )

    if (
        underlying_pb is not None
        and hasattr(
            underlying_pb,
            "DESCRIPTOR",
        )
    ):
        converted = MessageToDict(
            underlying_pb,
            preserving_proto_field_name=True,
        )

        return protobuf_value_to_python(
            converted
        )

    # -------------------------------------------------------
    # Ordinary scalar
    # -------------------------------------------------------

    return value


def protobuf_struct_to_dict(
    value: Any,
) -> dict[str, Any]:
    """
    Convert Dialogflow session parameters into an ordinary dict.

    Handles:
    - proto-plus MapComposite
    - protobuf Struct
    - ordinary dict
    """

    if value is None:
        return {}

    converted = protobuf_value_to_python(
        value
    )

    if not isinstance(
        converted,
        dict,
    ):
        raise TypeError(
            "Dialogflow query_result.parameters was expected "
            "to be mapping-like, but converted to "
            f"{type(converted).__name__}: {converted!r}"
        )

    return converted


# ---------------------------------------------------------------------------
# Value helpers
# ---------------------------------------------------------------------------

def has_value(
    value: Any,
) -> bool:
    """
    Determine whether Dialogflow returned a meaningful value for
    the target session parameter.
    """

    if value is None:
        return False

    if isinstance(
        value,
        str,
    ):
        return bool(
            value.strip()
        )

    if isinstance(
        value,
        (
            list,
            tuple,
            dict,
        ),
    ):
        return len(value) > 0

    return True


def value_as_text(
    value: Any,
) -> str:
    """
    Convert a Dialogflow parameter value into a stable textual form
    for exact-text comparison.
    """

    if value is None:
        return ""

    if isinstance(
        value,
        list,
    ):
        return " ".join(
            str(item)
            for item in value
        )

    if isinstance(
        value,
        dict,
    ):
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
        )

    return str(value)


def percentage(
    numerator: int,
    denominator: int,
) -> str:
    if denominator == 0:
        return "N/A"

    return (
        f"{numerator / denominator * 100:.2f}%"
    )


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def main() -> int:

    # -------------------------------------------------------
    # Load environment configuration
    # -------------------------------------------------------

    project_id = required_environment_variable(
        "DIALOGFLOW_PROJECT_ID"
    )

    location = required_environment_variable(
        "DIALOGFLOW_LOCATION_ID"
    )

    agent_id = required_environment_variable(
        "DIALOGFLOW_AGENT_ID"
    )

    language_code = os.getenv(
        "DIALOGFLOW_LANGUAGE_CODE",
        "en",
    )

    # -------------------------------------------------------
    # Load frozen TEST split
    # -------------------------------------------------------

    rows, columns = load_test_rows()

    audit = audit_test_rows(
        rows,
        columns,
    )

    print()
    print(
        "Phase 9 Dialogflow TEST-set audit"
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
        "Total annotated slot pairs: "
        f"{audit['total_slot_annotations']}"
    )

    print(
        "Multi-slot rows: "
        f"{audit['multi_slot_rows']}"
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
            "Evaluation stopped because the "
            "frozen TEST split failed its "
            "integrity audit."
        )

        return 2

    # -------------------------------------------------------
    # Build Dialogflow clients
    # -------------------------------------------------------

    (
        flows_client,
        pages_client,
        sessions_client,
    ) = build_clients(
        location
    )

    # -------------------------------------------------------
    # Discover collection pages
    # -------------------------------------------------------

    print()
    print(
        "Discovering Dialogflow collection pages..."
    )

    page_lookup = discover_pages(
        project_id=project_id,
        location=location,
        agent_id=agent_id,
        flows_client=flows_client,
        pages_client=pages_client,
    )

    required_pages = set(
        PAGE_FOR_SLOT.values()
    )

    missing_pages = sorted(
        page_name
        for page_name
        in required_pages
        if page_name not in page_lookup
    )

    if missing_pages:
        print()
        print(
            "The evaluator could not find these "
            "required Dialogflow pages:"
        )

        for page in missing_pages:
            print(
                f"  - {page}"
            )

        print()
        print(
            "Pages actually discovered:"
        )

        for page in sorted(
            page_lookup
        ):
            print(
                f"  - {page}"
            )

        return 3

    print(
        "All required collection pages found."
    )

    # -------------------------------------------------------
    # Evaluation state
    # -------------------------------------------------------

    text_column = columns["text"]
    slots_column = columns["slots"]

    pair_results: list[dict] = []

    per_slot = defaultdict(
        lambda: {
            "pairs": 0,
            "successful_requests": 0,
            "filled": 0,
            "exact": 0,
            "errors": 0,
        }
    )

    row_results: dict[
        str,
        dict,
    ] = {}

    total_pairs = (
        audit[
            "total_slot_annotations"
        ]
    )

    successful_requests = 0
    filled_count = 0
    exact_count = 0

    pair_number = 0

    # -------------------------------------------------------
    # Evaluate each (utterance, annotated_slot) pair
    # independently.
    # -------------------------------------------------------

    for row_index, row in enumerate(
        rows,
        start=1,
    ):

        current_row_id = row_id(
            row,
            columns,
            row_index,
        )

        text = str(
            row.get(
                text_column or "",
                "",
            )
        ).strip()

        annotated_slots = parse_slots(
            row.get(
                slots_column or "",
                "",
            )
        )

        row_results[
            current_row_id
        ] = {
            "row_id": current_row_id,
            "utterance": text,
            "annotated_slots": (
                annotated_slots
            ),
            "pair_count": len(
                annotated_slots
            ),
            "filled_slots": [],
            "exact_slots": [],
            "failed_slots": [],
        }

        for slot in annotated_slots:

            pair_number += 1

            if slot not in CANONICAL_SLOTS:
                raise RuntimeError(
                    "Unexpected canonical slot "
                    f"{slot!r} in TEST row "
                    f"{row_index}."
                )

            per_slot[
                slot
            ]["pairs"] += 1

            page_display_name = (
                PAGE_FOR_SLOT[
                    slot
                ]
            )

            page_resource_name = (
                page_lookup[
                    page_display_name
                ]
            )

            # Fresh session per slot pair.
            session_id = (
                "p9-"
                + uuid.uuid4().hex[:28]
            )

            session_name = (
                f"projects/{project_id}/"
                f"locations/{location}/"
                f"agents/{agent_id}/"
                f"sessions/{session_id}"
            )

            # ------------------------------------------------
            # Send exact frozen utterance
            # ------------------------------------------------

            query_input = (
                dialogflow.QueryInput(
                    text=dialogflow.TextInput(
                        text=text
                    ),
                    language_code=(
                        language_code
                    ),
                )
            )

            # ------------------------------------------------
            # Isolate Dialogflow form/entity collection
            # from Phase 7 backend behavior.
            # ------------------------------------------------

            query_params = (
                dialogflow.QueryParameters(
                    current_page=(
                        page_resource_name
                    ),
                    disable_webhook=True,
                )
            )

            request = (
                dialogflow.DetectIntentRequest(
                    session=session_name,
                    query_input=query_input,
                    query_params=query_params,
                )
            )

            record = {
                "row_id": current_row_id,
                "row_index": row_index,
                "pair_index": (
                    pair_number
                ),
                "utterance": text,
                "all_annotated_slots": (
                    annotated_slots
                ),
                "target_slot": slot,
                "target_page": (
                    page_display_name
                ),
            }

            # ------------------------------------------------
            # Call Dialogflow
            # ------------------------------------------------

            try:
                response = (
                    sessions_client
                    .detect_intent(
                        request=request
                    )
                )

            except Exception as exc:

                record["error"] = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                per_slot[
                    slot
                ]["errors"] += 1

                row_results[
                    current_row_id
                ][
                    "failed_slots"
                ].append(
                    slot
                )

                pair_results.append(
                    record
                )

                print(
                    f"[{pair_number:03d}/"
                    f"{total_pairs}] "
                    f"row={row_index:02d} "
                    f"slot={slot}: "
                    "REQUEST ERROR"
                )

                continue

            successful_requests += 1

            per_slot[
                slot
            ][
                "successful_requests"
            ] += 1

            # ------------------------------------------------
            # Extract returned session parameters
            # ------------------------------------------------

            parameters = (
                protobuf_struct_to_dict(
                    response
                    .query_result
                    .parameters
                )
            )

            predicted_value = (
                parameters.get(
                    slot
                )
            )

            filled = has_value(
                predicted_value
            )

            predicted_text = (
                value_as_text(
                    predicted_value
                )
            )

            exact = (
                filled
                and normalize_text(
                    predicted_text
                )
                == normalize_text(
                    text
                )
            )

            if filled:
                filled_count += 1

                per_slot[
                    slot
                ]["filled"] += 1

                row_results[
                    current_row_id
                ][
                    "filled_slots"
                ].append(
                    slot
                )

            else:
                row_results[
                    current_row_id
                ][
                    "failed_slots"
                ].append(
                    slot
                )

            if exact:
                exact_count += 1

                per_slot[
                    slot
                ]["exact"] += 1

                row_results[
                    current_row_id
                ][
                    "exact_slots"
                ].append(
                    slot
                )

            returned_page = None

            if (
                response
                .query_result
                .current_page
                is not None
            ):
                returned_page = (
                    response
                    .query_result
                    .current_page
                    .display_name
                )

            record.update(
                {
                    "request_success": True,
                    "filled": filled,
                    "returned_value": (
                        predicted_value
                    ),
                    "exact_text_preservation": (
                        exact
                    ),
                    "returned_page": (
                        returned_page
                    ),
                }
            )

            pair_results.append(
                record
            )

            print(
                f"[{pair_number:03d}/"
                f"{total_pairs}] "
                f"row={row_index:02d} "
                f"slot={slot}: "
                f"filled={filled}, "
                f"exact={exact}"
            )

    # -------------------------------------------------------
    # Row-level aggregation
    # -------------------------------------------------------

    rows_all_slots_filled = 0
    rows_all_slots_exact = 0

    for result in row_results.values():

        annotated = set(
            result[
                "annotated_slots"
            ]
        )

        filled = set(
            result[
                "filled_slots"
            ]
        )

        exact = set(
            result[
                "exact_slots"
            ]
        )

        all_filled = (
            annotated == filled
        )

        all_exact = (
            annotated == exact
        )

        result[
            "all_annotated_slots_filled"
        ] = all_filled

        result[
            "all_annotated_slots_exact"
        ] = all_exact

        if all_filled:
            rows_all_slots_filled += 1

        if all_exact:
            rows_all_slots_exact += 1

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------

    summary = {
        "frozen_test_rows": len(
            rows
        ),

        "total_annotated_slot_pairs": (
            total_pairs
        ),

        "multi_slot_rows": (
            audit[
                "multi_slot_rows"
            ]
        ),

        "successful_api_requests": (
            successful_requests
        ),

        "slot_pair_filled_count": (
            filled_count
        ),

        "slot_pair_fill_rate": (
            filled_count / total_pairs
            if total_pairs
            else None
        ),

        "slot_pair_exact_text_count": (
            exact_count
        ),

        "slot_pair_exact_text_rate": (
            exact_count / total_pairs
            if total_pairs
            else None
        ),

        "rows_all_annotated_slots_filled": (
            rows_all_slots_filled
        ),

        "row_all_slots_fill_rate": (
            rows_all_slots_filled
            / len(rows)
            if rows
            else None
        ),

        "rows_all_annotated_slots_exact": (
            rows_all_slots_exact
        ),

        "row_all_slots_exact_rate": (
            rows_all_slots_exact
            / len(rows)
            if rows
            else None
        ),

        "per_slot": dict(
            per_slot
        ),
    }

    # -------------------------------------------------------
    # Machine-readable report
    # -------------------------------------------------------

    report = {
        "phase": 9,

        "evaluation": (
            "dialogflow_slot_collection_evaluation"
        ),

        "method": (
            "Each (utterance, annotated slot) pair "
            "from the multi-label Phase 5 frozen TEST "
            "split is evaluated independently. A fresh "
            "Dialogflow CX session is placed directly "
            "on the collection page for that slot. "
            "Webhook execution is disabled so this "
            "measures Dialogflow form/entity capture "
            "separately from Phase 7 backend logic."
        ),

        "project_id": project_id,
        "location": location,
        "agent_id": agent_id,
        "language_code": (
            language_code
        ),

        "webhook_disabled": True,

        "audit": audit,

        "summary": summary,

        "rows": list(
            row_results.values()
        ),

        "slot_pairs": (
            pair_results
        ),
    }

    report_dir = (
        ensure_report_directory()
    )

    json_path = (
        report_dir
        / "dialogflow_slot_eval.json"
    )

    markdown_path = (
        report_dir
        / "dialogflow_slot_eval.md"
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
    # Markdown report
    # -------------------------------------------------------

    lines = [
        "# Phase 9 Dialogflow Slot Evaluation",
        "",
        "## Frozen TEST split",
        "",
        (
            f"- Utterances: "
            f"{len(rows)}"
        ),
        (
            "- Annotated slot pairs: "
            f"{total_pairs}"
        ),
        (
            "- Multi-slot utterances: "
            f"{audit['multi_slot_rows']}"
        ),
        "",
        "## Overall pair-level results",
        "",
        (
            "- Successful Dialogflow API requests: "
            f"{successful_requests}/{total_pairs}"
        ),
        (
            "- Annotated slot captured on its "
            "collection page: "
            f"{filled_count}/{total_pairs} "
            f"({percentage(filled_count, total_pairs)})"
        ),
        (
            "- Exact utterance preserved as the "
            "parameter value: "
            f"{exact_count}/{total_pairs} "
            f"({percentage(exact_count, total_pairs)})"
        ),
        "",
        "## Row-level results",
        "",
        (
            "- Utterances for which every annotated "
            "slot was capturable: "
            f"{rows_all_slots_filled}/{len(rows)} "
            f"({percentage(rows_all_slots_filled, len(rows))})"
        ),
        (
            "- Utterances for which every annotated "
            "slot exactly preserved the utterance: "
            f"{rows_all_slots_exact}/{len(rows)} "
            f"({percentage(rows_all_slots_exact, len(rows))})"
        ),
        "",
        "## Per-slot results",
        "",
        (
            "| Slot | Pairs | Successful requests "
            "| Filled | Fill rate | Exact | Exact rate "
            "| Errors |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|---:|"
        ),
    ]

    for slot in CANONICAL_SLOTS:

        values = (
            per_slot[
                slot
            ]
        )

        pairs = (
            values[
                "pairs"
            ]
        )

        lines.append(
            f"| {slot} "
            f"| {pairs} "
            f"| {values['successful_requests']} "
            f"| {values['filled']} "
            f"| {percentage(values['filled'], pairs)} "
            f"| {values['exact']} "
            f"| {percentage(values['exact'], pairs)} "
            f"| {values['errors']} |"
        )

    lines.extend(
        [
            "",
            "## Method",
            "",
            (
                "The Phase 5 corpus is multi-label. "
                "A single utterance may therefore have "
                "multiple entries in final_slots."
            ),
            "",
            (
                "Each annotated slot is evaluated "
                "independently using a fresh Dialogflow "
                "session positioned on the corresponding "
                "collection page."
            ),
            "",
            (
                "Webhook execution is disabled. "
                "This prevents Phase 7 backend behavior "
                "from affecting the Dialogflow extraction "
                "measurement."
            ),
            "",
            (
                "Because the current MVP uses permissive "
                "free-text collection for several fields, "
                "slot-fill performance should not be "
                "interpreted as semantic medical entity "
                "normalization accuracy."
            ),
            "",
        ]
    )

    markdown_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    # -------------------------------------------------------
    # Console summary
    # -------------------------------------------------------

    print()
    print(
        "Dialogflow evaluation complete."
    )

    print()

    print(
        "Annotated slot pairs filled: "
        f"{filled_count}/{total_pairs} "
        f"({percentage(filled_count, total_pairs)})"
    )

    print(
        "Exact text preservation: "
        f"{exact_count}/{total_pairs} "
        f"({percentage(exact_count, total_pairs)})"
    )

    print(
        "Rows with every annotated slot filled: "
        f"{rows_all_slots_filled}/{len(rows)} "
        f"({percentage(rows_all_slots_filled, len(rows))})"
    )

    print()

    print(
        f"JSON: {json_path}"
    )

    print(
        f"Markdown: {markdown_path}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

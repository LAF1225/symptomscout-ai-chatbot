from __future__ import annotations

from typing import Any

from dialogflow_contract import WebhookRequest
from summary_builder import build_summary


TAG_BUILD_SUMMARY = (
    "p8.build_summary"
)

TAG_CONFIRM_SUMMARY = (
    "p8.confirm_summary"
)

TAG_REQUEST_CORRECTION = (
    "p8.request_correction"
)


PHASE8_TAGS = {
    TAG_BUILD_SUMMARY,
    TAG_CONFIRM_SUMMARY,
    TAG_REQUEST_CORRECTION,
}


def handles_phase8_tag(
    tag: str | None,
) -> bool:
    """
    Return True when this webhook request belongs
    to Phase 8 rather than the Phase 7 controller.
    """

    return (
        (tag or "").strip()
        in PHASE8_TAGS
    )


def _text_response(
    message: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a valid Dialogflow CX standard
    WebhookResponse.

    REPLACE prevents an old queued placeholder
    response from being shown together with the
    generated Phase 8 summary.
    """

    return {
        "fulfillmentResponse": {
            "messages": [
                {
                    "text": {
                        "text": [
                            message
                        ],
                    }
                }
            ],
            "mergeBehavior": "REPLACE",
        },
        "sessionInfo": {
            "parameters": updates,
        },
    }


def _build_summary_response(
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Create the review summary when the user enters
    Review Information.
    """

    summary = build_summary(parameters)

    updates = {
        "p8_action": "review",

        "p8_summary_version": (
            summary["data"][
                "schema_version"
            ]
        ),

        "p8_summary_data": (
            summary["data"]
        ),

        "p8_summary_text": (
            summary["body"]
        ),

        "p8_summary_fingerprint": (
            summary["fingerprint"]
        ),

        "p8_summary_ready": (
            summary["ready"]
        ),

        "p8_summary_confirmed": False,

        "p8_summary_status": (
            "awaiting_confirmation"
            if summary["ready"]
            else "empty"
        ),

        # Setting a parameter to None in a
        # Dialogflow webhook response removes it.
        # This prevents an older confirmed summary
        # surviving after a new review begins.
        "p8_confirmed_summary": None,
    }

    if summary["ready"]:

        message = (
            summary["review_message"]
        )

    else:

        message = (
            "I do not have any symptom "
            "information to review yet. "
            "Please return to symptom collection "
            "and provide at least your main symptom."
        )

    return _text_response(
        message,
        updates,
    )


def _confirm_summary_response(
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Confirm only the exact summary the patient
    previously reviewed.
    """

    current = build_summary(parameters)

    stored_fingerprint = parameters.get(
        "p8_summary_fingerprint"
    )

    stored_ready = (
        parameters.get(
            "p8_summary_ready"
        )
        is True
    )

    if (
        not current["ready"]
        or not stored_ready
        or not stored_fingerprint
        or stored_fingerprint
        != current["fingerprint"]
    ):

        updates = {
            "p8_action": (
                "refresh_required"
            ),
            "p8_summary_confirmed": False,
            "p8_summary_status": "stale",
        }

        message = (
            "The symptom information changed "
            "after the summary was created, "
            "so I will not mark the old summary "
            "as confirmed. Please review the "
            "refreshed summary first."
        )

        return _text_response(
            message,
            updates,
        )

    updates = {
        "p8_action": "confirmed",
        "p8_summary_confirmed": True,
        "p8_summary_status": (
            "confirmed"
        ),
        "p8_confirmed_summary": (
            current["body"]
        ),
    }

    message = (
        "Thanks. I’ve marked this symptom "
        "summary as confirmed.\n\n"
        f"{current['body']}"
    )

    return _text_response(
        message,
        updates,
    )


def _request_correction_response(
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove confirmation whenever the patient asks
    to change the summary.
    """

    updates = {
        "p8_action": (
            "correction_requested"
        ),

        "p8_summary_confirmed": False,

        "p8_summary_status": (
            "needs_correction"
        ),

        "p8_confirmed_summary": None,
    }

    message = (
        "Okay. Tell me which part you want "
        "to change, and I’ll return you to "
        "the relevant symptom question."
    )

    return _text_response(
        message,
        updates,
    )


def process_phase8_webhook(
    request: WebhookRequest,
) -> dict[str, Any]:
    """
    Main Phase 8 webhook dispatcher.
    """

    tag = (
        request.fulfillment_info.tag
        or ""
    ).strip()

    parameters = dict(
        request.session_info.parameters
        or {}
    )

    if tag == TAG_BUILD_SUMMARY:
        return _build_summary_response(
            parameters
        )

    if tag == TAG_CONFIRM_SUMMARY:
        return _confirm_summary_response(
            parameters
        )

    if tag == TAG_REQUEST_CORRECTION:
        return _request_correction_response(
            parameters
        )

    raise ValueError(
        "Unsupported Phase 8 webhook tag: "
        f"{tag}"
    )

from copy import deepcopy
from typing import Any

from dialogflow_contract import WebhookRequest

from slot_logic import (
    SLOT_ORDER,
    apply_updates,
    get_just_collected_slot,
    get_missing_slots,
    slot_from_webhook_tag,
)

from text_signals import (
    detect_flags,
    is_correction_signal,
    is_done_signal,
    should_request_clarification,
)


ACTION_CONTINUE = "continue"
ACTION_DONE = "done"
ACTION_CORRECTION = "correction"
ACTION_CLARIFY = "clarify"


RAW_TEXT_SLOTS = {
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity",
}


def _safe_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return deepcopy(value)

    return {}


def _finalize_response(
    original_parameters: dict[str, Any],
    updates: dict[str, Any],
) -> dict:
    """
    Calculate missing/next slots using the state that will exist
    after our webhook updates have been applied.
    """

    simulated_state = apply_updates(
        original_parameters,
        updates,
    )

    missing_slots = get_missing_slots(simulated_state)

    updates["p7_missing_slots"] = missing_slots

    updates["p7_next_slot"] = (
        missing_slots[0]
        if missing_slots
        else None
    )

    return {
        "sessionInfo": {
            "parameters": updates
        }
    }


def process_webhook(
    request: WebhookRequest,
) -> dict:
    """
    Main Phase 7 conversation controller.

    Processing order is intentionally:

    1. Raw utterance
    2. Done detection
    3. Correction detection
    4. Normal slot metadata
    5. Clarification decision
    6. Missing-slot calculation

    This prevents control words from being accepted as symptoms.
    """

    raw_utterance = (
        request.text
        or request.transcript
        or ""
    )

    session_parameters = dict(
        request.session_info.parameters or {}
    )

    webhook_tag = request.fulfillment_info.tag or ""

    just_collected_slot, _ = get_just_collected_slot(
        request.page_info
    )

    tag_slot = slot_from_webhook_tag(
        webhook_tag
    )

    # Prefer Dialogflow's explicit justCollected value.
    current_slot = just_collected_slot

    # Fallback to webhook tag only if required.
    if current_slot not in SLOT_ORDER:
        current_slot = tag_slot

    updates: dict[str, Any] = {}

    existing_flags = _safe_dict(
        session_parameters.get("p7_slot_flags")
    )

    clarification_counts = _safe_dict(
        session_parameters.get("p7_clarify_counts")
    )

    # ---------------------------------------------------------
    # 1. DONE SIGNAL
    # ---------------------------------------------------------

    if is_done_signal(raw_utterance):

        # If @sys.any temporarily captured "done",
        # remove it from the clinical field.
        if current_slot in SLOT_ORDER:
            updates[current_slot] = None

        updates["p7_action"] = ACTION_DONE
        updates["p7_current_slot"] = current_slot
        updates["p7_target_slot"] = None

        return _finalize_response(
            session_parameters,
            updates,
        )

    # ---------------------------------------------------------
    # 2. CORRECTION SIGNAL
    # ---------------------------------------------------------

    if is_correction_signal(raw_utterance):

        # A correction phrase may itself have been captured
        # by the current @sys.any parameter.
        if current_slot in SLOT_ORDER:
            updates[current_slot] = None

        updates["p7_action"] = ACTION_CORRECTION
        updates["p7_current_slot"] = current_slot
        updates["p7_target_slot"] = None

        return _finalize_response(
            session_parameters,
            updates,
        )

    # ---------------------------------------------------------
    # 3. NORMAL SLOT PROCESSING
    # ---------------------------------------------------------

    updates["p7_action"] = ACTION_CONTINUE
    updates["p7_current_slot"] = current_slot
    updates["p7_target_slot"] = None

    if current_slot in SLOT_ORDER:

        # -----------------------------------------------------
        # PRESERVE RAW PATIENT WORDING
        # -----------------------------------------------------
        #
        # Dialogflow entities may convert the patient's wording
        # into a canonical value.
        #
        # Example:
        #
        # "The left side of my head"
        #
        # might become:
        #
        # "temple"
        #
        # For SymptomScout, we want to preserve the patient's
        # actual wording for free-text symptom-description fields.
        if (
            current_slot in RAW_TEXT_SLOTS
            and raw_utterance.strip()
        ):
            updates[current_slot] = raw_utterance.strip()

        # -----------------------------------------------------
        # DETECT LANGUAGE FLAGS
        # -----------------------------------------------------

        slot_flags = detect_flags(
            raw_utterance
        )

        existing_flags[current_slot] = slot_flags

        updates["p7_slot_flags"] = existing_flags

        # -----------------------------------------------------
        # 4. ONE-TIME CLARIFICATION
        # -----------------------------------------------------

        clarification_needed = (
            should_request_clarification(
                raw_utterance,
                slot_flags,
            )
        )

        previous_attempts = int(
            clarification_counts.get(
                current_slot,
                0,
            )
            or 0
        )

        if (
            clarification_needed
            and previous_attempts < 1
        ):
            clarification_counts[current_slot] = (
                previous_attempts + 1
            )

            # Remove the low-information answer so that
            # Dialogflow asks for this field again.
            updates[current_slot] = None

            updates["p7_action"] = ACTION_CLARIFY
            updates["p7_target_slot"] = current_slot

        updates[
            "p7_clarify_counts"
        ] = clarification_counts

    return _finalize_response(
        session_parameters,
        updates,
    )

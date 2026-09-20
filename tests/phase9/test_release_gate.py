from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Import backend exactly as Cloud Run sees it.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402


client = TestClient(app)


# ---------------------------------------------------------------------------
# Canonical symptom slots used throughout the MVP.
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


# ---------------------------------------------------------------------------
# Complete example patient session.
#
# This is deliberately a neutral symptom-description example.
# It is used to verify summary construction, confirmation,
# correction handling, and stale-summary protection.
# ---------------------------------------------------------------------------

COMPLETE_SYMPTOM_PARAMETERS = {
    "main_symptom": "abdominal pain",
    "site": "lower right abdomen",
    "onset": "last night",
    "character": "sharp",
    "radiation": "does not spread",
    "associated": "nausea",
    "timing": "comes and goes",
    "exacerbating": "walking makes it worse",
    "relieving": "resting helps a little",
    "severity": "6 out of 10",
}


# ---------------------------------------------------------------------------
# Dialogflow CX webhook request helper.
# ---------------------------------------------------------------------------

def make_request(
    tag: str,
    parameters: dict | None = None,
    text: str = "",
    just_collected_slot: str | None = None,
) -> dict:
    """
    Build the standard Dialogflow CX webhook request shape used by
    the Phase 7 and Phase 8 backend.
    """

    parameters = dict(parameters or {})

    parameter_info = []

    if just_collected_slot is not None:
        parameter_info.append(
            {
                "displayName": just_collected_slot,
                "value": parameters.get(just_collected_slot),
                "justCollected": True,
            }
        )

    return {
        "fulfillmentInfo": {
            "tag": tag,
        },
        "text": text,
        "sessionInfo": {
            "session": (
                "projects/test-project/"
                "locations/global/"
                "agents/test-agent/"
                "sessions/phase9-test"
            ),
            "parameters": parameters,
        },
        "pageInfo": {
            "formInfo": {
                "parameterInfo": parameter_info,
            }
        },
    }


def post_webhook(
    tag: str,
    parameters: dict | None = None,
    text: str = "",
    just_collected_slot: str | None = None,
) -> dict:
    """
    Send a webhook request and simulate Dialogflow CX session
    parameter behaviour.

    IMPORTANT:
    The webhook normally returns only the session parameters that
    it wants to update.

    Dialogflow CX merges those returned parameters into the
    existing session instead of replacing the entire session
    parameter object.

    Therefore this test helper must merge the webhook response
    back into the parameters that were originally supplied.

    Without this merge, the canonical symptom values disappear
    between webhook calls and the Phase 8 fingerprint correctly
    identifies the summary as stale.
    """

    existing_parameters = dict(parameters or {})

    response = client.post(
        "/dialogflow/webhook",
        json=make_request(
            tag=tag,
            parameters=existing_parameters,
            text=text,
            just_collected_slot=just_collected_slot,
        ),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert "sessionInfo" in body
    assert "parameters" in body["sessionInfo"]

    updated_parameters = body["sessionInfo"]["parameters"]

    merged_parameters = dict(existing_parameters)
    merged_parameters.update(updated_parameters)

    return merged_parameters


# ---------------------------------------------------------------------------
# Basic deployment/backend availability.
# ---------------------------------------------------------------------------

def test_health_endpoint_is_alive():
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# Phase 8 summary construction.
# ---------------------------------------------------------------------------

def test_phase8_complete_summary_contains_every_patient_value():
    params = post_webhook(
        tag="p8.build_summary",
        parameters=COMPLETE_SYMPTOM_PARAMETERS,
    )

    assert params["p8_summary_ready"] is True

    assert (
        params["p8_summary_status"]
        == "awaiting_confirmation"
    )

    assert params["p8_summary_confirmed"] is False

    summary = params["p8_summary_text"]

    for value in COMPLETE_SYMPTOM_PARAMETERS.values():
        assert value in summary


def test_phase8_missing_information_is_not_invented():
    params = post_webhook(
        tag="p8.build_summary",
        parameters={
            "main_symptom": "headache",
        },
    )

    summary = params["p8_summary_text"]

    assert "headache" in summary

    # The deterministic summary builder must explicitly indicate
    # that information which was never collected is unavailable.
    #
    # It must not invent values to make the summary appear complete.
    assert "Not provided" in summary


# ---------------------------------------------------------------------------
# Phase 8 confirmation.
# ---------------------------------------------------------------------------

def test_phase8_valid_summary_can_be_confirmed():
    built = post_webhook(
        tag="p8.build_summary",
        parameters=COMPLETE_SYMPTOM_PARAMETERS,
    )

    confirmed = post_webhook(
        tag="p8.confirm_summary",
        parameters=built,
    )

    assert confirmed["p8_action"] == "confirmed"

    assert confirmed["p8_summary_confirmed"] is True

    assert (
        confirmed["p8_summary_status"]
        == "confirmed"
    )

    assert confirmed["p8_confirmed_summary"]


# ---------------------------------------------------------------------------
# Phase 8 stale-summary protection.
# ---------------------------------------------------------------------------

def test_phase8_stale_summary_cannot_be_confirmed():
    built = post_webhook(
        tag="p8.build_summary",
        parameters=COMPLETE_SYMPTOM_PARAMETERS,
    )

    # Simulate patient information changing AFTER the review
    # summary was generated.
    #
    # The summary fingerprint should no longer match.
    built["site"] = "upper abdomen"

    result = post_webhook(
        tag="p8.confirm_summary",
        parameters=built,
    )

    assert (
        result["p8_action"]
        == "refresh_required"
    )

    assert result["p8_summary_confirmed"] is False

    assert (
        result["p8_summary_status"]
        == "stale"
    )


# ---------------------------------------------------------------------------
# Phase 8 correction workflow.
# ---------------------------------------------------------------------------

def test_phase8_correction_invalidates_confirmation():
    built = post_webhook(
        tag="p8.build_summary",
        parameters=COMPLETE_SYMPTOM_PARAMETERS,
    )

    confirmed = post_webhook(
        tag="p8.confirm_summary",
        parameters=built,
    )

    assert confirmed["p8_summary_confirmed"] is True

    correction = post_webhook(
        tag="p8.request_correction",
        parameters=confirmed,
    )

    assert (
        correction["p8_action"]
        == "correction_requested"
    )

    assert correction["p8_summary_confirmed"] is False

    assert (
        correction["p8_summary_status"]
        == "needs_correction"
    )


# ---------------------------------------------------------------------------
# Phase 8 preservation of Phase 7 safety/context flags.
# ---------------------------------------------------------------------------

def test_phase8_preserves_negation_and_uncertainty_context():
    parameters = dict(COMPLETE_SYMPTOM_PARAMETERS)

    parameters["p7_slot_flags"] = {
        "associated": {
            "negated": True,
            "uncertain": False,
            "ambiguous": False,
        },
        "onset": {
            "negated": False,
            "uncertain": True,
            "ambiguous": False,
        },
    }

    result = post_webhook(
        tag="p8.build_summary",
        parameters=parameters,
    )

    summary_lower = result["p8_summary_text"].lower()

    assert "negative statement" in summary_lower
    assert "uncertainty" in summary_lower


# ---------------------------------------------------------------------------
# Non-diagnostic safety boundary.
# ---------------------------------------------------------------------------

def test_summary_does_not_generate_diagnoses():
    """
    None of the disease terms below were supplied by the patient.

    The deterministic Phase 8 summary must therefore never
    introduce them.
    """

    result = post_webhook(
        tag="p8.build_summary",
        parameters=COMPLETE_SYMPTOM_PARAMETERS,
    )

    summary = result["p8_summary_text"].lower()

    invented_diagnoses = [
        "appendicitis",
        "cancer",
        "pneumonia",
        "migraine",
        "stroke",
        "heart attack",
        "infection diagnosis",
    ]

    for diagnosis in invented_diagnoses:
        assert diagnosis not in summary


# ---------------------------------------------------------------------------
# Phase 7 signal handling regression tests.
# ---------------------------------------------------------------------------

def test_phase7_negation_is_preserved():
    result = post_webhook(
        tag="slot.updated.radiation",
        parameters={
            "radiation": "No, it doesn't spread.",
        },
        text="No, it doesn't spread.",
        just_collected_slot="radiation",
    )

    assert (
        result["p7_slot_flags"]["radiation"]["negated"]
        is True
    )


def test_phase7_uncertainty_is_preserved():
    result = post_webhook(
        tag="slot.updated.onset",
        parameters={
            "onset": "Maybe Monday, I'm not sure",
        },
        text="Maybe Monday, I'm not sure",
        just_collected_slot="onset",
    )

    assert (
        result["p7_slot_flags"]["onset"]["uncertain"]
        is True
    )


def test_phase7_ambiguity_requests_clarification():
    result = post_webhook(
        tag="slot.updated.site",
        parameters={
            "site": "Somewhere around there.",
        },
        text="Somewhere around there.",
        just_collected_slot="site",
    )

    assert (
        result["p7_slot_flags"]["site"]["ambiguous"]
        is True
    )

    assert result["p7_action"] == "clarify"

    assert result["p7_target_slot"] == "site"

    assert (
        result["p7_clarify_counts"]["site"]
        == 1
    )


def test_phase7_does_not_repeat_clarification_forever():
    first = post_webhook(
        tag="slot.updated.site",
        parameters={
            "site": "Somewhere around there.",
        },
        text="Somewhere around there.",
        just_collected_slot="site",
    )

    assert (
        first["p7_clarify_counts"]["site"]
        == 1
    )

    second = post_webhook(
        tag="slot.updated.site",
        parameters=first,
        text="Somewhere around there.",
        just_collected_slot="site",
    )

    # Phase 7 intentionally limits a slot to one clarification
    # attempt so the conversation cannot become trapped in an
    # infinite clarification loop.
    assert (
        second["p7_clarify_counts"]["site"]
        == 1
    )

    assert second["p7_action"] != "clarify"


# ---------------------------------------------------------------------------
# Phase 7 conversational-control handling.
# ---------------------------------------------------------------------------

def test_done_control_text_is_not_saved_as_symptom_content():
    result = post_webhook(
        tag="slot.updated.site",
        parameters={
            "site": "done",
        },
        text="done",
        just_collected_slot="site",
    )

    assert result["p7_action"] == "done"

    assert result.get("site") is None


# ---------------------------------------------------------------------------
# Canonical schema regression.
# ---------------------------------------------------------------------------

def test_all_canonical_slots_are_still_supported():
    assert CANONICAL_SLOTS == [
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

from fastapi.testclient import (
    TestClient,
)

from main import app


client = TestClient(app)


def make_request(
    tag: str,
    parameters: dict | None = None,
    text: str = "",
) -> dict:

    return {
        "fulfillmentInfo": {
            "tag": tag,
        },

        "text": text,

        "sessionInfo": {
            "session": (
                "projects/test/"
                "locations/global/"
                "agents/test/"
                "sessions/"
                "phase8-test"
            ),

            "parameters": (
                parameters
                or {}
            ),
        },

        "pageInfo": {
            "currentPage": (
                "projects/test/"
                "locations/global/"
                "agents/test/"
                "flows/test/"
                "pages/test"
            ),

            "displayName": (
                "Review Information"
            ),

            "formInfo": {
                "parameterInfo": [],
            },
        },
    }


def response_parameters(
    response,
) -> dict:

    return (
        response
        .json()
        ["sessionInfo"]
        ["parameters"]
    )


def response_text(
    response,
) -> str:

    return (
        response
        .json()
        ["fulfillmentResponse"]
        ["messages"]
        [0]
        ["text"]
        ["text"]
        [0]
    )


def test_build_summary_webhook():

    response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.build_summary",

            {
                "main_symptom": (
                    "headache"
                ),
                "site": (
                    "left temple"
                ),
                "severity": (
                    "7 out of 10"
                ),
            },
        ),
    )

    assert (
        response.status_code
        == 200
    )

    params = response_parameters(
        response
    )

    assert (
        params["p8_action"]
        == "review"
    )

    assert (
        params[
            "p8_summary_ready"
        ]
        is True
    )

    assert (
        params[
            "p8_summary_confirmed"
        ]
        is False
    )

    assert (
        params[
            "p8_summary_status"
        ]
        == "awaiting_confirmation"
    )

    assert (
        "headache"
        in params[
            "p8_summary_text"
        ]
    )

    assert (
        "Is this an accurate summary"
        in response_text(response)
    )


def test_build_summary_with_no_symptom_information_is_not_ready():

    response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.build_summary",
            {},
        ),
    )

    params = response_parameters(
        response
    )

    assert (
        params[
            "p8_summary_ready"
        ]
        is False
    )

    assert (
        params[
            "p8_summary_status"
        ]
        == "empty"
    )

    assert (
        params[
            "p8_summary_confirmed"
        ]
        is False
    )


def test_confirm_summary_only_confirms_current_summary():

    original = {
        "main_symptom": "headache",
        "site": "left temple",
    }

    build_response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.build_summary",
            original,
        ),
    )

    built_updates = (
        response_parameters(
            build_response
        )
    )

    confirm_parameters = {
        **original,
        **built_updates,
    }

    confirm_response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.confirm_summary",
            confirm_parameters,
        ),
    )

    confirmed = response_parameters(
        confirm_response
    )

    assert (
        confirmed["p8_action"]
        == "confirmed"
    )

    assert (
        confirmed[
            "p8_summary_confirmed"
        ]
        is True
    )

    assert (
        confirmed[
            "p8_summary_status"
        ]
        == "confirmed"
    )

    assert (
        "headache"
        in confirmed[
            "p8_confirmed_summary"
        ]
    )


def test_stale_summary_cannot_be_confirmed():

    original = {
        "main_symptom": "headache",
        "site": "left temple",
    }

    build_response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.build_summary",
            original,
        ),
    )

    built_updates = (
        response_parameters(
            build_response
        )
    )

    changed_parameters = {
        **original,
        **built_updates,

        "site": "right temple",
    }

    confirm_response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.confirm_summary",
            changed_parameters,
        ),
    )

    params = response_parameters(
        confirm_response
    )

    assert (
        params["p8_action"]
        == "refresh_required"
    )

    assert (
        params[
            "p8_summary_confirmed"
        ]
        is False
    )

    assert (
        params[
            "p8_summary_status"
        ]
        == "stale"
    )


def test_request_correction_clears_confirmation_state():

    response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "p8.request_correction",

            {
                "main_symptom": (
                    "headache"
                ),

                "p8_summary_confirmed": (
                    True
                ),

                "p8_summary_status": (
                    "confirmed"
                ),

                "p8_confirmed_summary": (
                    "old summary"
                ),
            },
        ),
    )

    params = response_parameters(
        response
    )

    assert (
        params["p8_action"]
        == "correction_requested"
    )

    assert (
        params[
            "p8_summary_confirmed"
        ]
        is False
    )

    assert (
        params[
            "p8_summary_status"
        ]
        == "needs_correction"
    )

    assert (
        params[
            "p8_confirmed_summary"
        ]
        is None
    )


def test_non_phase8_tag_still_goes_to_phase7_controller():

    response = client.post(
        "/dialogflow/webhook",

        json=make_request(
            "phase7.slot_update",

            {
                "main_symptom": (
                    "headache"
                )
            },
        ),
    )

    params = response_parameters(
        response
    )

    assert (
        "p7_action"
        in params
    )

    assert (
        "p8_action"
        not in params
    )

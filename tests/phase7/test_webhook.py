from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def make_request(
    text="left side",
    slot="site",
    value="left side",
    parameters=None,
    tag=None,
):
    if parameters is None:
        parameters = {
            "main_symptom": "headache",
            slot: value,
        }

    if tag is None:
        tag = f"slot.updated.{slot}"

    return {
        "fulfillmentInfo": {
            "tag": tag
        },
        "text": text,
        "sessionInfo": {
            "session": (
                "projects/test/"
                "locations/global/"
                "agents/test/"
                "sessions/test123"
            ),
            "parameters": parameters,
        },
        "pageInfo": {
            "displayName": (
                f"Collect {slot.title()}"
            ),
            "formInfo": {
                "parameterInfo": [
                    {
                        "displayName": slot,
                        "required": True,
                        "state": "FILLED",
                        "value": value,
                        "justCollected": True,
                    }
                ]
            },
        },
    }


def response_parameters(response):
    return (
        response.json()
        ["sessionInfo"]
        ["parameters"]
    )


def test_health_endpoint():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_done_clears_captured_slot():
    payload = make_request(
        text="done",
        slot="site",
        value="done",
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    assert response.status_code == 200

    params = response_parameters(
        response
    )

    assert params["site"] is None
    assert params["p7_action"] == "done"


def test_pain_gone_does_not_finish_conversation():
    payload = make_request(
        text="The pain is gone now",
        slot="timing",
        value="The pain is gone now",
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["p7_action"] == "continue"


def test_correction_is_detected():
    payload = make_request(
        text="Actually I need to change something",
        slot="site",
        value="Actually I need to change something",
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["site"] is None

    assert (
        params["p7_action"]
        == "correction"
    )


def test_negation_is_preserved():
    payload = make_request(
        text="No, it doesn't spread",
        slot="radiation",
        value="No, it doesn't spread",
        parameters={
            "main_symptom": "headache",
            "radiation": "No, it doesn't spread",
        },
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["p7_action"] == "continue"

    assert (
        params["p7_slot_flags"]
        ["radiation"]
        ["negated"]
        is True
    )


def test_uncertainty_is_preserved():
    payload = make_request(
        text="Maybe Monday, I'm not sure",
        slot="onset",
        value="Maybe Monday, I'm not sure",
        parameters={
            "main_symptom": "headache",
            "onset": "Maybe Monday, I'm not sure",
        },
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert (
        params["p7_slot_flags"]
        ["onset"]
        ["uncertain"]
        is True
    )


def test_ambiguous_answer_requests_one_clarification():
    payload = make_request(
        text="somewhere around there",
        slot="site",
        value="somewhere around there",
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["site"] is None
    assert params["p7_action"] == "clarify"
    assert params["p7_target_slot"] == "site"

    assert (
        params["p7_clarify_counts"]["site"]
        == 1
    )


def test_second_ambiguous_answer_is_accepted():
    payload = make_request(
        text="somewhere around there",
        slot="site",
        value="somewhere around there",
        parameters={
            "main_symptom": "headache",
            "site": "somewhere around there",
            "p7_clarify_counts": {
                "site": 1
            },
        },
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["p7_action"] == "continue"


def test_transcript_is_supported():
    payload = make_request(
        text="ignored",
        slot="site",
        value="done",
    )

    payload.pop(
        "text"
    )

    payload["transcript"] = "done"

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    params = response_parameters(
        response
    )

    assert params["p7_action"] == "done"


def test_unknown_dialogflow_fields_are_ignored():
    payload = make_request()

    payload[
        "someFutureGoogleField"
    ] = {
        "anything": True
    }

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    assert response.status_code == 200

def test_site_preserves_raw_patient_wording():
    payload = make_request(
        text="The left side of my head",
        slot="site",
        value="temple",
        parameters={
            "main_symptom": "headache",
            "site": "temple",
        },
    )

    response = client.post(
        "/dialogflow/webhook",
        json=payload,
    )

    assert response.status_code == 200

    params = response_parameters(
        response
    )

    assert params["p7_action"] == "continue"

    assert (
        params["site"]
        == "The left side of my head"
    )

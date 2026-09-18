from dialogflow_contract import PageInfo

from slot_logic import (
    get_just_collected_slot,
    get_missing_slots,
    get_next_slot,
    slot_from_webhook_tag,
)


def test_missing_slots():
    parameters = {
        "main_symptom": "headache",
        "site": "left temple",
    }

    missing = get_missing_slots(
        parameters
    )

    assert "main_symptom" not in missing
    assert "site" not in missing
    assert "onset" in missing


def test_next_slot():
    parameters = {
        "main_symptom": "headache",
        "site": "left temple",
    }

    assert get_next_slot(
        parameters
    ) == "onset"


def test_webhook_tag_to_slot():
    assert slot_from_webhook_tag(
        "slot.updated.site"
    ) == "site"


def test_invalid_webhook_tag():
    assert slot_from_webhook_tag(
        "something.else"
    ) is None


def test_just_collected_slot():
    page = PageInfo.model_validate(
        {
            "displayName": "Collect Site",
            "formInfo": {
                "parameterInfo": [
                    {
                        "displayName": "site",
                        "required": True,
                        "state": "FILLED",
                        "value": "left side",
                        "justCollected": True,
                    }
                ]
            },
        }
    )

    slot, value = get_just_collected_slot(
        page
    )

    assert slot == "site"
    assert value == "left side"

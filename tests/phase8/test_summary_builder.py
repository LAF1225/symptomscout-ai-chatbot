from summary_builder import (
    build_summary,
    build_summary_data,
)


def test_summary_uses_canonical_order():

    params = {
        "severity": "7 out of 10",
        "main_symptom": "headache",
        "site": "left temple",
    }

    summary = build_summary_data(
        params
    )

    slots = [
        field["slot"]
        for field
        in summary["fields"]
    ]

    assert slots == [
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


def test_summary_preserves_patient_wording():

    params = {
        "main_symptom": (
            "a weird pounding headache"
        ),
        "site": (
            "mostly behind my left eye"
        ),
    }

    summary = build_summary(
        params
    )

    assert (
        "a weird pounding headache"
        in summary["body"]
    )

    assert (
        "mostly behind my left eye"
        in summary["body"]
    )


def test_summary_marks_missing_fields_without_inventing_information():

    params = {
        "main_symptom": "headache"
    }

    summary = build_summary(
        params
    )

    assert (
        summary["data"][
            "provided_count"
        ]
        == 1
    )

    assert (
        summary["data"][
            "missing_count"
        ]
        == 9
    )

    assert (
        "• Location: Not provided"
        in summary["body"]
    )


def test_summary_renders_phase7_flags():

    params = {
        "main_symptom": "headache",

        "associated": "no nausea",

        "onset": (
            "I think it started yesterday"
        ),

        "p7_slot_flags": {
            "associated": {
                "negated": True,
            },

            "onset": [
                "uncertain"
            ],
        },
    }

    summary = build_summary(
        params
    )

    assert (
        "negative statement"
        in summary["body"]
    )

    assert (
        "patient expressed uncertainty"
        in summary["body"]
    )


def test_internal_control_parameters_are_not_summarised():

    params = {
        "main_symptom": "headache",
        "p7_action": "done",
        "p7_next_slot": None,
        "p8_action": "review",
    }

    summary = build_summary(
        params
    )

    assert (
        "p7_action"
        not in summary["body"]
    )

    assert (
        "p8_action"
        not in summary["body"]
    )


def test_fingerprint_changes_when_patient_information_changes():

    first = build_summary(
        {
            "main_symptom": "headache",
            "site": "left side",
        }
    )

    second = build_summary(
        {
            "main_symptom": "headache",
            "site": "right side",
        }
    )

    assert (
        first["fingerprint"]
        != second["fingerprint"]
    )

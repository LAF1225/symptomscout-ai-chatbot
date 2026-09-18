from text_signals import (
    detect_flags,
    is_correction_signal,
    is_done_signal,
    should_request_clarification,
)


def test_done_is_detected():
    assert is_done_signal("done") is True


def test_thats_all_is_detected():
    assert is_done_signal(
        "That's all."
    ) is True


def test_pain_is_gone_is_not_done():
    assert is_done_signal(
        "The pain is gone now."
    ) is False


def test_done_coughing_is_not_done():
    assert is_done_signal(
        "I'm done coughing now."
    ) is False


def test_correction_signal():
    assert is_correction_signal(
        "Actually, I meant something else"
    ) is True


def test_plain_no_is_not_correction():
    assert is_correction_signal(
        "No"
    ) is False


def test_negation_flag():
    flags = detect_flags(
        "No, it doesn't spread."
    )

    assert flags["negated"] is True


def test_uncertainty_flag():
    flags = detect_flags(
        "Maybe Monday, I'm not sure."
    )

    assert flags["uncertain"] is True


def test_ambiguity_flag():
    flags = detect_flags(
        "Somewhere around there."
    )

    assert flags["ambiguous"] is True


def test_low_information_requests_clarification():
    flags = detect_flags(
        "Somewhere around there."
    )

    assert should_request_clarification(
        "Somewhere around there.",
        flags,
    ) is True


def test_useful_imprecise_answer_does_not_force_clarification():
    flags = detect_flags(
        "Sort of burning."
    )

    assert flags["ambiguous"] is True

    assert should_request_clarification(
        "Sort of burning.",
        flags,
    ) is False

def test_correction_with_actually_prefix():
    assert is_correction_signal(
        "Actually I need to change something"
    ) is True


def test_correction_with_sorry_prefix():
    assert is_correction_signal(
        "Sorry, I need to change something"
    ) is True


def test_correction_with_wait_prefix():
    assert is_correction_signal(
        "Wait, I meant something else"
    ) is True


def test_normal_actually_sentence_is_not_correction():
    assert is_correction_signal(
        "Actually it started yesterday"
    ) is False

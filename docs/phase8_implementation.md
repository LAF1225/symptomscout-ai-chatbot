# Phase 8 — Structured Patient Summary and Confirmation

## Objective

Phase 8 converts the symptom information collected by the
Dialogflow CX conversation into a deterministic structured
patient summary and requires explicit patient confirmation
before the summary is considered final.

The phase remains non-diagnostic. It does not infer diagnoses,
recommend treatment, or translate patient descriptions into
clinical conclusions.

## Inputs

Phase 8 uses the ten canonical symptom parameters produced by
the existing Phase 7 dialogue controller:

- main_symptom
- site
- onset
- character
- radiation
- associated
- timing
- exacerbating
- relieving
- severity

Phase 8 may also consume Phase 7 slot metadata such as
p7_slot_flags.

## Architecture

Phase 8 introduces two backend modules:

- summary_builder.py
- phase8_controller.py

The existing FastAPI endpoint remains:

POST /dialogflow/webhook

main.py dispatches p8.* webhook tags to the Phase 8 controller.
All other requests continue through the Phase 7 controller.

Phase 7 controller logic was not replaced.

## Webhook Tags

p8.build_summary

Creates a structured summary from the current symptom session
parameters and displays it for patient review.

p8.confirm_summary

Checks that the reviewed summary still matches the current
symptom state before marking it confirmed.

p8.request_correction

Clears confirmation state and returns the user to the existing
Phase 7 Correction flow.

## Summary Safety Rules

The summary:

- preserves patient wording
- uses a fixed canonical slot order
- marks missing information as "Not provided"
- does not infer diagnoses
- does not generate treatment advice
- preserves relevant uncertainty and negation metadata
- excludes internal p7_* and p8_* control parameters

## Stale Summary Protection

Each generated summary receives a deterministic SHA-256
fingerprint.

Before confirmation, the backend rebuilds the summary from the
current symptom data and verifies that its fingerprint matches
the summary previously shown to the patient.

If the symptom data changed, confirmation is rejected and a
fresh review is required.

## Dialogflow Changes

Review Information entry fulfillment calls:

p8.build_summary

Review Information routes:

answer.yes
→ p8.confirm_summary
→ Summary Complete

answer.no
→ p8.request_correction
→ Correction

answer.correction
→ p8.request_correction
→ Correction

An empty-summary condition returns the conversation to Collect
Main Symptom.

Summary Complete permits completion only when:

p8_summary_confirmed = true

## Testing

Phase 8 contains automated tests for:

- canonical field order
- preservation of patient wording
- missing information
- Phase 7 flag rendering
- exclusion of internal state
- summary fingerprint changes
- summary webhook generation
- empty summary rejection
- explicit confirmation
- stale summary rejection
- correction reset
- Phase 7 dispatcher preservation

All Phase 7 and Phase 8 automated tests must pass before Phase
8 is considered complete.

## Storage Boundary

The confirmed summary currently exists as Dialogflow session
state.

Phase 8 does not create persistent patient medical records or
long-term storage.

## Completion Criteria

Phase 8 is complete when:

1. Phase 7 regression tests pass.
2. All Phase 8 automated tests pass.
3. Review Information generates the structured summary.
4. Patient wording is preserved.
5. Negated and uncertain statements remain distinguishable.
6. Missing fields are not invented.
7. The user can reject and correct the summary.
8. Corrections regenerate the summary.
9. A stale summary cannot be confirmed.
10. Confirmation sets p8_summary_confirmed = true.
11. The complete agent passes Dialogflow simulator tests.
12. Phase 8 Dialogflow regression tests are saved.
13. The agent is exported and the Git branch is committed.

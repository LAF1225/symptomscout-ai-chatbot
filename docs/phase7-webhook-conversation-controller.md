# Phase 7 — Webhook Conversation Controller

## 1. Purpose

Phase 7 introduces a deterministic FastAPI controller between
Dialogflow CX and the symptom-collection flow.

The controller remains explicitly non-diagnostic.

## 2. Dependencies

- Python 3.12
- FastAPI
- Dialogflow CX
- Google Cloud Run
- pytest
- HTTPX

## 3. Canonical Slots

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

## 4. Processing Order

1. Obtain raw user utterance.
2. Detect conversation completion.
3. Detect correction request.
4. Record language metadata.
5. Determine whether clarification is required.
6. Calculate remaining symptom slots.
7. Update Dialogflow session state.

## 5. Control Actions

- continue
- done
- correction
- clarify

## 6. Language Metadata

The backend preserves:

- ambiguity
- negation
- uncertainty

These are metadata rather than diagnoses or clinical conclusions.

## 7. Done Handling

Whole-message completion phrases are detected before symptom slot
processing.

This prevents free-text Dialogflow parameters from storing values
such as "done" as clinical information.

## 8. Correction Handling

Correction requests route to a dedicated Correction page.

The user selects which symptom field should be recollected.

Correcting the main symptom clears all dependent symptom-description
slots.

## 9. Clarification Handling

Very low-information ambiguous answers receive at most one
clarification attempt.

After one attempt, uncertain information can be retained rather than
creating an infinite conversational loop.

## 10. Privacy

Clinical free text is not written to application logs.

Dialogflow clinical parameters use log redaction.

## 11. Deployment

The backend is deployed as a private Cloud Run service.

Dialogflow CX authenticates using Service Agent Auth with an ID token.

## 12. Testing

Automated tests cover:

- done handling
- false done detection
- correction
- negation
- uncertainty
- ambiguity
- one-time clarification
- transcript input
- unexpected Dialogflow fields
- missing-slot calculation

## 13. Phase 7 Status

Phase 7 is complete when:

- automated tests pass
- Cloud Run responds successfully
- Dialogflow can invoke the webhook
- done handling works
- corrections work
- clarification works
- normal symptom collection still works

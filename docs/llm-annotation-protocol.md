# LLM Annotation Protocol

## Purpose

Classify patient-language examples according to the canonical
SOCRATES/OPQRST information fields used by the SymptomScout chatbot.

The annotation is linguistic and non-diagnostic.

Annotators must classify only information explicitly expressed by the
patient or clearly established by the immediately preceding question.

Annotators must not infer diseases, physiological mechanisms, treatment
needs, or diagnoses.

## Slot Definitions

### main_symptom

The primary symptom or sensation being discussed.

Example:
"My shoulder has been hurting."

### site

Where the symptom is experienced.

Example:
"Mostly behind my right eye."

### onset

When the symptom began or how recently it started.

Example:
"It began yesterday."

### character

How the patient describes the quality or subjective sensation.

Examples:
"burning"
"throbbing"
"heavy"
"weird"

Ambiguous descriptions should still be labelled `character` while also
setting `ambiguous = 1`.

### radiation

Whether a symptom remains in one location or moves/spreads elsewhere.

Example:
"It goes down my arm."

### associated

Another experience occurring alongside the main symptom.

Example:
"I also feel nauseous when it happens."

### timing

Duration, frequency, recurrence, or temporal pattern.

Examples:
"It comes and goes."
"It lasts around twenty minutes."

### exacerbating

Something the patient reports makes the symptom worse or triggers it.

Example:
"Walking makes it worse."

### relieving

Something the patient reports makes the symptom better.

Example:
"Resting seems to help."

### severity

Patient-reported intensity.

Example:
"It's about six out of ten."

## Flags

### ambiguous

1 when an expression is meaningfully unclear or could reasonably refer
to several different sensations.

Examples:
"weird"
"heavy"
"off"
"funny"

Do not resolve ambiguity through medical inference.

### uncertain

1 when the patient expresses uncertainty.

Examples:
"maybe"
"I think"
"probably"
"I'm not sure"
"around Tuesday"

Approximation alone does not always imply meaningful uncertainty.
Use judgement based on the full statement.

### negated

1 when the patient explicitly denies the relevant information.

Examples:
"It doesn't spread."
"No numbness."

### context_dependent

1 when the patient's response cannot be interpreted correctly without
the preceding question.

Example:

Doctor: "Does it spread?"
Patient: "No."

The word "No" alone does not identify radiation.

## Review Status

### keep

The utterance contains useful information relevant to the symptom
communication schema.

### discard

The utterance is unrelated to the MVP annotation task.

Examples:
"Thank you."
"I need a prescription refill."
"My insurance wouldn't cover it."

### needs_review

The example is potentially useful but the correct annotation is not
clear enough for confident automatic use.

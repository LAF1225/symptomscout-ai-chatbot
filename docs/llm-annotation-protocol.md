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

# SymptomScout LLM Annotation Protocol

## Version

Annotation Protocol v0.2

## Purpose

This protocol defines how patient-language examples are annotated for the
SymptomScout AI Chatbot.

The project is a non-diagnostic symptom communication system based on
SOCRATES and OPQRST.

The purpose of annotation is to identify what symptom information the
patient explicitly communicates.

The purpose is NOT to determine what disease, diagnosis, physiological
mechanism, urgency level, treatment, or clinical interpretation might
explain the patient's language.

---

# 1. Core Annotation Principle

The annotator should answer:

> What symptom-description information has the patient actually communicated?

The patient's utterance is the primary source of information.

The immediately preceding doctor prompt may be used only to understand
what a short or context-dependent response refers to.

The doctor prompt must never be treated as patient-confirmed information
unless the patient explicitly confirms it.

Annotators must not infer:

- diagnoses;
- diseases;
- causes;
- physiological mechanisms;
- pathology;
- urgency;
- treatment requirements;
- medication requirements;
- testing requirements;
- specialist requirements;
- clinical significance;
- information not expressed by the patient.

Annotate what the patient's language contains, not what it might mean
medically.

---

# 2. Valid Annotation Slots

Only the following canonical slots may be used:

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

Do not invent additional slot labels during annotation.

---

# 3. Canonical Slot Order

When an utterance contains multiple slots, list them in this order:

1. main_symptom
2. site
3. onset
4. character
5. radiation
6. associated
7. timing
8. exacerbating
9. relieving
10. severity

Separate multiple slots with a semicolon.

Example:

```text
main_symptom;site;onset;character

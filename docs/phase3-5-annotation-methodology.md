# Phase 3.5 — LLM-Assisted Annotation Methodology

## Purpose

Phase 3.5 reduces manual annotation burden while preserving human
oversight over ambiguous and conflicting examples.

## Annotation Task

Patient utterances were classified according to the project's canonical
SOCRATES/OPQRST slots.

The task was explicitly linguistic and non-diagnostic.

Annotators were instructed not to infer diagnoses, physiological causes,
treatments, or unexpressed clinical information.

## Annotators

Two independent large language models were used to annotate the same
input examples using the same annotation protocol.

The second annotator was not shown the first annotator's output.

## Agreement

Annotations were compared across:

- review status
- SOCRATES/OPQRST slots
- ambiguity
- negation
- uncertainty
- context dependence

Examples with complete agreement were provisionally accepted.

Examples with disagreement were flagged for human adjudication.

## Human Review

All disagreements were manually reviewed.

A random sample of agreed annotations was also manually audited to
identify systematic errors shared by both models.

Unresolved or clinically sensitive cases were retained as
`needs_review` rather than forcing a label.

## Clinical Interpretation

The annotation task did not convert patient expressions into diagnoses
or disease mechanisms.

For example, expressions such as "heavy" were preserved as ambiguous
descriptions rather than automatically interpreted as weakness.

## Provenance

Each final annotation retains its original dataset and source ID together
with the annotation pathway used to establish the final label.

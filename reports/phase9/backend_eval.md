# Phase 9 Backend Evaluation

## Frozen TEST split

- Rows: 57
- Total annotated symptom slots: 98
- Multi-slot utterances: 19
- Successful webhook requests: 57/57

## Slot distribution

| Slot | Annotations |
|---|---:|
| main_symptom | 9 |
| site | 8 |
| onset | 13 |
| character | 13 |
| radiation | 8 |
| associated | 14 |
| timing | 9 |
| exacerbating | 7 |
| relieving | 6 |
| severity | 11 |

## Safety-signal classification

| Flag | Precision | Recall | F1 | Accuracy | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ambiguous | 100.00% | 28.57% | 44.44% | 91.23% | 2 | 0 | 5 | 50 |
| negated | 58.33% | 87.50% | 70.00% | 89.47% | 7 | 5 | 1 | 44 |
| uncertain | 20.00% | 50.00% | 28.57% | 91.23% | 1 | 4 | 1 | 51 |

## Evaluation method

The Phase 5 corpus is multi-label: one utterance may contain more than one symptom attribute in final_slots.

The ambiguity, negation and uncertainty labels are evaluated once per utterance. For the webhook call, the first annotated canonical slot is used as a deterministic target. This avoids weighting a multi-slot utterance multiple times.

This evaluation measures Phase 7 backend signal handling. It does not measure Dialogflow CX slot extraction or conversation-level multi-slot extraction.

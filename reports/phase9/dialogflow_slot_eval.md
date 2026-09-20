# Phase 9 Dialogflow Slot Evaluation

## Frozen TEST split

- Utterances: 57
- Annotated slot pairs: 98
- Multi-slot utterances: 19

## Overall pair-level results

- Successful Dialogflow API requests: 98/98
- Annotated slot captured on its collection page: 88/98 (89.80%)
- Exact utterance preserved as the parameter value: 77/98 (78.57%)

## Row-level results

- Utterances for which every annotated slot was capturable: 49/57 (85.96%)
- Utterances for which every annotated slot exactly preserved the utterance: 39/57 (68.42%)

## Per-slot results

| Slot | Pairs | Successful requests | Filled | Fill rate | Exact | Exact rate | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| main_symptom | 9 | 9 | 8 | 88.89% | 0 | 0.00% | 0 |
| site | 8 | 8 | 8 | 100.00% | 8 | 100.00% | 0 |
| onset | 13 | 13 | 13 | 100.00% | 13 | 100.00% | 0 |
| character | 13 | 13 | 13 | 100.00% | 13 | 100.00% | 0 |
| radiation | 8 | 8 | 8 | 100.00% | 8 | 100.00% | 0 |
| associated | 14 | 14 | 13 | 92.86% | 13 | 92.86% | 0 |
| timing | 9 | 9 | 3 | 33.33% | 0 | 0.00% | 0 |
| exacerbating | 7 | 7 | 7 | 100.00% | 7 | 100.00% | 0 |
| relieving | 6 | 6 | 6 | 100.00% | 6 | 100.00% | 0 |
| severity | 11 | 11 | 9 | 81.82% | 9 | 81.82% | 0 |

## Method

The Phase 5 corpus is multi-label. A single utterance may therefore have multiple entries in final_slots.

Each annotated slot is evaluated independently using a fresh Dialogflow session positioned on the corresponding collection page.

Webhook execution is disabled. This prevents Phase 7 backend behavior from affecting the Dialogflow extraction measurement.

Because the current MVP uses permissive free-text collection for several fields, slot-fill performance should not be interpreted as semantic medical entity normalization accuracy.

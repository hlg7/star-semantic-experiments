# Frozen held-out evaluator audit

**Status: all inference and AI review completed; no semantic passed every prespecified screening gate. Full-set semantic scoring has not started.**

Grounding DINO and Qwen each produced 240 predictions with zero evaluation errors. All 240 anonymous images were inspected in native-resolution contact sheets before model answers or reference target answers were read. Review labels were frozen with a timestamp and SHA-256, then joined to predictions. Model/config/question hashes, split membership, shared PNG hashes and recomputed primary scores were checked. The original labels remain unchanged after comparison.

This is AI review, not human ground truth. Same-thread research context, correlated images and existing scene families limit independence. A review disagreement can reflect ambiguous visual evidence, ontology or reviewer error; it is not automatically a detector/VLM error.

## Summary

| Semantic | Clear AI review / 40 | Binary decisions agreeing | Observed answers agreeing |
|---|---:|---:|---:|
| color | 36/40 | 36/36 | 31/36 |
| count | 12/40 | 9/12 | 9/12 |
| object | 36/40 | 32/36 | 32/36 |
| shape | 20/40 | 20/20 | 15/20 |
| spatial_relation | 24/40 | 24/24 | 21/24 |
| texture | 35/40 | 29/35 | 29/35 |

Binary agreement compares success/failure relative to the prompt target. Answer agreement compares the actual observed answer or missing status. Both exclude ambiguous/unclear AI review while reporting those excluded counts. Neither column is a human-validated accuracy estimate. Shared failures can yield perfect binary agreement despite wrong identity or attribute observations.

## Prespecified screening outcome

All six are **inconclusive because reference coverage or positive/negative denominators are inadequate**; several also miss performance targets on the available clear subset. No criterion was relaxed after seeing results.

- **color**: unmet gates: reference_failure_denominator. Clear review successes/failures: 28/8.
- **count**: unmet gates: clear_images, clear_prompts, reference_success_denominator, reference_failure_denominator, binary_agreement, answer_agreement, false_failure_rate. Clear review successes/failures: 4/8.
- **object**: unmet gates: reference_failure_denominator, binary_agreement, false_success_rate. Clear review successes/failures: 32/4.
- **shape**: unmet gates: clear_images, clear_prompts, reference_success_denominator, answer_agreement. Clear review successes/failures: 8/12.
- **spatial_relation**: unmet gates: clear_images, clear_prompts, reference_success_denominator. Clear review successes/failures: 4/20.
- **texture**: unmet gates: reference_failure_denominator, binary_agreement, answer_agreement, false_success_rate. Clear review successes/failures: 27/8.

The requirement for at least ten clear successes and ten clear failures cannot be met merely by adding repeated views of a few prompts. Here four conditions share each prompt. The clear count subset covers only three prompts; this does not establish reliability on dense counts.

## Practical findings

- **Color:** 36/36 binary agreement but 31/36 actual-answer agreement. Hourglass judgments differ between blue interior/brown frame (AI: multicolored) and frame color (VLM: black/brown). Main-surface ontology can be underspecified for transparent objects. There are only eight clear reference failures, fewer than the frozen minimum.
- **Object:** 32/36 agreement. Three disagreements are notebook queries over laptop images; notebook can mean a paper notebook or a notebook computer. The anonymous AI review used the paper sense. These are not established false detections without a prior category definition. One scarf was missed. Labels were not changed after discovering this issue.
- **Shape:** 20/20 binary agreement versus 15/20 observed-answer agreement. The evaluator can classify a loaf pan or tray as rectangular while AI marks the requested plate missing; both may nevertheless fail the prompt target. Half the images have ambiguous identity or perspective for the AI reviewer.
- **Count:** DINO matches 9/12 numerically clear labels, MAE 0.25 on those twelve only. It counts three where AI identifies four baskets in three images. Twenty-eight of forty images are unresolved due to dense books/bottles, overlapping mugs/hats/toys or remote/controller identity ambiguity. The clear-subset result must not be extrapolated to all counts.
- **Texture:** pattern has 20/20 answer agreement on clear images; surface has 9/15. Mixed smooth/rough stone surfaces and rough shallow dishes cause disagreements. Pattern includes only a small set of prompts and still lacks enough negative examples for a validated metric. A blanket claim that texture is reliable would hide this split.
- **Spatial:** 24/24 binary agreement versus 21/24 observed-answer agreement. Fourteen clear reviews say a required object is missing. All relation subtypes have fewer than ten clear images; separate depth and containment reliability is not established. Spoon versus small bowl identity and absent frames are remaining issues.

The evaluator reports ambiguous/unclear for only four images (all spatial primary outputs), while the AI reviewer leaves many more unresolved. This difference does not prove which side is right; it cautions against interpreting confident model answers as reliable observations.

## Subtypes

| Subtype | Clear / total | Answer agreement |
|---|---:|---:|
| color/color | 36/40 | 31/36 |
| count/single_category | 12/40 | 9/12 |
| object/identity | 36/40 | 32/36 |
| shape/outline | 20/40 | 15/20 |
| spatial_relation/above_below | 8/8 | 7/8 |
| spatial_relation/containment | 8/16 | 6/8 |
| spatial_relation/front_behind | 4/8 | 4/4 |
| spatial_relation/left_right | 4/8 | 4/4 |
| texture/pattern | 20/24 | 20/20 |
| texture/surface | 15/16 | 9/15 |

## Recommended next step

Do not launch all 6,000 as validated scores. First define category/attribute ambiguity explicitly at dataset metadata level (e.g. paper notebook versus computer, plate versus tray, transparent-object surface versus contents). Preserve the original 300 prompts and original generation results. If revising the evaluator after this audit, this held-out split becomes development evidence for that new revision; it cannot validate it independently.

For a new validation screen, sample from the remaining unused prompt IDs before inspecting their predictions, and preserve a separate validation split. The current experiment has only one seed and repeated scene templates. More samples may still lack enough clear successes/failures. Report insufficiency honestly rather than selecting images to manufacture a pass. An independent category-labeled diagnostic set may be needed for sensitivity/specificity, but cannot substitute for checking the actual STAR images.

An alternative is explicitly exploratory full-set scoring with these limitations and no reliability claim. That is a scientific scope choice, not automatically authorized by a passing screen; no full-set job was launched.

## Files

- `comparison.json`: full joined observations, raw tool predictions, protocol/run manifests, per-semantic/subtype/prompt summaries.
- `ai_labels.reviewed.json`: all 240 pre-prediction AI review labels.
- `labels.freeze.json`: timestamp and hash before prediction comparison.
- Frozen criteria: [validation plan](../../../data/semantic_eval_v2/validation/README.md).
- Reproduce with `python analyze_semantic_heldout.py --review-root <downloaded-heldout-directory> --output <report-directory>`.

GPU evaluation has finished. The Pod has not been stopped or deleted by this audit.

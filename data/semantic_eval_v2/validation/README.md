# Frozen held-out screening plan

This plan was frozen after development review and before held-out inference. It tests transfer of the existing settings despite known development weaknesses; it does not declare development success or certify accuracy. No detector threshold tuning or model substitution is included.

The held-out split has 240 existing images from 60 prompts (10 prompts × four conditions per semantic), disjoint from development prompts. The same scene families may occur in both splits; this is not out-of-domain validation.

## Per-semantic screening gates

| Requirement | Fixed target |
|---|---:|
| Execution/schema errors | 0 |
| Clear AI-review images | At least 30 of 40 |
| Distinct prompts represented by clear review | At least 8 of 10 |
| Binary success agreement on clear review | At least 90% |
| Observed answer agreement on clear review | At least 85% |
| Evaluator ambiguous/unclear fraction | At most 25% |
| Clear reference positives and negatives for directional error rates | At least 10 each |
| False success on clear reference failures | At most 10% |
| False failure on clear reference successes | At most 10% |

These are conservative operational targets, not published standards. All gates must pass; insufficient denominators are inconclusive. Count answer agreement means exact count; also report MAE with numeric coverage. For missing attribute targets, compare missing status rather than inventing an attribute. A shared wrong success score alone does not establish correct observation. Report the full denominator and every error/unknown status.

Texture pattern/surface and spatial 2D/depth/containment are reported separately. Fewer than ten clear images in a subtype provides descriptive evidence only. Four images share each prompt; report per-prompt results and do not treat 40 images as 40 independent prompt samples.

AI reviewers receive anonymous images and v2 questions, without expected answers, condition names or model outputs. Review labels must be frozen before joining predictions. Current-thread knowledge prevents claiming fully independent blindness. AI labels are not human ground truth; even passing these gates supports exploratory automated scoring only.

Any revision informed by held-out findings makes this split development data for that revision. Do not silently relabel to match predictions, tune on held-out scores, or launch the full 6,000-image evaluation automatically.

`plan.json` defines the frozen policy. `freeze.json` records SHA-256 hashes of code, questions, sample, settings and blank review labels. `ai_labels.template.json` contains only anonymous review questions and blank answers. The launcher checks hashes before inference and preserves separate tool outputs.

## Completed screen

Both tools completed 240 held-out images without evaluation errors. AI labels were frozen before inspecting predictions. No semantic passed every gate; all have insufficient reference coverage and some additionally miss performance targets. See [held-out audit](../../../reports/2026-09-08/heldout/README.md). This file records outcome without changing the hashed plan or inputs.

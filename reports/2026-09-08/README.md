# Semantic evaluator development review — September 8, 2026

**Status: execution repaired; calibration evidence does not yet support full evaluation.** Existing STAR images only. No new generation, held-out inference, or full 6,000-image semantic evaluation.

## Held-out follow-up

Both tools completed 240/240 without errors. All anonymous images were AI-reviewed and labels frozen before prediction comparison. No semantic passed every prespecified screening gate; insufficient reference coverage and observed disagreements are reported separately. See the [held-out audit](heldout/README.md). No full-set job has started.

## V2 follow-up

The schema-clarified v2 run completed 240/240 with zero errors and zero retries. See [v2 audit](v2_audit.md) and [joined raw comparison](v2_development_comparison.json). Visual validity remains limited; held-out and full-set evaluation are pending. The original v1 review below is preserved.

## Completed

- Grounding DINO: 240 development images processed without runtime errors. Of these, 144 were localization-only auxiliary checks, not semantic scores.
- Qwen: 240 first-pass responses, including 32 schema errors. Sixteen unsigned decimal strings were converted to integers without changing meaning; sixteen remaining invalid responses were rerun with an explicit schema reminder. All sixteen retries parsed successfully.
- Original responses retained under `/workspace/star-semantic-pilot/qwen-development`; normalization results in `qwen-rescored-v2`; rerun responses and manifest in `qwen-retry-v2`. No original result was overwritten.
- All 240 development images were visually inspected by Codex AI, with individual PNG rechecks for selected cases. Labels and comparison are included here. This is **AI visual review, not human ground truth**. Some model outputs were seen during earlier debugging, so the review is not fully blind or independent.

## Comparison against AI visual review

Each semantic has 40 images from 10 prompts × four conditions. The table compares the primary evaluator's binary success decision with the review-derived binary decision, excluding review labels marked ambiguous/unclear. Missing objects remain clear failures for attribute/relation tasks. Agreement on a shared failure does not prove agreement on the actual observed attribute or count.

| Semantic | Clear review subset | Matching binary decisions | Review ambiguous/unclear |
|---|---:|---:|---:|
| Object | 36 | 33 | 4 |
| Color | 32 | 32 | 8 |
| Shape | 36 | 25 | 4 |
| Texture | 32 | 24 | 8 |
| Count | 13 | 8 | 27 |
| Spatial relation | 26 | 20 | 14 |

These are descriptive development-set agreement counts, **not evaluator accuracy estimates** or independent statistical evidence. Review errors and conservative abstentions are possible. The small, correlated sample and selection of clear cases limit generalization. No thresholds were tuned to maximize these counts.

## Concrete issues

1. **Object identity must precede attributes.** `image_0107` contains a white pyramidal object; Qwen labels it triangular without establishing that it is a plate. `image_0127` contains an architectural opening/pillar, which Qwen calls a rectangular sign. DINO also detects the pyramidal object as plate, so simply adding DINO gating does not solve all identity errors.
2. **Detector false positives.** `image_0022` shows draped fabric; DINO produces a glove detection at approximately 0.346, while both Qwen and AI inspection reject glove presence. Raising a universal threshold could also remove real objects and is not yet justified.
3. **Count uncertainty and missing instances.** `image_0214` has four hats in the AI review, including a collapsed hat; both tools report three. In `image_0311`, DINO reports one hat, Qwen three, and the AI review confidently distinguishes two with additional fabric that remains debatable. Count labels on dense books, bottles and blurred instances often remain uncertain; do not calibrate from guessed AI counts.
4. **Shape conventions.** Square versus rectangular mats, circular versus oval trays, and three-dimensional pyramids require a consistent identity/shape rubric. A confident VLM category is not sufficient.
5. **Containment definition.** Apples protruding above bowl rims are labeled partial under the current strict review rule but inside by Qwen. This is primarily a rubric disagreement; it must not be presented as established VLM error. The definition should be settled before further scoring and applied to all development images uniformly.
6. **Duplicate objects and identity confusion.** Several vase/bowl scenes produce multiple category candidates. Keep ambiguity explicit; do not select the pair yielding the requested relation.
7. **Texture visibility.** Strong patterns are easier to inspect than surface roughness. Some disagreements are between rough and smooth/unclear, and some fine umbrella dots are subtle. Preserve pattern/surface breakdown and uncertainty.

## Next work

- Refine and freeze identity-first questions, duplicate-instance policy, containment convention and shape definitions on the development set. If question wording changes, rerun the affected development task consistently, not only the answers that disagree.
- Choose detection thresholds using reviewed evidence and inspect recall/false-positive tradeoffs; do not chase a desired intervention curve.
- Keep AI-uncertain images out of claims about evaluator correctness, while reporting coverage. Preserve all images in generator-success reporting with explicit uncertainty status.
- Only after the protocol is settled, run the disjoint held-out set. Full 6,000-image scoring remains pending.

Images and all inference artifacts are on the original network volume. Local anonymous image copies: `/Users/gaohanlin/Desktop/RP/semantic_review_20260908/ai-review-development`. PNG hashes are distinct from the historical float-tensor hashes; see the protocol documentation.

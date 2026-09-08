# V2 development audit

**Decision: execution is sound; semantic validity remains insufficient for a confirmatory full-set evaluation. Held-out evaluation has not started.**

The schema-clarified run completed 240/240 Qwen predictions with zero evaluation errors and zero retries. All source/config hashes matched local files, the output IDs matched the development split exactly, and all saved scores were recomputed from raw responses. No images were regenerated. Grounding DINO primary outputs were reused unchanged.

The initial v2 run had 20 invalid identity-status responses. Its artifacts remain separate. The clarification was applied to all development questions, not selected failures.

## Same-rubric descriptive agreement

This compares primary-evaluator binary success with historical AI visual review, excluding ambiguous/unclear review labels and all containment records. It is not accuracy: review is not human ground truth, samples are small and correlated, and shared failures can hide different observed answers. Containment was excluded uniformly because its definition changed.

| Semantic | Comparable clear images | v1 matching decisions | v2 matching decisions |
|---|---:|---:|---:|
| color | 32 | 32 | 32 |
| count | 13 | 8 | 8 |
| object | 36 | 33 | 33 |
| shape | 36 | 25 | 26 |
| spatial_relation | 18 | 16 | 16 |
| texture | 32 | 24 | 27 |

Object and count use unchanged DINO scores; unchanged agreement is not evidence about improved Qwen. Spatial results combine DINO for 2D position and Qwen for depth; containment is excluded here. The 40 count images include 27 uncertain historical review labels, so the clear subset is especially unrepresentative.

## Targeted visual rechecks

Twelve previously selected disagreement/rubric examples were re-opened at native resolution. This is a targeted audit, not a fresh blind annotation of all 240 images. Original AI labels were preserved.

- `image_0127`: a masonry passage with a white vertical structure; v2 now reports the queried sign missing. This repairs one identity error.
- `image_0107`: a white pyramid on a kitchen counter; v2 still asserts plate identity and triangular shape. An identity field does not guarantee identity recognition.
- `image_0222`: an oval framed mirror-like object; v2 reports no mirror. Reflective versus open-frame interpretation remains a potential visual ambiguity; the older review is not infallible.
- `image_0214` and `image_0311`: clear hats coexist with collapsed or partly visible fabric. Exact counts are sensitive to instance interpretation. These images do not justify assuming either the detector, VLM or AI reviewer is exact.
- `image_0050`: the vase/bowl scene supports possible category/referent confusion; Qwen reports the reverse horizontal relation. It is an auxiliary answer, not a replacement for the fixed DINO primary.
- `image_0138`: a cup and a lidded vessel; Qwen treats the latter as a coffee pot despite questionable identity. Strict object identity remains difficult.
- `image_0171`: a clock on a wall, with no clearly identifiable sign. Qwen invents a sign and produces an answer that contradicts its own relation explanation. This remains an auxiliary Qwen failure.
- `image_0011`: an apple is seated in a bowl with its top protruding. The v2 inside convention is appropriate for this example, but the explanation incorrectly claims no protrusion. Answer correctness and evidence faithfulness differ.
- `image_0250`: fine umbrella dots are called a checkered pattern; native 256-pixel resolution limits certainty.
- `image_0074`: visible grain on a vase is called smooth; surface texture remains less reliable than coarse patterns.
- `image_0124`: perspective complicates square versus rectangular mat classification; a confident label cannot remove that ambiguity.

## Next decision

Do not use these results as validated six-semantic metrics or launch all 6,000 evaluations yet. Preserve the existing two tools and general rubric. Next establish a documented validation plan with per-task coverage and error criteria, explicit pattern/surface and 2D/depth/containment breakdowns, and instance-localization evidence for detector errors. Do not tune thresholds from binary agreement alone or repeatedly rewrite prompts to fit the same examples. A held-out run can estimate transfer only after this plan is frozen; if its findings drive revisions, it becomes development data.

A conservative alternative is to publish all six as exploratory automated scores with explicit failure rates and uncertainty, rather than claiming validated semantic accuracy. This choice has not been silently made.

## Artifacts

- `v2_development_comparison.json`: all 240 joined records, raw v2 Qwen outputs, reused-primary decisions, and inference manifest.
- Local native image copies and raw run archives remain under `/Users/gaohanlin/Desktop/RP/semantic_review_20260908`.
- Remote run: `/workspace/star-semantic-pilot/v2-schema2/qwen-development`.
- GPU inference is finished. The Pod remains running; no stop/delete operation was issued.

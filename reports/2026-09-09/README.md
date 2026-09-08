# Exploratory semantic evaluation — September 9, 2026

**Completed: 6,000 records, 5,999 valid scores, one explicit evaluation error.** Grounding DINO supplied 2,600 primary evaluations and Qwen3-VL supplied 3,400. No images were regenerated. The frozen v3 rubric clarifies category identity and attribute definitions after development and held-out audits; these results are exploratory automatic scores, not validated semantic accuracy.

## Baseline versus full masking

| Semantic | Baseline | Full mask | Paired change | Gained / lost successes |
|---|---:|---:|---:|---:|
| Object | 94% | 90% | -4 pp | 0 / 2 |
| Color | 78% | 84% | +6 pp | 4 / 1 |
| Shape | 38% | 36% | -2 pp | 1 / 2 |
| Texture | 80% | 84% | +4 pp | 4 / 2 |
| Count | 18% | 16% | -2 pp | 4 / 5 |
| Spatial Relation | 26% | 26% | +0 pp | 2 / 2 |

Each endpoint uses 50 prompts with seed 42. Gains/losses count per-prompt transitions from baseline failure to success and vice versa. Net changes can hide different affected prompts: count loses five successes and gains four, while spatial relation gains two and loses two. Color and texture increases do not establish improved image semantics or quality. No inferential significance test is claimed.

Changes are generally small and non-monotonic. Global conditioning and contextualized embeddings remain available under this intervention; evaluator errors, a single seed and repeated scene families also limit interpretation. These data do not establish distinct causal semantic scale windows. Low baseline success for count, shape and spatial relation further limits a net-success curve; inspect baseline-correct retention with its smaller denominator.

## Reading the plots

- Prefix masks scales 1..k; suffix masks k+1..10. Boundary k runs from 0 to 10. Shared endpoints reuse identical images.
- **Success:** mean confirmed match. Incorrect, missing, ambiguous and unclear are zero; evaluation errors are excluded.
- **Paired change:** mean of masked score minus the score of the same prompt/seed's baseline, in percentage points. Uses matched valid pairs.
- **Uncertain outputs:** fraction marked ambiguous or unclear, not a confidence estimate. Missing-object frequency is separately available in CSV/JSON. DINO existence/count always yields a definite detection estimate; zero uncertainty does not mean zero uncertainty in reality.
- **Retention:** success among prompts whose baseline was already scored correct. The plot gives the effective denominator; count has only nine such baseline prompts, spatial relation thirteen.
- **Count deviation:** absolute difference between DINO's count and the requested count, not error against a true annotated image count. Numeric coverage is reported.

Lines are descriptive means. No error bars or confidence intervals are shown; four or twenty conditions from one prompt are not independent replications, and scene templates are shared across prompts.

The only invalid record is `p052_s42_suffix_08`: Qwen returned `silver`, outside the fixed color ontology, on both allowed attempts. Its raw answer is preserved. It was not mapped to another color or assigned zero. Color suffix k=8 has 49 valid observations and pairs; other main curve points have 50. The paired baseline mean for that point uses the same 49 prompts, while the success plot's dashed baseline is the full unmasked 50-prompt mean.

## Six-semantic overview

![Success and paired change](plots/overview.jpg)

| Semantic | Success | Paired change |
|---|---|---|
| Object | ![object success](plots/object_success_rate.png) | ![object paired change](plots/object_paired_delta.png) |
| Color | ![color success](plots/color_success_rate.png) | ![color paired change](plots/color_paired_delta.png) |
| Shape | ![shape success](plots/shape_success_rate.png) | ![shape paired change](plots/shape_paired_delta.png) |
| Texture | ![texture success](plots/texture_success_rate.png) | ![texture paired change](plots/texture_paired_delta.png) |
| Count | ![count success](plots/count_success_rate.png) | ![count paired change](plots/count_paired_delta.png) |
| Spatial Relation | ![spatial_relation success](plots/spatial_relation_success_rate.png) | ![spatial_relation paired change](plots/spatial_relation_paired_delta.png) |

## Coverage and retention

![Uncertain outputs and baseline-correct retention](plots/coverage_overview.jpg)

## Subtype figures

![texture pattern](plots/texture_pattern_success_rate.png)

![texture surface](plots/texture_surface_success_rate.png)

![spatial_relation above_below](plots/spatial_relation_above_below_success_rate.png)

![spatial_relation containment](plots/spatial_relation_containment_success_rate.png)

![spatial_relation front_behind](plots/spatial_relation_front_behind_success_rate.png)

![spatial_relation left_right](plots/spatial_relation_left_right_success_rate.png)

![Count deviation](plots/count_mae.png)

## Verification and files

The aggregation checked frozen code/question/config hashes, exact disjoint primary-tool partitions, all 6,000 canonical names, 20 conditions per prompt, generation provenance fields, raw-response score recomputation and equivalent prefix/suffix endpoints. All valid scores were recomputed; the invalid category remained an explicit error. Plot layout was visually checked. The code's semantic unit checks pass.

- [metrics.jsonl](metrics.jsonl): 6,000 records, raw predictions, observations, scores, errors, image hashes and paired differences.
- [summary.json](summary.json): errors, endpoint summaries, per-curve statistics and frozen run manifests.
- [curve_data.csv](curve_data.csv): denominators, gains/losses, status frequencies, retention and count deviation for all curves.
- [plots](plots): 31 figures in both PNG and PDF, plus two overview sheets.
- [Frozen v3 definitions](../../data/semantic_eval_v3/README.md) and [prior held-out audit](../2026-09-08/heldout/README.md).

Reproduce locally from downloaded raw results (no model inference):

```bash
python summarize_semantic_full.py --raw-root /path/to/downloaded/results --output reports/2026-09-09
python plot_semantic_full.py --report reports/2026-09-09
```

Install `requirements-plots.txt` for plotting. Model inference uses the separate semantic requirements and RunPod scripts. Original images and weights remain on the persistent RunPod volume; raw full-evaluation results are also downloaded locally. The user stopped the Pod after inference. Report preparation and plotting require no GPU.

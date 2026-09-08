#!/usr/bin/env bash
set -euo pipefail
# Run only inside the existing RunPod workspace after syncing v2 code.
cd /workspace/star-semantic-eval-v1
export HF_HOME=/workspace/star-semantic-assets
export TOKENIZERS_PARALLELISM=false
PYTHON=/workspace/star-semantic-env/bin/python
COMMON=(--images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --checks data/semantic_eval_v2/checks.json --split development)
"$PYTHON" run_semantic_pilot.py "${COMMON[@]}" --tool qwen_vlm --output /workspace/star-semantic-pilot/v2-schema2/qwen-development --preflight
"$PYTHON" run_semantic_pilot.py "${COMMON[@]}" --tool qwen_vlm --output /workspace/star-semantic-pilot/v2-schema2/qwen-development

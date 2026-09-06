# Pilot v1

手工构造六类各 10 个干预样本，共 60 条记录、54 条不同 prompt。用于小规模验证，尚未生成这批 baseline，也未指定 metric。

- `pilot_v1_review.md`：人工审阅表，加粗部分为 mask 目标。
- `pilot_v1.json`：可直接传给 `check_masking.py --input`；字符区间为左闭右开，token 索引由实际 tokenizer 定位。
- `pilot_v1_baseline_prompts.json`：去重后的 baseline prompt 列表。
- `pilot_v1_token_check.json`：在 RunPod 使用配套 CLIP tokenizer 的实际检查结果。
- `build_pilot.py`：手工样本源和导出工具；修改后重新导出并校验。

物体、颜色、形状、质感各含 5 条单物体与 5 条多物体样本；数量含 5 条单类别计数与 5 条多类别计数；空间关系包含 5 对反向关系。相同 prompt 共用 `prompt_id`，但不同 mask 目标是独立干预。

Texture 的图案与表面质感分别标记 subtype，后续应分开检查。空间关系的左右按观察者视角解释；前后和内外可能涉及遮挡。数量只屏蔽数词，保留名词复数形式。所有实验仍保留完整文本编码和 global 条件，因此不能将 token 屏蔽解释为删除全部相关语义信息。

`expected` 用于人工核对；多物体样本也描述参照物，最终 metric 可分别记录目标响应与其他对象的变化。`baseline_status` 当前均为 `not_evaluated`。不要按生成结果悄悄筛选样本；若之后依据 baseline 能力筛选，应保留原始集合并报告筛选规则与数量。

RunPod 上重新检查（无需加载模型）：

```bash
python validate_prompts.py --input data/pilot_v1.json --tokenizer /workspace/star-baseline-assets/weights/CLIP/tokenizer --output data/pilot_v1_token_check.json
```

2026-09-06：60 条全部通过 fast/官方 slow tokenizer ID 一致性、字符目标与完整 token 边界检查；最长序列 12 tokens（含特殊 token），上限 77。

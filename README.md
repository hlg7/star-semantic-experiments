# STAR Semantic Scale Experiments

基于 **STAR d30 / 256×256** 的尺度干预实验：只屏蔽 cross-attention 对目标文本 token 的访问，保持完整 global 条件和文本 embeddings。所有模型生成与评估均在 RunPod RTX 4090 上完成。

## 2026-09-06：今天完成的实验

- 验证原始 STAR 的 baseline 与 cross-attention mask 实现，保留官方 `[0]` batch 广播行为。
- 从最初六类各10条的短 prompt pilot，扩展到基于 CSFM 场景主题构造的 **六类各50条，共300条不同 prompt**；全部通过 tokenizer 和目标区间检查。
- 固定 **seed 42**，完成 **6,600 次生成**：每条20个不同条件，加无 hook 参考和全尺度 mask 重复两次校验。
- 对 **6,000 个正式输出**完成 **LPIPS + CLIPScore** 评估，生成下面12张曲线；校验重复不计入统计。本轮不使用 VQAScore。

[300条 prompt 审阅表](data/csfm50_v1/review.md) · [逐图指标](reports/2026-09-06/metrics.jsonl) · [曲线数据 CSV](reports/2026-09-06/curve_data.csv) · [数值摘要](reports/2026-09-06/results_summary.json)

## 六类尺度曲线

横轴 **k 是尺度分界点，不是额外生成尺度**。STAR 有10个尺度，token网格为 `1,2,3,4,5,6,8,10,13,16` 的平方。

- **蓝线 Prefix**：屏蔽尺度 `1..k`。k=0 为无 mask，k=10 为全尺度 mask。
- **橙线 Suffix**：屏蔽尺度 `k+1..10`。k=0 为全尺度 mask，k=10 为无 mask。
- 线为50条 prompt 的均值，阴影为 **25%–75%四分位范围，不是置信区间**。两条曲线共享等价端点，未重复采样。
- **LPIPS**：与同 prompt、同 seed baseline 的感知距离，越大表示图像改变越多，不代表质量越差。
- **CLIPScore**：图片与完整原始 prompt 的匹配分数，越高表示整体匹配更强；虚线为 baseline 均值，不直接表示目标语义正确率。

| Semantic | LPIPS | CLIPScore |
|---|---|---|
| **Object** | ![Object LPIPS](reports/2026-09-06/object_lpips.png) | ![Object CLIPScore](reports/2026-09-06/object_clipscore.png) |
| **Color** | ![Color LPIPS](reports/2026-09-06/color_lpips.png) | ![Color CLIPScore](reports/2026-09-06/color_clipscore.png) |
| **Shape** | ![Shape LPIPS](reports/2026-09-06/shape_lpips.png) | ![Shape CLIPScore](reports/2026-09-06/shape_clipscore.png) |
| **Texture** | ![Texture LPIPS](reports/2026-09-06/texture_lpips.png) | ![Texture CLIPScore](reports/2026-09-06/texture_clipscore.png) |
| **Count** | ![Count LPIPS](reports/2026-09-06/count_lpips.png) | ![Count CLIPScore](reports/2026-09-06/count_clipscore.png) |
| **Spatial relation** | ![Spatial relation LPIPS](reports/2026-09-06/spatial_relation_lpips.png) | ![Spatial relation CLIPScore](reports/2026-09-06/spatial_relation_clipscore.png) |

点击图查看大图；同目录提供各图的 PDF 和 [12图总览](reports/2026-09-06/overview.jpg)。各子图纵轴自动缩放，跨类别比较请看刻度或下面数值。

## 本轮观察

1. **较早开始的干预会造成可测的最终图像变化。** 六类仅 mask 第1尺度时，平均 LPIPS 约0.118–0.143；只 mask 最后第10尺度时，约0.0028–0.0043。Suffix 曲线在较晚的分界点总体接近零，Prefix 曲线并非严格单调。
2. **完整 prompt CLIPScore 大多变化较小，部分条件分数反而上升。** 不将这些上升解释为语义能力改善。全尺度 mask 时，Count 组的平均 CLIPScore 从0.8683下降到0.8568，LPIPS为0.1882；这是当前构造集合中的描述性结果，不是显著性结论。
3. **两项指标共同显示：图像改变不等于整体文本匹配下降。** 当前结果不能证明某种语义已被删除，也不足以确定每种语义的独有生成尺度。

全尺度 mask 的端点均值如下。`CLIP下降 = baseline − full mask`，负数表示分数上升。

| Semantic | Baseline CLIPScore | Full-mask CLIPScore | CLIP下降 | Full-mask LPIPS |
|---|---:|---:|---:|---:|
| Object | 0.8653 | 0.8709 | -0.0056 | 0.1378 |
| Color | 0.9018 | 0.9051 | -0.0032 | 0.1440 |
| Shape | 0.8677 | 0.8677 | +0.0000 | 0.1403 |
| Texture | 0.9103 | 0.9117 | -0.0014 | 0.1413 |
| Count | 0.8683 | 0.8568 | +0.0116 | 0.1882 |
| Spatial relation | 0.8795 | 0.8804 | -0.0009 | 0.1336 |

## 实验设置与验证

| 项目 | 本轮设置 |
|---|---|
| Backbone | 原始 STAR d30，256×256；30层、10个尺度 |
| 生成 | seed=42，B=1，CFG=4，top-k=600，top-p=0.8，sampler关闭 |
| 数值配置 | FP32权重、FP16 autocast、math SDP、TF32关闭 |
| 干预 | 在所选尺度的全部cross-attention层/head，将目标key位置bias设为−∞ |
| 文本条件 | 完整text embeddings和global pooled features固定；空文本分支的mask保持原样 |
| CLIPScore | OpenAI CLIP ViT-B/32；前缀`A photo depicts `；`2.5 × max(cosine, 0)`；FP32 |
| LPIPS | lpips==0.1.4，AlexNet，权重版本0.1；RGB 256×256、像素范围[-1,1] |
| 设备/环境 | RTX4090 24GB；Python3.12.3；torch2.8.0+cu128；torchvision0.23.0+cu128 |

**保留原始 `[0]` 行为**：官方 block 取 conditional cross-attention 输出后广播到两个CFG分支，因此本实验修改条件分支的key访问后，两条CFG分支都会接收被干预的cross-attention输出。这不是“修正版独立双分支”的实验。

[独立审计摘要](reports/2026-09-06/audit_summary.json)：300条输入的无mask与无hook输出哈希全部一致，全尺度mask重复全部一致，所有原始文本/global条件哈希保持不变。共有1,890,000个层/尺度审计点。为控制批量开销，仅每类首条进行实际QK概率重算，共37,800个概率检查点，其中19,800个mask点的目标权重全部为零；其余输入执行结构检查，不宣称对所有样本都重算了注意力概率。300个baseline的LPIPS自比较和CLIP分数差检查通过。

[生成配置](reports/2026-09-06/generation_manifest.json) · [生成完成摘要](reports/2026-09-06/generation_summary.json) · [评估配置](reports/2026-09-06/metric_manifest.json) · [评估完成摘要](reports/2026-09-06/metric_summary.json) · [token检查](reports/2026-09-06/token_check.json)

## 解释边界

- **单seed、受控组合样本。** Prompt来自CSFM的10个场景主题，经人工替换对象、属性、数量和关系；不是独立随机抽取的300条原始caption。共享句式和场景引入相关性，各类别的对象配置和token长度也未完全匹配。详见[数据说明](data/csfm50_v1/README.md)。
- **保留global与上下文语义。** 屏蔽目标token访问不等于从模型条件中删除全部相关信息。
- **累积干预有下游传播。** Prefix/Suffix屏蔽长度随k改变；较早的干预有更多后续生成步骤，LPIPS差异不能直接定位独立的“语义负责尺度”。本轮没有非目标token placebo对照。
- **缺少目标语义正确率。** LPIPS对布局和外观变化敏感，完整prompt CLIPScore可能掩盖局部错误；本轮没有VQA或人工成功率统计，不以CLIP略升推断语义改善。
- 所有300条预先构造的样本均保留，没有按生成结果筛选“成功样本”。图中阴影是样本分布，不是跨seed稳定性证据。

## 在 RunPod 复现

保留已验证的 CUDA torch/torchvision 组合，不需要降级到torch2.1。仅在RunPod运行生成和评分；本地可编辑数据与报告。

```bash
cd /workspace/star-semantic-experiments
HF_HUB_ENABLE_HF_TRANSFER=0 bash prepare_runpod.sh /workspace/star-baseline-assets
python validate_prompts.py --input data/csfm50_v1/prompts.json \
  --tokenizer /workspace/star-baseline-assets/weights/CLIP/tokenizer \
  --output /workspace/csfm50-token-check.json

# 每次生成使用新的输出目录；目前不支持从中断处续生成。
python -u check_masking.py --input data/csfm50_v1/prompts.json \
  --output /workspace/star-csfm50-20260906 --seeds 42 \
  --weight-audit first-per-semantic

# 单独评估环境，复用已安装的CUDA torch；不修改STAR的transformers版本。
python -m venv --system-site-packages /workspace/star-metrics-env
/workspace/star-metrics-env/bin/python -m pip install --no-deps -r requirements-metrics.txt
/workspace/star-metrics-env/bin/python evaluate_metrics.py \
  --run /workspace/star-csfm50-20260906 \
  --output /workspace/star-csfm50-metrics-20260906
/workspace/star-metrics-env/bin/python plot_metrics.py \
  --metrics /workspace/star-csfm50-metrics-20260906 \
  --output /workspace/star-csfm50-report-20260906
```

官方源码固定为`4ae4492b45bfa1ac24eadcf83c8d474837bfc4b1`，权重仓库固定为`23fab671cb225c27a85321309129994498185338`。本次生成脚本来自提交`51aa98f`；评估来自`5bfa966`；绘图使用当前`plot_metrics.py`。评估代码可复用完整阶段缓存，缓存配置不匹配时拒绝混用。完整6600张PNG和逐层生成日志保留在RunPod输出目录；GitHub保存prompt、代码、逐图指标、配置、审计摘要和图表，不上传模型权重。

## 今日早期探索记录

- 初始短prompt pilot：六类各10个目标，60条记录对应54条不同prompt。生成54×2张原始baseline，重复结果一致；人工初查发现形状、属性绑定和空间关系错误。
- CSFM风格预览：六类各5个目标，30条记录对应27条不同prompt，完成文本与token检查，未单独生成该预览集。
- 本页结果来自后续300条受控prompt的完整尺度实验，不将前述pilot或预览混入统计。

## 参考

- [STAR官方源码](https://github.com/Davinci-XLab/STAR-T2I) / [公开权重](https://huggingface.co/taocrayon/STAR)
- [CSFM-ImageNet1K-Caption](https://huggingface.co/datasets/junwann/CSFM-ImageNet1K-Caption)：数据卡标注MIT；caption由Qwen3-VL-8B Instruct生成。
- [CLIPScore官方实现](https://github.com/jmhessel/clipscore) / [OpenAI CLIP](https://github.com/openai/CLIP)
- [LPIPS官方实现](https://github.com/richzhang/PerceptualSimilarity)

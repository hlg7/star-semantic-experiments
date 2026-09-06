# STAR baseline 检查（仅在 RunPod 运行）

包括 baseline 诊断与小规模尺度 masking 正确性检查；尚不包含正式 prompt 数据集或 semantic metric。

## 尺度 masking 检查

在已准备好 assets 的 RunPod 上执行：

```bash
python -u check_masking.py --assets /workspace/star-baseline-assets --output /workspace/star-mask-check-001
```

默认输入是 `mask_smoke.json` 中的 `A red car.`，目标 `red`，字符区间 `[2,5)`。输入为包含 `id`、`prompt`、`semantic`、`spans` 的 JSON 数组，区间使用 Python 字符索引（左闭右开）。可用 `--input` 指定其他文件。

程序用配套 fast tokenizer 定位字符区间，并要求它与实际 CLIPTokenizer 的完整 token IDs 完全一致。拒绝截断、无对应 token 或切断 token 的目标区间，不屏蔽特殊 token。

固定原始 STAR `[0]` 广播行为、B=1、完整 global 特征与原始文本 embeddings。仅通过 cross-attention pre-hook 改动条件分支的 attention bias，所有层和 head 均生效。空文本分支的原始 mask 不变，但因原始 `[0]` 行为，两条 CFG 分支最终都会收到被干预的 conditional attention 输出。

对于 10 个尺度，`prefix k` 屏蔽 1 至 k，`suffix k` 屏蔽 k+1 至 10；k 从 0 到 10。合并相同端点后有 20 个唯一条件，另加无 hook 参考和全程 mask 重复，共 22 次生成。`runs.jsonl` 的 aliases 保存等价条件名称。

检查所有层/尺度的目标 attention 权重（用实际传入 SDP 的 Q/K、scale 和 bias，以 FP32 重算 softmax）；被 mask 时必须严格为零。保留原 SDP 计算结果，不用重算值替代生成。额外检查 no-op 与无 hook 参考逐位一致、干预前累计视觉状态哈希一致、原始文本和 global 哈希不变、全程 mask 重复一致。原始 self-attention 缓存保留，允许前段干预的影响传播到后续尺度。

结果写入 PNG、manifest.json、runs.jsonl 和完成后才生成的 summary.json。使用全新输出目录；目前是完整审计入口，不是高吞吐或断点续跑的正式批处理入口。环境已在 Python 3.12.3、PyTorch 2.8.0+cu128、torchvision 0.23.0+cu128、RTX 4090 上完成 baseline 实测；保留 Pod 已有的这套 PyTorch，不必降级。

## 环境与准备

使用 Linux、Python 3.10/3.11、NVIDIA CUDA 环境。一个可采用的基础组合是 PyTorch 2.1.2 + torchvision 0.16.2 + CUDA 12.1；CUDA 驱动需兼容。此组合尚未在 RunPod 实测。模型保留 FP32 权重、FP16 autocast，并使用 math attention 做诊断，因此不要据论文推理显存或速度估计本脚本资源开销。

将本目录上传到 RunPod，例如 `/workspace/RP/star_baseline`，然后执行：

```bash
cd /workspace/RP/star_baseline
# 若镜像未提供配套 torch/torchvision，在独立环境中安装：
python -m pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121
bash prepare_runpod.sh /workspace/star-baseline-assets
python check_baseline.py --assets /workspace/star-baseline-assets --output /workspace/star-check-001
```

准备脚本会下载固定版本的官方源码、d30 256 checkpoint、原始 VQ-VAE 和配套 CLIP。checkpoint 是训练快照，可能明显大于模型推理权重；预留磁盘和 CPU 内存，首次运行只加载这一个分辨率。使用持久化卷保存 assets 和输出。

源码固定为 `4ae4492b45bfa1ac24eadcf83c8d474837bfc4b1`，权重仓库固定为 `23fab671cb225c27a85321309129994498185338`。脚本要求官方 checkout 干净，采用 strict 权重加载；若权重键不匹配，停止并保留错误，不通过 `strict=False` 绕过。

## 检查内容

默认 3 个手工 prompt、1 个 seed、2 种模式，每种重复 2 次，共 12 张图。一次只生成一个 prompt，CFG 内部仍是条件与空文本两个分支。

- `upstream`：保留公开代码 `cross_attn(...)[0]` 的行为。
- `corrected`：仅在内存中去掉 AttnBlock 内两处 `[0]`，保留完整 batch 输出。不会修改官方源码或权重。
- 两种模式均禁用可选 fused 算子、使用 math SDP 和相同的确定性设置。因此 upstream 指保留原始 batch 逻辑，不代表逐位复现官方加速配置。
- 同一 prompt 的文本序列、padding mask 和 global pooled feature 只编码一次，运行后校验哈希不变。
- 重复生成的浮点图像哈希必须一致。不支持的确定性算子会直接报错，不静默退化。
- 每个尺度记录第一层 cross-attention 在 `[0]` 索引之前的两分支 RMS 差异。它不是语义对齐 metric，也不是实际残差差异的测量。

保留官方逐尺度 CFG：`t = cfg * si / (K - 1)`，最终 logits 为 `(1+t)*conditional - t*unconditional`。本脚本不启用 causal-driven sampler。

自定义 prompt 文件为 JSON 字符串数组，使用 `--prompts /workspace/prompts.json`；更多随机种子使用 `--seeds 42 123`。超出 CLIP 上限的 prompt 会报错，避免静默截断。每次使用新的输出目录，诊断阶段不做断点续跑。

## 输出与判断

- `manifest.json`：版本、GPU、精度、模型与采样配置。
- `runs.jsonl`：每次生成的 token、条件哈希、图片哈希、耗时、显存峰值与 attention 诊断。
- `*.png`：两种实现及重复生成的配对图片。
- `summary.json`：完成次数和重复一致性结果，仅在整个检查完成后写出。

先确认 strict 加载成功、无 NaN、重复结果一致、文本条件保持不变，再比较两种模式的图像质量和 prompt 响应。修正模式成功生成、甚至质量更好，都不能证明它与 checkpoint 训练时的代码一致。正式 masking 实验必须明确采用哪种实现；不要把两种结果混成一个 baseline。

已在 RunPod 的 Python 3.12.3 / PyTorch 2.8.0+cu128 / RTX 4090 环境完成单 prompt baseline 检查：两种模式各重复两次，重复哈希一致，原始文本条件保持不变。没有在本地运行模型。

2026-09-06 尺度 masking 检查也已通过：`A red car.`、seed 42、目标 token 索引 2（`red</w>`），共 22 次生成。6300 个层/尺度审计点中，3300 个屏蔽点的目标权重均为零；所有 global/文本条件哈希一致，no-op 与之前 baseline 浮点输出完全相同，干预前轨迹及全程 mask 重复检查均通过。峰值 CUDA allocated memory 约 8.43 GiB。全程屏蔽后这一例仍呈现红色汽车，不能据此推断颜色的普遍尺度规律或 mask 无效。

## 依据

- [官方源码](https://github.com/Davinci-XLab/STAR-T2I)
- [公开权重](https://huggingface.co/taocrayon/STAR/tree/main)
- [作者说明公开 1024 权重不含 sampler](https://github.com/Davinci-XLab/STAR-T2I/issues/2#issuecomment-2710601993)
- [作者说明 VQ-VAE 沿用 VAR](https://github.com/Davinci-XLab/STAR-T2I/issues/5#issuecomment-3031960701)

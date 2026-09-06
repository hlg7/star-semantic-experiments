# CSFM 场景主题的受控 prompt 集合（50 × 6）

本集合用于 2026-09-06 的单 seed 探索实验，不是正式 benchmark。

共 300 条不同 prompt：object、color、shape、texture、count、spatial_relation 各 50 条；20–37 个空格分词。所有目标用左闭右开字符区间标注。RunPod 配套 CLIP slow/fast tokenizer 全部一致，目标边界全部有效；最长 43 tokens，未截断。

[人工审阅表](review.md) · [完整 JSON](prompts.json) · [构造脚本](build.py)

## 来源与构造

[CSFM-ImageNet1K-Caption](https://huggingface.co/datasets/junwann/CSFM-ImageNet1K-Caption) 的 validation caption 提供场景素材。原始文本池在 `source_pool.json`；每条实验样本记录来源 id/path 与改写说明。素材由 Qwen3-VL-8B Instruct 生成，原图未检查。

实际实验是基于 10 个场景主题的受控组合：草地、咖啡桌、图书馆、花园小路、瓷砖地面、办公桌、工作台、厨房、沙漠和庭院。主体、属性、数量与关系均可能人工替换，不把改写当作原图 ground truth。不能将 300 条描述成独立随机抽取的 300 条自然 caption。

- Object：50 个主体。
- Color：10 种颜色各 5 条；包含常见及不常见的对象–颜色搭配。
- Shape：5 种几何轮廓各 10 条，目标为物体外轮廓。
- Texture：striped/checkered/polka-dotted 各 10 条；rough/smooth 各 10 条。图案与表面质感用 subtype 区分。
- Count：2、3、4、5、6 各 10 条。数书样本移除了背景书架，避免额外书本干扰。
- Spatial relation：left/right 各 10 条，above/below、front/behind、inside/outside 各 5 条。左右按观察者视角；前后与容纳可能存在遮挡歧义。

## 使用边界

文本和 token 检查先于生成；没有根据模型生成成功率筛选或替换样本。共享场景、主体和句式意味着样本相关；本轮仅 seed 42，不能据此推断跨 seed 的稳定性。曲线阴影表示样本四分位范围，不是置信区间。各语义类别的背景、目标长度和对象配置并非完全匹配，不将类别间数值排序解释为纯语义因果差异。

Global 与 contextual text embeddings 保留完整 prompt，干预仅阻断指定尺度的目标 token 注意力访问。LPIPS 和完整 prompt CLIPScore 不直接评估目标语义是否正确。

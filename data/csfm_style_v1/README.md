# CSFM style preview v1

2026-09-06：六类各 5 个语义目标，共 30 条记录、27 条独立 prompt。仅用于确认文本风格，尚未生成这批 baseline，也不是最终每类 100 条的正式集合。

来源：[junwann/CSFM-ImageNet1K-Caption](https://huggingface.co/datasets/junwann/CSFM-ImageNet1K-Caption)。数据卡标注 MIT，并说明 caption 由 Qwen3-VL-8B Instruct 对 ImageNet-1K 生成。本次从 validation 若干位置抽取少量文本作为素材，不是随机代表性抽样。保留来源 id、path、原始 caption 和改写记录；未读取原图，不把新增或修改的内容当作原图 ground truth。

- `review.md`：30 条 prompt 表，目标加粗；后附原始 caption 与改写记录。
- `prompts.json`：兼容现有 masking 输入，spans 为左闭右开字符区间。
- `baseline_prompts.json`：27 条去重后的完整 prompt，尚未运行。
- `token_check.json`：在 RunPod 使用 STAR 配套 tokenizer 检查的结果。

全部 prompt 为 23–25 个英文空格分词，实际 CLIP 序列最长 31 tokens（含特殊 token），30 条目标均通过 slow/fast ID 一致性和完整 token 边界检查。计数字符串的词数不代替 tokenizer 长度。

这版包含整物体属性和部件属性（沙子的颜色、沙漏底座形状、日晷部件形状），subtype 单独标记；最终集合需确定是否都纳入。背景可出现其他属性，但本条只干预 target_object 对应的 target_text。空间关系左右为观察者视角，左右两条是仅替换方向的配对样本。计数为 2–4，未给目标同义数词或重复身份提示。

这些只是风格示例，不能据此决定最终对象频率、semantic 子类比例或目标 token 位置分布。正式构造时应扩大来源类别、平衡长度和对象配置，并记录共享来源和共享 prompt，避免把它们视为完全独立样本。

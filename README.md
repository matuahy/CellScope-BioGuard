# CellScope BioGuard

**科研人员用大模型读单细胞文献时，哪些请求会被生物安全护栏误拦？**

CellScope BioGuard 将中文文献请求判为放行、澄清或限制。它评估用户希望助手提供的帮助。例如，研究者询问昆虫精巢图谱中的 RNA 信号能否证明蛋白定位，即使证据不足，助手仍可解释推断的边界。输入判别与科学答案质量分别评价。

在 436 条原创请求上，模型自行判断与项目参考标签符合 **428 条（98.17%）**。在有五种条件可对照的 48 条请求上，各条件均判对 **48/48**。三路融合检索取出的前三张解释卡片在 **42/48** 条请求中命中参考依据，边界配对检索为 **39/48**。该样本支持讨论依据质量，动作准确率已达到题集上限。

**先看结果**　[评测报告](results.md) · [可打印 PDF](results/report.pdf) · [离线演示](demo/index.html)

## 项目导航

| 想了解什么 | 从这里开始 |
|---|---|
| 哪些请求应放行、澄清或限制 | [政策与知识库](policy/knowledge.json)，包含 5 条规则、43 张解释卡片和 29 条来源记录 |
| 用哪些请求做评测 | [评测数据](data/requests.jsonl) 和 [分组索引](data/groups.json)，同一请求可用于回归或稳定性检验 |
| 模型如何判别 | [判别与引用校验](bioguard/judge.py)、[本地检索](bioguard/retrieval.py)、[请求传输与输出校验](bioguard/core.py) |
| 如何复核数字和错误 | [运行入口](evaluate.py)、[分条件指标](results/summary.csv)、[逐题原始记录](results/records/) |

## 方法

系统接收请求后，本地 BGE 模型与 BM25 分别排序解释卡片。融合条件以 RRF（k=60）合并原文语义、扩展文本语义和词项三路排名，选取三张卡片。模型接收当前输入、固定政策和选中的解释，再输出动作、规则及简短理由。动作和引用分开校验，返回的引用须来自实际提供的卡片。

云端评测限于经内容哈希核对的原创请求，发送给模型的用户消息只含请求文本。演示中的自由输入在本机检索，展示匹配依据。已记录的模型动作可以断网回放。模型服务商自身的安全机制适用于所有 API 条件。

## 查看和复核

下载并解压项目，双击 `demo/index.html`，即可查看 48 题在五种条件下的 240 条逐题结果。评测报告和结果复核无需密钥或模型权重。在仓库根目录执行以下命令，使用 Python 3.11 即可。

```powershell
python -X utf8 evaluate.py verify
```

## 体验本地检索

已有本地环境和权重时，直接运行最后一行。在 Windows 上从空目录安装时，先在仓库根目录执行以下命令。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.6,<3"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-small-zh-v1.5', revision='7999e1d', local_dir='models/bge-small-zh-v1.5', allow_patterns=['model.safetensors','config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt'])"
.\.venv\Scripts\python.exe -X utf8 demo_server.py
```

浏览器打开本机地址 `http://127.0.0.1:8765`。在“本地检索体验”输入一条文献问题，可查看卡片、来源和排序。

## 调用 API 复测

交互终端会隐藏输入密钥，也可从环境变量 `DASHSCOPE_API_KEY` 读取。以下命令分别对应证据对照的 240 次判别和全题库模型自行判断的 436 次判别，按服务商计费。每次执行写入独立的 `local-runs/` 目录。云端使用 `deepseek-v4.1-flash`，温度为 0。

```powershell
.\.venv\Scripts\python.exe -X utf8 evaluate.py run --group evidence-comparison --method unprompted none boundary fusion low_relevance
python -X utf8 evaluate.py run --group all --method unprompted
```

`unprompted` 表示模型自行判断，`none` 表示提供固定政策，`boundary` 表示附加边界配对卡片，`fusion` 表示附加融合检索卡片，`low_relevance` 表示附加低相关卡片。当前入口使用证据对照实验的政策，其他数据集下的早期实验配置可在对应原始记录中查阅。

**GitHub 上传范围**　上传本 README 所在的项目内容；本地虚拟环境、模型权重、临时运行和凭证已在 [.gitignore](.gitignore) 中排除。分发 ZIP 已按同一范围打包。

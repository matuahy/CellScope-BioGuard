# 运行记录索引

每个目录保留当时写入的记录和配置。检索诊断只在本机运行。网络失败和未完成的试跑单列，行数包含这些记录。

| 场景 | 用途 | 账本行数 |
|---|---|---:|
| 任务与政策边界 | [回归对照](records/boundary-regression/decisions.jsonl) | 72 |
| 任务与政策边界 | [通用政策对照](records/boundary-standard-policy/decisions.jsonl) | 128 |
| 任务与政策边界 | [任务级政策对照](records/boundary-task-policy/decisions.jsonl) | 128 |
| 引用格式 | [工程试跑](records/citation-format-pilot/decisions.jsonl) | 77 |
| 语言与上下文 | [挑战集判别](records/context-challenge/decisions.jsonl) | 288 |
| 语言与上下文 | [检索诊断](records/context-index/retrieval.json) | 0 |
| 语言与上下文 | [回归对照](records/context-regression/decisions.jsonl) | 180 |
| 语言与上下文 | [重复稳定性](records/context-stability/decisions.jsonl) | 24 |
| 跨主题覆盖 | [开发集判别](records/coverage-calibration/decisions.jsonl) | 60 |
| 跨主题覆盖 | [留出集判别](records/coverage-holdout/decisions.jsonl) | 180 |
| 跨主题覆盖 | [开发集检索](records/coverage-index-calibration/retrieval.json) | 0 |
| 跨主题覆盖 | [留出集检索](records/coverage-index-holdout/retrieval.json) | 0 |
| 跨主题覆盖 | [政策解释检索核查](records/coverage-index-policy/retrieval.json) | 0 |
| 检索依据 | [同题四种政策条件](records/evidence-comparison/decisions.jsonl) | 192 |
| 检索依据 | [回归对照](records/evidence-regression/decisions.jsonl) | 72 |
| 检索依据 | [重复稳定性](records/evidence-stability/decisions.jsonl) | 24 |
| 无项目政策 | [全量请求](records/model-only/decisions.jsonl) | 436 |
| 基础文献阅读 | [开发集判别](records/reading-calibration/decisions.jsonl) | 36 |
| 基础文献阅读 | [开发集政策对照](records/reading-calibration-policy/decisions.jsonl) | 24 |
| 基础文献阅读 | [留出集判别](records/reading-holdout/decisions.jsonl) | 96 |
| 基础文献阅读 | [开发集检索](records/reading-index-calibration/retrieval.json) | 0 |
| 基础文献阅读 | [留出集检索](records/reading-index-holdout/retrieval.json) | 0 |
| 基础文献阅读 | [政策解释检索核查](records/reading-index-policy/retrieval.json) | 0 |
| 网络连接 | [网络失败诊断](records/transport-diagnostic/decisions.jsonl) | 60 |

# 各分组的无项目政策对照

相同文本复用同一条模型响应。表中包含重叠分组，各行分母不可相加。

| 分组标识 | 正确 | 题数 |
|---|---:|---:|
| reading-calibration | 12 | 12 |
| reading-holdout | 46 | 48 |
| coverage-calibration | 29 | 30 |
| coverage-calibration-source | 29 | 30 |
| coverage-holdout | 88 | 90 |
| context-challenge | 142 | 144 |
| context-regression | 88 | 90 |
| context-stability | 11 | 12 |
| boundary-challenge | 63 | 64 |
| boundary-regression | 34 | 36 |
| citation-pilot | 48 | 48 |
| citation-pilot-regression | 34 | 36 |
| citation-pilot-stability | 12 | 12 |
| evidence-comparison | 48 | 48 |
| evidence-regression | 34 | 36 |
| evidence-stability | 12 | 12 |

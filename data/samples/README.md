# 回归用例（AutoGrader）

四份标准用例，供验收与回归使用。`.md` 是源文件，`.docx` 由 md 转换生成（转换脚本在 A 的工作区）。
真机实测值来自 2026-09-22，模型 glm-4.7（关闭思考）。

| 文件 | 用途 | 实测总分 | 判定标准 |
| --- | --- | --- | --- |
| case_good | 章节完整，含多组测试数据与异常/边界分析 | 100.0 | 不得被判跑题，应 ≥ 90 |
| case_mid | 章节齐全，但测试只有一组、分析基本复述 | 68.9 | 应在 70 分上下 |
| case_code_only | 大段代码、几乎没有正文说明 | 15.0 | 不得被判跑题，应在 12 到 20 之间 |
| case_offtopic | 食堂消费调研，内容与数据结构实验无关 | 0.0 | **必须 0 分、七项全部 absent** |

case_offtopic 是四份里最关键的一份：它验证的是确定性跑题判据——**报告正文里不出现任何数据结构术语时，后端强制全部清零**，不依赖模型措辞。改动评分链路后必须重跑它。

## 用法

```bash
cd backend
rm -f autograder.db
python scripts/seed.py
python scripts/run_one_report.py ../data/samples/case_offtopic.docx
```

## 两个已知坑

1. **上传幂等键是「文件内容 SHA-256 + template_id」，不是文件名。** 同一份文件重复上传会返回 4091。脚本化测试时要么每次往 docx 里追加一段随机文字造唯一副本，要么每轮换干净库。
2. **跑 httpx 相关脚本前清掉 `HTTP_PROXY` / `HTTPS_PROXY`。** 带代理变量时 multipart 上传会被代理改写，表现为上传返回 404，与代码无关。

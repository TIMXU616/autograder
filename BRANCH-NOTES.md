# a/backend-p2 分支说明（A 的后端 P2 冻结版）

本分支基于 `dev` 最新提交建立，与 `dev` 有共同祖先，合并无需 `--allow-unrelated-histories`。

## 新增内容
- `backend/`：完整后端实现（routes / controllers / services / repositories 四层，pytest 16 passed）
- `templates/grading/`：数据结构实验报告评分点（7 项 100 分）+ 机器版 JSON
- `docs/`：接口契约 v1、openapi.yaml、需求文档、平台能力清单、部署记录、试跑记录（4 份）、代码真值源与部署口径
- `prompt-library/`：交给 LearnBuddy 的提示词存档（P1-01 ~ P2-06F）

## 未改动仓库已有文件
`docs/api.md`、`docs/interface-contract-v1.md`、`docs/contract-diff.md`、`docs/requirements.md`、
`frontend/**`、`backend/README.md`、`data/README.md`、`README.md`、`.gitignore`、`.gitattributes`
全部保持 dev 分支原样。

注意：仓库里现在有三份与接口有关的文档 —— `docs/api.md`、`docs/interface-contract-v1.md`、
以及本分支新增的 `docs/接口契约.md`。**接口定义以 `docs/接口契约.md` 为唯一依据**
（字段最全、含 13 个错误码表、EARS 验收标准、变更记录），另两份建议在本次合并后标注为历史文档。

## 真机验收结论（2026-09-22，模型 glm-4.7）
| 用例 | 实测 |
| --- | --- |
| 跑题报告（食堂调研）连跑三次 | total = 0.0，七项全 absent（正文无任何数据结构术语即判跑题） |
| 只有代码 | 15.0，未被误判跑题 |
| 优秀报告 | 100.0 |
| 中等报告 | 68.9 |
| 参数类错误 | 统一 HTTP 400 + code 4002 + {code,message,detail} |
| pytest | 16 passed |

## 合入后自检
```bash
cd backend
pip install -r requirements.txt
python -m pytest -q                 # 期望 16 passed
python scripts/seed.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
python scripts/smoke.py             # 期望最后一行 PASS
```

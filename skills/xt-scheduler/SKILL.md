---
name: xt-scheduler
description: 行途技术全局定时任务控制面。聚合 registry + WorkBuddy DB + Claude Code scheduled_tasks + GH Actions + LaunchAgent + crontab，让任意 agent 一眼看全「有哪些定时任务 / 状态 / 产出在哪 / 是否漂移」，并支持 list/show/drift 纠偏。
---

# xt-scheduler — 全局定时任务控制面

## 何时用
- 想**综合查看**全部 xingtu 定时任务（不分平台、不分仓库）。
- 排查**漂移**：registry 登记的 id/状态 与平台运行时真实状态不一致。
- 新建/改/删任务前的**先回写 registry** 步骤（registry 是唯一事实索引）。

## 调用（本仓内）
```bash
python3 tools/xt_scheduler.py list [--category 工作|创作|生活|信源] [--platform wb|cc|gh|launchagent|cron]
python3 tools/xt_scheduler.py show <slug>
python3 tools/xt_scheduler.py drift
python3 tools/xt_scheduler.py sources
```

## 设计铁律（来自 SCHEDULED-SYSTEM-DESIGN.md）
1. **registry 是唯一事实索引**：`registry/AUTOMATIONS.yaml` 跨平台描述每条任务的触发/工作目录/意图全文/产出落点/分类（路径用 `<WORKSPACE_ROOT>` 占位符脱敏）。平台是运行时，不是资产。
2. **任何平台变更必须先回写 registry，再同步平台**：新增/修改/删除自动化 → 先改 `registry/AUTOMATIONS.yaml` → 再 `automation_update` / 改 `scheduled_tasks.json` / 改 workflow → 最后 `ops-feed-daily-push` 滚动推送。
3. **漂移即信号**：`xt-scheduler drift` 标红的条目必须修——通常是因为平台侧任务被重建（新 uuid），把 registry 的 `id` 改成平台当前 live uuid 即可。
4. **id 脆弱性**：WorkBuddy 重建任务会换 uuid，registry 的 `id` 字段会过时。drift 命令就是为此存在；不要手工猜 id，用 drift 比对 DB 后修正。
5. **操作类（enable/disable/new/run）走人工/agent 调平台 API**：CLI v1 只做只读聚合 + 漂移纠偏，避免脚本越权改平台状态。WB 类操作由 agent 调 `automation_update` 工具执行。

## 分类口径（四分类）
- 工作：工程/基建/工具/规则/开源矩阵/技能进化/数据同步
- 创作：内容生产/分发/贴图/发布飞轮/素材库/变现
- 生活：个人成长/学习（如 MEM 考研打卡）
- 信源：舆情/arXiv/RSS/竞品 watch

## 与 GitHub 关联
- registry 在 git 仓，所有 agent 可 clone/read。
- `ops-feed-daily-push` 每日刷新 `registry/OUTPUTS-INDEX.yaml`（全局产出索引），`show <slug>` 直接打开最新产出。
- 新任务可直接 `git grep` 历史产出做差异比对（回流查重、素材去重）。

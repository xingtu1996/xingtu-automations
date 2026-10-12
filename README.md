# xingtu-automations · 多 Agent 定时任务 Registry

> **一个工作流的「自动驾驶层」：所有定时任务的工具中立清单 + 跨平台重建指南。**

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) ![Automations](https://img.shields.io/badge/automations-17-blue.svg) ![Platforms](https://img.shields.io/badge/platforms-WorkBuddy%20%7C%20Claude%20Code%20%7C%20cron-orange.svg) ![Tool Neutral](https://img.shields.io/badge/tool--neutral-rebuild--anywhere-purple.svg)

---

## 这是什么

一个人的内容工程体系跑起来后，定时任务会散在多个 agent 工具里（WorkBuddy automation、Claude Code scheduled_tasks、crontab……）——**换个工具、换台机器，任务就「失忆」**。

本仓是所有定时任务的**唯一清单（registry）**：每条任务的触发、工作目录、意图（prompt）、产物落点，全部落成可读文件。平台只是运行时，本仓才是资产。

配套姊妹仓：[xingtu-skills](https://github.com/xingtu1996/xingtu-skills)（任务里调用的技能）、[xingtu-harness](https://github.com/xingtu1996/xingtu-harness)（一键拉全资产的工作台）。

## 当前编目（17 条）

| 平台 | 条数 | 说明 |
|---|---|---|
| WorkBuddy automation | 14 | 内容飞轮主线：舆情→选题→成稿→发布→复盘→分发闭环 |
| Claude Code scheduled_tasks | 3 | 会话归档、元宝抓取、知识付费提醒 |
| crontab | — | 按需挂载，定义同 schema |

完整字段见 [`registry/AUTOMATIONS.yaml`](./registry/AUTOMATIONS.yaml)；字段规范见 [docs/schema.md](./docs/schema.md)；换平台重建见 [docs/MIGRATION.md](./docs/MIGRATION.md)。

## 一条定时任务到底由什么构成

不管平台怎么包装，缺一样就废：

| 要素 | 说明 | 最容易丢的地方 |
|---|---|---|
| **触发** | 什么时候跑 | rrule ↔ cron ↔ launchd 互转时写错星期/时区 |
| **工作目录** | 在哪个根下跑 | 头号事故源：路径指到历史残留目录，对着空壳干活 |
| **意图** | prompt 全文 | 迁移时只搬了名字，prompt 留在原地 |
| **产物落点** | 能验证它真跑过 | 没有落点 = 无法判断跑没跑 |
| **失败留痕** | 能发现它没跑 | 静默失败是常态 |

## 纪律（本仓存在的意义）

1. **平台任何变更**（新建/改期/改 prompt/删除）→ **先回写私有 registry**（`.harness/scheduled/`）→ 再脱敏同步本公开镜像。
2. **完成判定认落盘凭证**：产物 mtime / git log / 退出码，不认模型自述「已跑」。
3. **路径纪律**：所有 cwd 锚定唯一工作区根（镜像里是 `<WORKSPACE_ROOT>` 占位符）。
4. **公开镜像脱敏**：真实路径/内部代号一律占位符化；私有 registry 含全量真值，禁公开。

## 快速开始

```bash
# 看全量清单
cat registry/AUTOMATIONS.yaml

# 在任意平台重建（以 crontab 为例）
# 每条 schedule.cron + cwd + prompt 三件套，缺一不可
```

---

一线 AI 工程化实践者 · FDE 方向 · 公众号「行途」· GitHub/X：`@xingtu1996`

*公开镜像只含占位符路径与聚合口径；私有 registry（含真实路径与完整 prompt）在工作区 `.harness/scheduled/`。*

## 关于作者 · 行途

一线 AI 工程化实践者 · FDE 方向。这些仓库不是写出来的，是每天真用、用完回炉改的。

- 公众号「**行途**」（长文首发，微信搜索关注）
- GitHub / X：`@xingtu1996` ｜ 博客：https://xingtu1996.github.io
- 方法论旗舰仓：[xingtu-ai-engineering](https://github.com/xingtu1996/xingtu-ai-engineering)

## 📄 许可证

MIT License

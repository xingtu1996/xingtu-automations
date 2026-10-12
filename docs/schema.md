# Automation Schema · 任务条目字段规范

> registry 里每条任务的字段定义。新任务入册、平台回写时按本规范对齐。
> 设计原则：**最小够用**——一个平台迁移时需要的信息一项不缺，装饰性字段一项不多。

## 必填字段

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `slug` | string | 稳定标识（kebab-case），跨平台不变，引用它 | `toolbelt-weekly-scan` |
| `name` | string | 人读名（与平台显示名一致，改期时同步） | `云中立工具带每周盘点` |
| `status` | enum | `ACTIVE` / `PAUSED` / `RETIRED` | `ACTIVE` |
| `platform` | enum | 运行时平台：`workbuddy` / `claude-code` / `cron` | `workbuddy` |
| `schedule` | object | 触发定义，见下 | — |
| `cwd` | list | 工作目录（绝对路径；公开镜像用 `<WORKSPACE_ROOT>`） | `["<WORKSPACE_ROOT>"]` |
| `purpose` | string | 一段话讲清「干什么、为什么」，≤100 字 | — |
| `prompt` | string | **意图全文**（多行 YAML 块）。prompt 必须自包含：路径纪律/执行步骤/红线/完成判定四段式 | — |

## schedule 子字段

| 字段 | 说明 |
|---|---|
| `rrule` | RFC 5545（WorkBuddy 平台用）：`FREQ=WEEKLY;BYDAY=MO;BYHOUR=10;BYMINUTE=0` |
| `cron` | 等价 5 段 cron（CC/crontab 用）：`0 10 * * 1` |
| `human` | 人读口径（含时区）：`每周一 10:00（Asia/Shanghai）` |

三个都写——互转时防丢，人也看得懂。

## 选填字段

| 字段 | 说明 |
|---|---|
| `id` | 平台侧 ID（回查/更新用；建后回填） |
| `ring` | 层级：`L1` 数据底座 / `L2` 生产流程 / `L3` 治理维护 |
| `artifacts` | 产物落点列表（完成判定的凭证来源） |
| `note` | 备注（如「完整 spec 在私有 registry」） |

## prompt 四段式（写 prompt 的硬规范）

1. **角色+任务一句话**：你是谁、干什么
2. **路径纪律**：唯一根、Python 路径、私有件位置（禁外传项）
3. **执行步骤**：编号步骤，每步可验证（命令/期望输出）
4. **红线 + 完成判定**：禁什么；「做完了」认什么凭证（mtime/log/退出码）

## 反模式

- ❌ 只登 name 不登 prompt（迁移即废）
- ❌ cron/rrule 只写一个（换平台必丢）
- ❌ cwd 写相对路径（换工具即跑错）
- ❌ prompt 里写「参见某文档」而不内联路径（文档会漂移）

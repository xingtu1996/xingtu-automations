# 定时任务跨 harness 迁移指南

> 配套：[`registry/AUTOMATIONS.yaml`](../registry/AUTOMATIONS.yaml)（任务全量清单，prompt 全文在此）
> 本文**不复述 prompt 正文**，只讲「换一个 agent 工具后，怎么把这些任务原样搬过去」。
> 建立：2026-09-14 ｜ 依据：Claude Code 官方 headless 文档 + Codex CLI 官方 non-interactive 文档（2026-09-13 实查）

---

## 一、先想清楚：一个"定时任务"到底是什么

不管平台怎么包装，一条自动化只由三样东西构成。迁移时**三样都要搬，缺一样就废**：

| 要素 | 说明 | 最容易丢的地方 |
|------|------|----------------|
| **触发** | 什么时候跑 | rrule ↔ cron ↔ launchd 表达式互转时写错星期/时区 |
| **工作目录** | 在哪个根目录下跑 | 🔴 **本工作空间的头号事故源**，见 §四 |
| **意图** | 让它干什么（prompt 全文） | 平台迁移时只搬了名字，prompt 留在原地 |

外加两个非必需但强烈建议的：**产物落点**（能验证它真跑过）与**失败留痕**（能发现它没跑）。

---

## 二、触发层映射表

本工作空间现有 10 条任务的实际排期，等价表达式如下（可直接抄）：

| 任务 | WorkBuddy rrule | crontab | 人读 |
|------|-----------------|---------|------|
| T-WB-01 会话广撒网 | `FREQ=DAILY;BYHOUR=2;BYMINUTE=0` | `0 2 * * *` | 每天 02:00 |
| T-WB-02 舆情扫描 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` | `0 9 * * *` | 每天 09:00 |
| T-WB-03 贴图日更 | `FREQ=DAILY;BYHOUR=10;BYMINUTE=0` | `0 10 * * *` | 每天 10:00 |
| T-WB-04 对话挖掘 | `FREQ=DAILY;BYHOUR=14;BYMINUTE=30` | `30 14 * * *` | 每天 14:30 |
| T-WB-05 发布飞轮 | `FREQ=DAILY;BYHOUR=19;BYMINUTE=0` | `0 19 * * *` | 每天 19:00 |
| T-WB-06 开源周巡检 | `FREQ=WEEKLY;BYDAY=WE;BYHOUR=21;BYMINUTE=0` | `0 21 * * 3` | 每周三 21:00 |
| T-WB-07 素材库刷新 | `FREQ=WEEKLY;BYDAY=SU;BYHOUR=21;BYMINUTE=0` | `0 21 * * 0` | 每周日 21:00 |
| T-WB-08 变现飞轮 | `FREQ=WEEKLY;BYDAY=SU;BYHOUR=22;BYMINUTE=0` | `0 22 * * 0` | 每周日 22:00 |

> 互转注意：**crontab 的星期字段 0 = 周日**（与 `BYDAY=SU` 对应）；macOS 上 crontab 受「完全磁盘访问权限」限制，可能被系统静默拒绝——此时改用 `launchd`。

---

## 三、目标平台怎么落地

### 3.1 macOS launchd（不依赖任何 agent 工具，最稳）

适合「本机常开、要读写本地文件」的任务。`~/Library/LaunchAgents/com.xingtu.<slug>.plist`：

```xml
<key>ProgramArguments</key>
<array>
  <string>/bin/zsh</string>
  <string>-lc</string>
  <string>cd <WORKSPACE_ROOT> && <你的 agent 一次性命令> >> <WORKSPACE_ROOT>/.harness/scheduled/logs/&lt;slug&gt;.log 2>&1</string>
</array>
<key>StartCalendarInterval</key>
<dict><key>Hour</key><integer>19</integer><key>Minute</key><integer>0</integer></dict>
```

> **取 prompt 的通用办法（零依赖）**：`AUTOMATIONS.yaml` 是唯一事实源，各条目的 `prompt: |`
> 段正文即任务全文。迁移时把它复制成一份 UTF-8 文本文件即可（下面示例统一用 `$PROMPT_FILE`）。
> 本机实测**无 `yq`、Python 亦未装 PyYAML**，所以不要指望一行命令自动抽取——
> 这正是不把 prompt 拆成 10 个散文件、而是集中一份 YAML 的原因：**单一事实源，人工复制成本极低，且不会漂移**。

```bash
# 例：取出 T-WB-05（每日发布飞轮）的 prompt
PROMPT_FILE=/tmp/T-WB-05.txt   # ← 从 AUTOMATIONS.yaml 复制该条 prompt 正文到此文件
```

### 3.2 Claude Code（`claude -p` headless）

```bash
cd <WORKSPACE_ROOT> && \
claude -p "$(cat "$PROMPT_FILE")" \
  --allowedTools "Read" "Write" "Bash" \
  --max-turns 20 --max-budget-usd 1.00 \
  --output-format json >> .harness/scheduled/logs/T-WB-05.jsonl 2>&1
```

- 🔴 **不要加 `--bare`**。官方文档写明：`--bare` 会跳过 hooks / skills / plugins / MCP / CLAUDE.md 的自动发现。本工作空间的 prompt **重度依赖这些**——T-WB-03 靠 `browser-skill`/`wechat-tuitu-publish` 拉 bsk 通道、T-WB-08 靠 `find-skills` 做技能匹配。加 `--bare` = 这两条任务当场失效，且**不会报错，只会行为降级**（最危险的一种坏法）。
- `-p` 默认加载与交互会话相同的上下文（含 `CLAUDE.md`、项目 `.mcp.json`），这正是我们要的。
- 官方另提供 **Routines**（云端托管、`/schedule` 创建，最小粒度 **每小时**）。本清单里的 DAILY/WEEKLY 任务适合；但**任务是本地文件密集型的**（读 `素材库/`、写 `outputs/`），Routines 每次从默认分支全新 clone、只能推 `claude/` 前缀分支 ——**与本工作空间的工作方式不匹配，不建议**。

### 3.3 Codex CLI（`codex exec`）

```bash
# 例：取出 T-WB-06（开源周巡检）的 prompt → /tmp/T-WB-06.txt
cd <WORKSPACE_ROOT> && \
codex exec --sandbox workspace-write \
  "$(cat /tmp/T-WB-06.txt)" \
  --json -o .harness/scheduled/logs/T-WB-06.last.md \
  > .harness/scheduled/logs/T-WB-06.jsonl 2>&1
```

- 默认是**只读沙箱**；要写文件必须显式 `--sandbox workspace-write`。`--full-auto` 已废弃，别用。
- `--json` 出 JSONL 事件流（便于事后审计）；`-o/--output-last-message` 把最终自然语言落盘。
- 迁移红线：T-WB-03（贴图日更）依赖**本机已登录的浏览器态**（bsk 接管），Codex 沙箱下需确认浏览器权限与路径可见性，否则应留在本地 launchd。

### 3.4 GitHub Actions

适合**纯仓库内**任务（T-WB-06 开源巡检的隐私复扫部分）。用 `schedule: cron:`（UTC！北京时间 21:00 = UTC 13:00）。涉及本机私有文件（`素材库/`、`~/.claude/`）的任务**不适合**上云。

---

## 四、迁移三红线（本工作空间特有，别照搬通用教程）

### 红线 1 · 路径纪律：绝对路径锚定唯一根

**唯一根 = `<WORKSPACE_ROOT>`。**

不要写成 `~/xingtu`、不要用相对路径、**尤其不要出现 `<HOME>/工作室/xingtu`**——那是 2026-09-05 前后产生的残留副本（独立 inode，非软链），残留区素材库只有 12 卡，唯一根有 1466 卡。

迁移前先验证：

```bash
ls -ldi <WORKSPACE_ROOT> <HOME>/工作室/xingtu   # inode 不同 = 两个独立目录
```

### 红线 2 · 规模告警：让「跑错地方」当场炸出来

任务跑在空壳目录上**不会报错**，只会安静地输出垃圾。所以每条读关键数据的任务都要带规模自检：

```python
# 例：素材库正常 1000+ 卡，少于 500 直接中止
assert len(data["cards"]) >= 500, f"素材库异常：仅 {len(data['cards'])} 卡，疑似跑错工作目录"
```

### 红线 3 · 幂等 + 水位线

本地采集类任务（T-WB-01/04）要用「上次扫描时间」水位线做增量，重复触发不能重复入库。迁移时水位线文件必须一起搬（`.harness/scheduled/<task>/.watermark.json`）。

---

## 五、迁移检查清单

- [ ] 唯一根路径在 prompt 与 cwd 中**全部**为 `<WORKSPACE_ROOT>`
- [ ] rrule → cron 转换后，星期/时区经过实际触发验证（别只看表达式）
- [ ] 依赖的 skills / MCP / 浏览器登录态在新平台可用（CC 不加 `--bare`；Codex 确认沙箱可见性）
- [ ] 关键数据文件有规模告警，异常即中止
- [ ] 产物落点明确，且能用 `ls -la` 验证"确实产出过"
- [ ] 失败有留痕（日志文件 + 非零退出码），不靠人肉发现
- [ ] 破坏性动作（发布/推送/删除）在新平台上仍被显式禁止——**自动化只到「草稿/建议」，发表权留给人**
- [ ] 迁移后平台原任务**显式停用**，避免双跑（双跑 = 重复入库 / 重复出卡）

---

## 六、诚实标注：尚未核实的部分

| 项 | 状态 |
|---|---|
| `DIRECTORY.md` §八 提到的 `scheduled_tasks.json`（CC cron） | ⚠️ **本机不存在该文件**，实测 `find` 无结果。该映射行属**前瞻性声明**，非已落地事实 |
| 本机 `claude` / `codex` / `bsk` CLI | ⚠️ `claude` 实测**不在 PATH**；迁移前需先确认各 CLI 安装与登录态 |
| 云端托管任务 `cloud:1937308` | 排期与产物在云端侧配置，`automation_update` 读不全，**无法本地迁移** |
| 其他 harness 目录（`.agents` / `.kiro` / `.antigravity` / `.zcode`） | 仅确认目录存在；各自的**定时机制未逐一核实**，迁移前需查其官方文档 |

> 🔴 **公开化红线**：本目录的 `AUTOMATIONS.yaml` **含内部项目名与业务代号**，只可留在本地私有
> harness；`github/xingtu-harness` 是**公开仓**（实测目前不含本目录，保持现状）。
> 本文（MIGRATION.md）不含内部名，是这套体系里**唯一可直接开源**的一份。

---

## 关联

- 任务全量清单（含 prompt 全文）：`AUTOMATIONS.yaml`
- 任务总览表与新增流程：`README.md`
- 工作空间跨平台兼容铁律：`HARNESS.md` §四
- 资产登记：`DIRECTORY.md` §八

# 行途技术 · 全局定时任务系统设计方案（SSoT）

> 设计稿 v0.1 · 2026-10-19 · 已拍板：全量执行（对外身份统一「行途技术」+ 提交邮箱 xingtutech@163.com）
> 范围：为 agent 设计一套跨全部 xingtu 仓库的定时任务系统，支持全局查看/操作/新建，产出可纠偏调教，并与 GitHub 关联复用。
> 身份说明：本稿按对外口径「行途技术」撰写（boss 2026-10-19 拍板：行途/XingTu → 行途技术 全量执行；红线表保留「行途技术手记」为禁用旧账号名，二者不冲突）。

---

## 1. 仓库命名评估：xingtu-Scheduled vs xingtu-cron vs xingtu-automations

**结论（明确推荐）：保留/演进 `xingtu-automations`，若要做「Scheduled」语义的规范名，则重命名为 `xingtu-Scheduled`，不推荐 `xingtu-cron`。**

| 候选 | 含义 | 准确性 | 推荐度 | 评价 |
|---|---|---|---|---|
| `xingtu-automations` | 自动化（全集） | ★★★★★ | ✅ 最佳 | 已存在、有历史、有 registry 结构；"automations" 是**超集**，覆盖 cron/定时/触发/事件 |
| `xingtu-Scheduled` | 定时/排程的 | ★★★★☆ | ✅ 次选 | 平台中立、准确表达「定时任务」；比 cron 更贴切；与 `Tasks` 天然成对 |
| `xingtu-cron` | Unix cron | ★★☆☆☆ | ❌ 不推荐 | "cron" 暗含**单机 Unix cron daemon（5 段）**，但实际系统跨 WorkBuddy automation + Claude Code scheduled_tasks + GitHub Actions + LaunchAgent + crontab，**名不副实**；且 "cron"  alone 不表意"任务/系统" |

**执行建议**：
- 现状 `xingtu-automations` 已是最优名且内容齐备 → **首选不新建仓库，直接演进它**。
- 若 boss 坚持用「Scheduled」语义做规范名：GitHub 仓库重命名会**保留历史并自动 301 重定向**旧名，风险低，可从 `xingtu-automations` → `xingtu-Scheduled` 一键改；姐妹仓里的旧链接不受影响（GitHub 重定向）。
- `xingtu-cron` 仅在「内部口语」可用，**不当仓库名**。

---

## 2. 系统架构：全局 agent 可查看/操作/新建所有定时任务

### 2.1 设计原则
- **registry 是唯一事实索引**：`registry/AUTOMATIONS.yaml` 跨平台描述每条任务的触发/工作目录/意图全文/产出落点/分类（工具中立，路径用 `<WORKSPACE_ROOT>` 占位符）。
- **平台是运行时，不是资产**：WB automation / CC scheduled_tasks / GH Actions / LaunchAgent / crontab 各自只是执行器；换平台照 registry 重建。
- **任何 agent 可达**：registry 在 git 仓（所有 agent 可 clone/read），控制面 `xt-scheduler` 作为 skill（xingtu-skills）或 CLI（xingtu-tools）供任意仓库的 agent 调用。

### 2.2 控制面 `xt-scheduler`（skill + CLI 双形态）
```
xt-scheduler list                        # 聚合全部来源，按 分类/平台 过滤
xt-scheduler show <slug>                 # 任务定义 + 最近运行会话 + 最新产出路径
xt-scheduler runs <slug>                 # 拉该任务的历史运行/会话（来源：平台 API / xt_runs.jsonl / vault 产出）
xt-scheduler new --platform <p> ...      # 脚手架：写 registry 条目 + 对应平台文件（WB/CC/GH-Actions）
xt-scheduler enable|disable|run <slug>   # 操作（WB 走 automation_update；CC 改 scheduled_tasks.json；GH-Actions 改 workflow）
xt-scheduler drift                       # registry vs 各平台实时对账，标红不一致（见 §5 纠偏）
```
- **聚合来源**：① WorkBuddy `automation_update`/DB；② 各仓库 `.claude/scheduled_tasks.json`；③ `*/.github/workflows/*.yml`；④ `~/Library/LaunchAgents/*.plist`；⑤ 系统 `crontab -l`。
- **综合查看既有产出**：每条任务在 registry 登记 `artifacts:`（产出路径列表）；`xt-scheduler show` 直接打开最新产出 + 一个全局 `outputs-index`（见 §4）让 agent 一眼看全「今天所有定时任务产出了什么」。

### 2.3 全局可达性
- `xt-scheduler` 入 `xingtu-skills`（通用 skill），所有 xingtu 仓的 agent 经 `.claude/settings.json` 引用即可调用。
- registry 仓作为「定时任务指挥中心」，README 写明：新增/改/删任务 → 先回写 registry → 再同步平台。

---

## 3. 四类定时任务规划（基于 27 仓库，排除已归档）

> 已归档（2026-10-12）：xingtu-cli / xingtu-cloud-neutral / xingtu-design / xingtu-hooks / xingtu-mcps / xingtu-prompts → **不纳入活跃调度**，仅作信源/历史参考。
> 活跃仓库按四类归仓：

### 3.1 🗂 生活（个人成长/管理）
| 仓库 | 现有/规划任务 | 说明 |
|---|---|---|
| xingtu-learn | `mem-exam-daily-reminder`（已存在） | MEM 考研每日打卡，落 xingtu-learn |
| xingtu-learn | 规划：读书/课程笔记同步 | 个人学习资产→vault 素材库 |
| xingtu-book | 规划：出书草稿周更核对 | 出书项目进度看护 |

### 3.2 🔧 工作（工程/基建/工具/规则）
| 仓库 | 现有/规划任务 | 说明 |
|---|---|---|
| xingtu-automations | `ops-feed-daily-push`（已存在） | 每日滚动推送 vault 产出至 GitHub |
| xingtu-harness | `opensource-matrix-weekly`（已存在，落点 xingtu-harness 巡检） | 开源矩阵健康度+隐私复扫 |
| xingtu-skills / dsh-xingtu-skills | `skill-library-weekly-checkup` + `skill-evolution-miner`（已存在） | 技能库体检/进化 |
| xingtu-tools / xingtu-harness | 规划：harness 配置自愈 | 检测 config.yaml 漂移 |
| xingtu-sdd | 规划：spec 引擎每日构建校验 | SDD 引擎健康 |
| xingtu-rules | 规划：规则库 CI 体检 | 规则工程化看护 |
| tokenhub-bench-restore | 规划：LLM 榜单可复现评测定时跑 | 评测基建 |

### 3.3 📣 创作（内容生产/分发）
| 仓库 | 现有/规划任务 | 说明 |
|---|---|---|
| xingtu-articles | `github-article-reflux`（已存在） | GitHub 文章回流公众号 |
| xingtu-vault / xingtu-articles | `daily-trend-scan` / `mp-data-review-daily` / `daily-publish-flywheel` / `monetization-flywheel-weekly` / `free-compute-daily` / `toolbelt-weekly-scan` / `wechat-tuitu-daily` / `ai-collab-miner-daily` / `session-broadcast-collect` / `materials-library-weekly-refresh`（已存在） | 自媒体内容飞轮全链路 |
| xingtu-video | 规划：视频资产周更核对 | 视频内容看护 |
| xingtu-site / xingtu-github-io | 规划：名片/作品集构建校验 | 展示层 |

### 3.4 📡 信源（采集/情报/参考）
| 仓库 | 现有/规划任务 | 说明 |
|---|---|---|
| xingtu-vault | `daily-trend-scan`（舆情，已存在） | 外部热点→选题 |
| xingtu-vault | 规划：arXiv/技术博客/RSS 采集→素材库 | 技术信源常态化入库 |
| xingtu-vault | 规划：标杆竞品 repo watch（star/release 监控） | 竞品情报 |
| xingtu-articles | `github-article-reflux` 亦为信源复用 | 自有文章二次分发 |

**分类汇总（活跃）**：生活 2~3 · 工作 6~8 · 创作 11+ · 信源 3~4。与现有 registry 的 工程化/自媒体 二分法合并为四分类，registry 加 `category:` 字段（工作/自媒体→创作，工程化→工作，新增生活/信源）。

---

## 4. 产出物规划 + 纠偏调教 + GitHub 关联

### 4.1 产出物落点纪律（沿用既有铁律）
- 所有产出**只落 git 仓**（vault / 各仓库），**禁落主区 `outputs/`**（非 git、云端不可见）。
- 每条任务在 registry 登记 `artifacts:`（产出路径列表），作为「完成判定」凭证源。

### 4.2 全局产出索引（综合查看）
- `registry/OUTPUTS-INDEX.yaml`（或 vault `定时任务产出/_索引.md`）：每日由 `ops-feed-daily-push` 增量刷新，记录「任务 → 当日产出文件 → mtime → 一句话结论」。
- agent 调 `xt-scheduler show <slug>` 或读索引即可**综合查看既有产出**，无需逐个仓库翻。

### 4.3 纠偏与调教机制（核心增量）
1. **漂移检测（drift）**：`xt-scheduler drift` 比对 registry 与各平台实时状态，不一致标红。
   - 实测已有 4 条 legacy id 漂移（session-broadcast-collect / ai-collab-miner-daily / daily-publish-flywheel / materials-library-weekly-refresh 的 `id` 指向已被软删的旧任务）→ 本期修复。
2. **运行期护栏（沿用 prompt 四段式）**：429 降级（禁反复重试→`_待推队列.md`）、规模告警（素材卡 <1500 即中止）、完成判定认 mtime/退出码不认自述。
3. **产出反哺调教（feed-back tuning）**：每篇产出（舆情日报/数据复盘/技能进化）含「假设验证/判断」段；新增 `task-tuner` 任务读取近 N 天产出，提炼「prompt 该调哪里」建议，回写对应任务 prompt（经 registry + 平台），形成**纠偏闭环**。
4. **GitHub 关联复用/调整**：产出已 commit 进 git 仓 → 新任务可直接 `git grep`/读取历史产出做差异比对（如回流任务查重、素材库去重）；「调整已有产出」= registry 记录 artifact 历史版本，新 run 自动 diff 上一版。

---

## 5. harness 配置优化（参考 ctf-gitlab 范式，纯通用）

> 参考源：`/Users/lijiacheng/projects/ctf-gitlab/.claude/` 的 scheduled_tasks.json / settings.json / config.yaml / user-config.yaml。
> **仅借鉴结构，内容完全通用**——不写入任何雇主项目名/密码/内网地址/真名（SAF-010）。

在 `xingtu-harness/.claude/`（或各仓 `.claude/`）落地通用骨架：

| 文件 | 作用 | 通用要点 |
|---|---|---|
| `scheduled_tasks.json` | CC 定时任务清单 | `{"tasks":[...]}`；每条含 `schedule`(cron/rrule)、`cwd`、`prompt` 摘要、指向 registry slug |
| `settings.json` | CC 权限/MCP/hooks | `permissions.allow` 收敛到必要命令；`hooks` 接 pre-tool 护栏 |
| `config.yaml` | 中心 harness 配置 | `project` / `tech_stack`(通用) / `environments`(占位) / `branch` / `quality_gates` / `script_runtime` |
| `user-config.yaml` | 个人环境 | `git.author_name/email`（按 §7 决策）、本地路径占位 |

**script_runtime 约定（沿用参考源优点，修正其"禁装 pyyaml"为"基建优先"）**：简单 YAML 用 awk，复杂用 python（已装 PyYAML 于受管 venv），不引入非必要系统依赖。

---

## 6. 提交纪律
- 所有 xingtu 仓提交身份统一（见 §7 决策）。
- 平台任何定时任务变更 → 先回写 registry（私有全量 + 本公开镜像脱敏）→ 再同步平台 → 最后 `ops-feed-daily-push` 滚动推送。

---

## 7. ✅ 身份决策（2026-10-19 boss 拍板：全量执行）

boss 要求：① 对外身份「行途 / XingTu」统一为「行途技术」；② 所有 xingtu 仓提交邮箱统一 `xingtutech@163.com`。**已拍板全量执行**，本稿与设计仓已落地。

**红线冲突处理（关键）**：本仓 HEAD 提交 `25c1922` 曾把对外口径统一为「行途 XingTu」并把「行途技术手记」列入禁词表。经核查后确认不冲突：
- 禁词表禁的是「行途技术手记」（旧公众号账号名），**不是**「行途技术」——扫描逻辑为"禁用词是否出现在文本"，「行途技术手记」并非「行途技术」的子串，故改名后**不会被红线命中**，禁词表无需改（旧账号名仍禁）。
- 配套动作：更新 `AGENTS.md` 铁律 10 对外口径 →「行途技术」；工作区 ~10 个 skill 的隔离守卫「含「行途技术」才执行」同步改为「含「行途技术」才执行」（防个人项目 skill 在公司仓误跑）。

| 项 | 决策 | 说明 |
|---|---|---|
| 对外品牌 | 「行途技术」 | 治跨仓身份漂移；旧「行途技术手记」仍禁，二者不冲突 |
| 提交邮箱 | `xingtutech@163.com` | 真实邮箱，公开 commit 暴露该邮箱（已知代价：失去 GitHub noreply 匿名保护）；仅用于 xingtu 工程仓 |
| 内部项目标识 | 保留「行途」（工作区目录 `/Users/lijiacheng/xingtu`、仓库名 `xingtu-*`） | 目录/仓库名不动（改名会崩 git 远端与脚本）；scope 守卫串已同步改为「含「行途技术」才执行」 |

> 已知固有限制：已发布公众号文章署名不可回溯修改。

---

## 8. 实施路线（拍板后）
1. 仓库命名定案（§1）→ 必要时 `gh repo rename`。
2. registry 加 `category:` + 修复 4 条 legacy id 漂移 + 补 `技能进化周分析` 条目 + 加 `OUTPUTS-INDEX.yaml`。
3. 写 `xt-scheduler`（skill + CLI）入 xingtu-skills / xingtu-tools。
4. xingtu-harness 落通用四件套配置。
5. 批量身份重命名（§7 确认后）+ 提交邮箱统一。
6. `ops-feed-daily-push` 滚动推送 + 写 CHANGELOG。

# Changelog

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)，格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.2.0] - 2026-09-18

**BREAKING：默认写作模式由「纯英文」反转为「中英混合」。** 中文成为叙事语言，英文只嵌「待检测的目标词 + 已会词（范围词库）+ 专名白名单」——纯英文读不下去时的务实折中，也是一条坡道：已会词名单越长，英文比例自然爬升，坡顶即纯英文。

### 新增

- **中英混合审计模式（`mode: mixed`，默认）**：中文叙事 + 英文白名单制。英文只允许三类——目标词 / 范围词库（已会词）/ 明确专名；**内置功能词不再豁免**（the/and/is 出现即判超纲）。长度改为混合字数（汉字数 + 英文词数），默认窗口 300–800（`minLength`/`maxLength` 可调）。
- **目标词加粗硬检查**：混合模式下每个目标词的每次出现都必须被 `**…**` 包裹（加粗是「待检测词 vs 已会词」的唯一视觉锚点，此前只是技能软规则）。
- **英文占比观测值**：审计返回 `english_ratio` / `cjk_chars` / `english_words` / `length`——只观测不设闸，用于观察英文比例随词库成长爬坡。
- **纯英文模式保留（`mode: english`，坡顶/兼容）**：旧规则全量保留（功能词豁免、纯英文、180–400 词窗），审计与提交工具传 `mode: english` 即可切换。
- 写作工艺段新增「嵌词四纪律」：语境可猜 / 两次两语境 / 密度克制（单句英文词 ≤2）/ 不注译。

### 变更

- **范围词库角色重定义**：混合模式下即「已会词白名单」——故事里允许出现的英文词集合（旧角色仅在 english 模式生效）。`vocab_distill` 输出随模式变化：mixed 不含功能词。
- **文本指纹升级**：由「仅英文 token」改为「英文 token + 汉字」共同哈希；mark 去重双检（新旧指纹任一命中即跳过），历史标记记录仍能拦截旧文本重标。
- **`commit_story` 钩子兜底切句**加入中文标点（`。！？`），混合正文的 `next_hook` 自动提取不再失效。
- 技能与文档全面对齐：`写故事`、`engstory-domain`、`engstory-guide` 参数地图（minWords/maxWords → minLength/maxLength、新增「英文多/少」行）、`doctor` 的白名单措辞、两份 README。

## [0.1.5] - 2026-09-18

### 新增

- **引导模式（`skills/engstory-guide/`）**：按需加载的引导技能。用户问「怎么开始 / 缺什么 / 怎么调整效果」时触发——先用 doctor 体检真实环境，再用小白能懂的自然语言解释每个空位该放什么、每个参数管什么、改完会看到什么变化。内置参数地图（词数 / 字数 / 风格 / 剧情方向 / 专名 / 文件位置），覆盖全部可调旋钮。
- **`doctor.py`（第 15 个脚本，纯标准库，只读）**：环境体检——Python 版本 / FSRS 依赖 / 学习词库 / 范围词库 / 可选状态文件逐项检查，每项带小白说明与「补上方法」（指向 `examples/` 样品）；路径三路解析（显式参数 > 环境变量 > 默认）并标注来源；有必修项缺失时退出码 1。
- **`engstory_doctor`（第 10 个工具）**：doctor.py 的工具层封装，缺项时退出码 1 的 stdout 照常解析返回。
- **字数旋钮打通工具层**：`engstory_audit_story` / `engstory_commit_story` 新增可选 `minWords` / `maxWords` 参数，透传脚本层已有的 `--min-words` / `--max-words`（此前该旋钮在脚本层存在但工具层够不着）。
- `engstory-domain` 技能新增 engstory-guide 指针（版本 1.3.0 → 1.4.0）。

### 修复

- **字数窗文档与审计不一致**：`写故事` 技能与两份 README 写「300–500 词」，但审计脚本默认硬窗口是 180–400——按文档写到 401+ 词必被审计拒。统一改为「300–400 词」（落在硬窗口内），并标注审计硬窗口。

## [0.1.4] - 2026-09-18

### 新增

- **写作工艺系统提示段**：`engstory-tools.mjs` 声明 `inject: ['tools', 'systemPrompt']`，通过 `ctx.systemPrompt.section()` 注册 `engstory:craft` 段（order 50，persona 之后、工具指导之前），写作工艺始终在场，不再依赖技能按需加载。
- 工艺文本独立为 `plugins/craft.md`：起草前六问自查、起草三纪律（别重复自己 / 目标词按遗忘分排戏 / 结构是骨架不是句式）、起草后七维自评与去腔诊断（证据+影响+修法，改写至多一次）。读不到该文件时挂载直接失败（fail loud）。
- `engstory_commit_story` 描述新增提交前须完成工艺自评改写的提示。
- 鸣谢：写作工艺灵感来自 [InkOS](https://github.com/Narcooo/inkos)（仅借鉴思路，文本与代码均为原创）。

### 修复

- **Python 解释器平台感知**：`execFile` 写死 `python` 改为 Windows 用 `python`、其他平台用 `python3`——服务器 `/usr/local/bin/python` 是 py2.7，写死会让全部脚本失败（此前只在服务器副本修过，本次收入 repo，消灭 repo↔服务器分歧）。

### 变更

- `写故事` 技能第 4 步增加指针：写作与自评纪律以系统提示写作工艺段为准。

## [0.1.3] - 2026-08-22

### 新增

- **分层剧情记忆**：
  - 新增 `chapter-ledger.jsonl`（账本 `ledger.py`）：每章结构化保存事实、人物变化、关系变化、线索增删与后果，用于"已发生什么"。
  - 新增 `plot-outline.json`（总纲 `outline.py`）：卷/故事弧级长期方向（核心主线 / 终点 / 卷 / 弧 / 永久事实 / 禁止项），用于长篇记忆。
  - 新增**冲突检测**：`ledger` 用"主体内容词重叠 + 否定极性相反"启发式，能标记「哥哥确实来过旧警局」vs「哥哥从未进过警局」这类矛盾（提示级，不自动拦截）。
- **可提炼风格**：
  - 新增 `style-profile.json`（`style.py`）：风格配置带维度 / must_do / avoid / 置信度。
  - 新增 `engstory_extract_style`（从参考片段 + 读者感受生成**候选**风格，不落盘）与 `engstory_confirm_style`（用户确认后才写入）。风格不会自动覆盖。
- **按需上下文组装**：
  - 新增 `context.py` + `engstory_build_context`：把风格 + 卷/弧总纲 + 事实账本 + 当前状态 + 目标词组装成一个**有界的写作上下文包**。
- **连载状态增强（storyline.py）**：
  - 新增风格 / 角色 / 关系 / 线索 / 本章目标 / 上章后果等字段。
  - 支持 `--style-profile`、`--characters`、`--open-threads`、`--relationship-state`、`--chapter-goal`、`--consequence`、`--new-threads`、`--resolved-threads` 等参数。
- **工具从 6 个扩展到 9 个**：新增 `engstory_build_context` / `engstory_extract_style` / `engstory_confirm_style`；`engstory_commit_story` 新增 `obstacle`、`choice`、`story_arc`、`scene_location`、`facts_added`、`facts_confirmed`、`character_changes`、`relationship_changes` 等可选字段，可同步写入账本。

### 修复

- **故事连载 Chapter 1 源起丢失**：滚动 `recap` 超过 5 章时永久保留 Chapter 1（初始因果）+ 最近 4 章，长篇不丢源头。
- **冷启动主线写死英文**：无激活连载时直接 `advance`，自动以本章摘要作为主线，不再固定为 `A continuous adventure.`。
- **中文 JSON 乱码**：为 `runPython` 增加 `PYTHONIOENCODING=utf-8`，修复被管道捕获 stdout 时 Python 用 GBK 编码导致中文摘要/线索/角色被 Node 误解码的问题。
- **`commit_story` 可复用兜底**：`summary` / `next_hook` 缺省时自动从正文末尾提取。

### 变更

- **写作规范升级为章节戏剧结构**：`写故事/SKILL.md` 要求每章完成「立即接场 → 本章目标 → 阻力 → 选择 → 后果 → 具体钩子」6 步，并加入负面约束（禁止重复天气 / 随机加人 / 空泛结尾 / 梦境解释等）。
- **领域规则补充**：`engstory-domain/SKILL.md` 明确"词汇审计 ≠ 文学审计"，提交前须生成结构化字段（summary / next_hook / chapter_goal / consequence / new_threads / resolved_threads）。

### 数据文件

- 词库、范围库、故事、状态、连载、风格、总纲、账本都是用户的持久学习数据，位于 preset 之外。
- 默认与词库同目录：`state.json`、`storyline.json`、`style-profile.json`、`plot-outline.json`、`chapter-ledger.jsonl`、`stories/`。

## [0.1.2] - 2026-08-16

### 修复

- **修复 FSRS `due` 参数未发挥作用的问题**：此前选词排序只看遗忘分（retrievability），完全忽略 Anki 的 `due` 到期时间，导致反馈「不会」的词因遗忘分≈0 反而沉底、迟迟不出现。现改为 Anki 同款「到期驱动」排序，`due` 正确生效——「不会」的词下一轮（无论隔多久调用）必现、排在最前。

### 变更

- **选词升级为到期驱动四队列**：学习中/重学中的词（反馈过「不会」的）→ 已逾期的复习词 → 没反馈过的新词 → 未到期的复习词
- **反馈输出不再显示「0.0 天后」**：改为自然语言（即将到期 / 约 X 分钟后 / 约 X 小时后 / 明天 / N 天后）
- **选词行新增「到期」列**：新词 / 已逾期 / 即将到期 / 约 X 分钟后 / 明天 / N 天后，一眼看出每个词该不该练

## [0.1.1] - 2026-08-16

首个公开版本。

### 新增

- **6 个确定性工具**：选目标词 / 准备故事词汇包 / 审计故事 / 提交故事 / 应用反馈 / 写入新词（DSH agent preset）
- **FSRS 间隔重复调度**：记忆调度参照 Anki 的开源 FSRS 算法（vendored py-fsrs 6.3.1），每个词独立维护难度 / 稳定性 / 下次到期
- **遗忘分实时排序选词**：新卡默认 30 分，反馈过「不会」的词随时间爬升自动插队回炉，刚复习的词沉底休息
- **受限词汇故事写作**：目标词强制加粗并豁免范围约束，普通词限定在范围词库 + 内置功能词 + 明确专名内
- **严格审计**：目标词全中 / 普通词范围 / 字数 180–400 / 纯英文，审计通过才提交
- **批次状态机**：`TARGETS_SELECTED → WAITING_FEEDBACK → WAITING_WORD_CONFIRMATION → IDLE`，无用户反馈不更新记忆、无用户确认不写新词
- **词形归并**：`sought → seek`、`stood → stand`；多义词按 `英文|释义` 独立词条、独立计数
- **文本指纹去重**：同一篇文本重复标记自动跳过，防止词频虚高
- **双用法**：DSH agent preset（对话式完整闭环）+ 独立 Python CLI（纯标准库，Python ≥ 3.10）
- **示例数据**：`examples/vocab.sample.json`、`examples/range.sample.json`

### 许可

- 本仓库：MIT
- vendored：py-fsrs（MIT）、typing-extensions（PSF-2.0 / Apache-2.0）

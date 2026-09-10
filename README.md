<div align="center">

# 🪐 Guanyuan BI Toolkit

**让看板好看，让数字有出处。**

用 AI 辅助开发，在观远 BI 中展示与管理数据。

`AI Skills` · `HTML BI` · `指标血缘` · `Python 标准库` · `MIT`

[适合谁](#-适合谁) · [应用场景](#-skill-应用场景) · [安装到 AI 工具](#-在-codex--claude-code-中使用) · [制作自己的看板](#-用-skill-制作你自己的看板) · [梳理已有看板](#-用-skill-梳理已有看板)

</div>

---

## 👋 这是什么？

这是一套面向观远 BI 的 AI Skills 与配套工具，帮助你把页面想法变成动态看板，也能把已有看板整理成可读的指标与来源说明。

你可能遇到过这些问题：

- AI 写的页面很好看，接进观远后却不知道数据该怎么喂。
- 一个看板几十张卡片，想弄清指标公式和来源，要逐个打开。
- 字段改了，数据也刷新了，页面为什么还不对？

这个仓库提供 HTML 看板开发、CLI 平台操作和指标血缘三套可组合的技能。

| 你想做什么 | 从这里开始 | 你会得到什么 |
| :--- | :--- | :--- |
| 做一个动态 HTML 看板 | **HTML BI Starter** | 预览页面、CSS / JS、数据契约和接入说明 |
| 弄清已有看板的指标来源 | **Metric Lineage** | 指标字典、筛选器清单、数据集映射和缺口报告 |
| 自动接入与发布看板 | **Guanyuan CLI** | 官方工具安装检查、数据集配置、组件绑定、发布与回读验证 |
| 让 AI 帮你完成这些工作 | **三套 Skills** | 可独立使用，也可由 HTML Skill 串起完整交付流程 |

## 🎯 适合谁？

- **已经会用 AI 的数据分析师、BI 开发者**：能用 AI 写 SQL、生成页面，希望进一步接入观远数据集。
- **需要在观远内交付报表的业务与数据团队**：希望提升页面表现力，同时沿用组织现有的数据访问与看板权限管理。
- **接手已有看板的维护者**：需要快速弄清指标公式、筛选器联动和数据集来源。

你不需要从头手写整套前端，但需要能说明业务指标，并具备目标观远环境的数据集或看板操作权限。

## 💡 Skill 应用场景

### 场景一：会用 AI 做页面，也需要通过观远保障数据访问安全

**你已经有 AI 使用基础，希望用自然语言设计报表，但业务数据的查询与展示需要留在组织管理的观远 BI 及其数据环境中。**

这时可以让 AI 根据页面需求、字段说明和模拟数据，辅助设计结果集、生成 HTML/CSS/JS；再把代码接入观远数据集，供团队在已有权限体系内访问。

```mermaid
flowchart LR
    A[页面需求 · 字段说明 · 模拟数据] --> B[AI + HTML BI Skill]
    B --> C[页面代码与数据契约]
    C --> D[观远 BI 看板]
    E[组织管理的数据源] --> F[观远数据集]
    F --> D
    D --> G[按组织配置的权限访问]
```

使用 **[`guanyuan-html-bi-generic`](skills/guanyuan-html-bi-generic/SKILL.md)**，把 AI 辅助开发衔接到观远的展示流程。数据访问范围仍以组织实际配置为准，Skill 负责开发方法与接入适配。

### 场景二：AI 原型已经做好，需要变成持续更新的经营看板

你已经有页面截图或 HTML 原型，希望加入 KPI、趋势、漏斗、排名和范围切换，并随数据集刷新更新。

使用 **HTML BI Skill** 拆解页面模块、明确结果集粒度和字段、固定数据集映射，再生成观远可用的 CSS / JavaScript 与验数说明。

### 场景三：接手一个看板，先搞清楚“这个数怎么算的”

看板里有很多卡片、计算字段和筛选器，逐个打开梳理费时，也容易漏掉关联关系。

使用 **[`guanyuan-metric-lineage`](skills/guanyuan-metric-lineage/SKILL.md)** 在获准环境中解析本地 HAR，生成指标字典、筛选器清单、数据集来源和补采建议，辅助交接、排查与后续改造。运行脚本可直接使用，无需将 HAR 提交给外部 AI；AI 是否读取材料应按组织规则决定。

## ☕ 示例：星际咖啡店

我们用一家不存在的咖啡店演示整个流程：月球站和火星站卖咖啡，老板只想知道订单、销售额和客单价。

![星际咖啡店合成数据演示](docs/assets/dashboard-preview.png)

页面支持门店切换、每日趋势、空数据和错误状态。不依赖在线字体、图表 CDN 或分析服务。

## 🤖 在 Codex / Claude Code 中使用

先选工具安装 Skill，再打开**你自己的看板项目目录**发起任务。这里的 Claude 指具备本地文件与脚本操作能力的 **Claude Code**。

### 1. 安装 Skill，只需做一次

<details open>
<summary><strong>我使用 Codex</strong></summary>

在 Codex 中调用 Skill Installer，发送下面这段话：

```text
请使用 $skill-installer，从这个仓库安装三套 Skill：
https://github.com/hhaoyy/guanyuan-bi-toolkit

仓库内路径：
- skills/guanyuan-html-bi-generic
- skills/guanyuan-metric-lineage
- skills/guanyuan-cli

保留各 Skill 的完整目录、参考文档和脚本。
若存在同名 Skill，先说明差异，不要直接覆盖。
安装后告诉我如何调用。
```

安装完成后，在 Codex 的技能选择器中选择对应 Skill。CLI / IDE 扩展中可以输入 `$guanyuan-html-bi-generic` 、`$guanyuan-metric-lineage` 或 `$guanyuan-cli`；未显示时重启 Codex 再检查。安装器与调用方式见 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills)。

</details>

<details>
<summary><strong>我使用 Claude Code</strong></summary>

在 Claude Code 中发送：

```text
请从 https://github.com/hhaoyy/guanyuan-bi-toolkit 下载以下 Skill：
- skills/guanyuan-html-bi-generic
- skills/guanyuan-metric-lineage
- skills/guanyuan-cli

将这三个完整目录分别安装到：
~/.claude/skills/guanyuan-html-bi-generic/
~/.claude/skills/guanyuan-metric-lineage/
~/.claude/skills/guanyuan-cli/

保留 SKILL.md、references 和 scripts 等全部子目录。
若目标已存在，先说明差异，不要直接覆盖。
完成后检查文件，并告诉我如何调用。
```

之后在 Claude Code 输入 `/guanyuan-html-bi-generic`、`/guanyuan-metric-lineage` 或 `/guanyuan-cli`。若命令未出现，重新启动当前会话。个人技能目录及命令方式见 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

</details>

<details>
<summary>手动安装 / 只在当前项目使用</summary>

点击本仓库 **Code → Download ZIP** 并解压，将 `skills/` 下需要使用的**完整 Skill 文件夹**复制到下表的目标目录。也可以用 Git 下载：

```bash
git clone https://github.com/hhaoyy/guanyuan-bi-toolkit.git
```

| 工具 | 仅当前项目 | 所有个人项目 |
| --- | --- | --- |
| Codex | 项目目录下 `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | 项目目录下 `.claude/skills/` | `~/.claude/skills/` |

例如 Claude Code 项目安装后的入口是 `.claude/skills/guanyuan-metric-lineage/SKILL.md`，旁边应保留 `scripts/`。目录规则分别参考 [Codex](https://learn.chatgpt.com/docs/build-skills) 与 [Claude Code](https://code.claude.com/docs/en/skills) 官方文档。

只想先试一次，也可以让 AI 读取下载目录内的 `SKILL.md` 并按其执行，不必先安装到全局目录。

</details>

### 2. 选择你要完成的工作

| 你的任务 | Codex 调用 | Claude Code 调用 |
| --- | --- | --- |
| 新建 / 改造 HTML 看板 | 选择 `guanyuan-html-bi-generic`；CLI / IDE 可用 `$guanyuan-html-bi-generic` | `/guanyuan-html-bi-generic` |
| 安装 CLI / 操作数据集与看板 | 选择 `guanyuan-cli`；CLI / IDE 可用 `$guanyuan-cli` | `/guanyuan-cli` |
| 梳理指标与来源 | 选择 `guanyuan-metric-lineage`；CLI / IDE 可用 `$guanyuan-metric-lineage` | `/guanyuan-metric-lineage` |

调用 Skill 后接着描述任务。下面的需求模板和后续对话适用于两种工具。

## 📊 用 Skill 制作你自己的看板

### 第一步：把需求交给 AI

在 Codex 或 Claude Code 中打开一个用于本次看板的工作目录，并选择 **HTML BI Skill**。准备以下信息；还不清楚的部分可以直接标注“待确认”。

| 你提供什么 | 可以怎么描述 |
| --- | --- |
| 使用者与业务问题 | 运营每天看哪些门店增长、哪些渠道需要关注 |
| 页面目标 | KPI、趋势、排名；或提供页面草图 / HTML 原型 |
| 指标定义 | 订单如何去重、金额单位、统计时间和分母 |
| 数据准备程度 | 已有结果集字段说明，或需要 AI 先设计结果集 |
| 筛选与刷新 | 日期、门店、渠道；每天更新或按需刷新 |

可以直接复制这段需求，替换成自己的内容：

```text
请使用 guanyuan-html-bi-generic 帮我制作一页观远 HTML 经营看板。

使用者：区域运营负责人。
需要回答：整体表现如何，哪些门店值得关注，最近趋势有什么变化。
页面模块：订单数、销售额、客单价、每日趋势、门店排名。
筛选：日期范围和门店。
现有材料：我会提供字段说明、指标定义和页面参考。
更新方式：每天刷新观远数据集。

请先拆解页面模块，列出缺少的信息，整理结果集契约。
没有明确的业务口径请标为待确认。
先使用模拟数据制作预览，业务数据通过观远数据集接入。
项目产物保存到当前工作目录。
```

**这一轮你应该拿到：** 页面模块清单、指标口径草案、结果集设计，以及需要你回答的关键问题。

### 第二步：确认口径，让 AI 生成交付文件

把上一轮的问题补充清楚后，继续说：

```text
按我们确认的页面结构和指标口径继续实现。
请交付：
1. 可在本地打开的 HTML 预览；
2. 观远自定义图表使用的 CSS 和 JavaScript；
3. 每个数据集的字段、粒度、单位和绑定顺序；
4. 需要我在观远完成的操作与验数步骤。

页面需要处理空数据、缺失字段和范围切换。
请先展示预览，便于我调整布局。
```

**这一轮你应该拿到：** 可以审阅的页面和接入文件。你可以继续描述修改，例如“把排名放到趋势右侧”“金额统一显示到万元”“移动端先展示 KPI”。

### 第三步：让 AI 接入并发布到观远

需要自动发布时，继续对 HTML Skill 说：

```text
请把当前 HTML 看板接入我的观远环境并完成发布。
使用 guanyuan-cli 检查并安装缺少的官方组件，复用适合的已有认证。
根据确认的数据契约创建或复用数据集，绑定自定义图表，发布后检查真实数据和页面交互。
实例、目标目录和数据源使用我提供的信息或本地项目配置；无法确定的选项再问我。
保留源工程和资源映射，以便后续修改同一个看板。
所有账户信息、业务数据和发布证据只保存在我的私有项目中。
```

HTML Skill 负责页面和数据契约，CLI Skill 负责平台操作。无需手工在两个技能之间搬运上下文。首次安装仍需符合官方系统要求；登录和发布需要目标环境的相应权限。

**流程：** 页面构想 → HTML/CSS/JS → 数据集准备 → SDK 组件绑定 → 发布 → 在线验收 → 同 ID 更新。

没有平台访问权限或只想先看效果时，仍可交付本地预览和接入文件，按 [HTML BI 接入指南](docs/html-bi.md) 手工接入。安装技能本身不会连接账户或更改线上资源。

通用技能不预设组织目录、地区或数据源。可将偏好保存在私有项目的 `local/guanyuan.json`；字段及优先级见 [配置约定](skills/guanyuan-cli/references/configuration.md)。

**验证边界：** 仓库测试使用合成输入，验证本地适配器和工具检查脚本。实际环境的首次 HTML 发布及同 ID 更新，需要在用户环境验收；不能把本地测试通过解释成所有观远版本都已验证。

### 第四步：带着具体问题继续迭代

例如接入后空白，可以继续向同一个任务描述：

```text
本地预览正常，接入观远后页面空白。
请基于当前项目的 CSS、JavaScript 和结果集契约排查。
先检查 renderChart 注册、container、数据集顺序和列式数据适配。
告诉我需要提供哪些错误信息或结构说明，再修改对应文件。
```

新增指标时，也可以说：“增加一个退款率卡片，先说明需要补充什么字段、是否要更新数据集结构，再修改页面。”

## 🔎 用 Skill 梳理已有看板

### 第一步：准备看板采集文件

在获准环境中采集目标看板的 HAR，保留响应正文；必要时补采卡片或数据集编辑页。详见 [HAR 采集指南](docs/lineage.md)。解析脚本需要 Python 3.9+，只使用标准库。

这条流程应在组织允许 AI 读取相应材料的环境中使用；若只允许本地脚本处理，可直接按指南运行命令。

### 第二步：调用血缘 Skill，说明范围

选择 **Metric Lineage Skill**，发送：

```text
请使用 guanyuan-metric-lineage 梳理我的观远看板。

输入文件：当前项目 local/ 中我指定的 HAR。
文件关系：同一个看板的运行态和编辑态采集。
目标：完成看板交接，弄清每个指标的公式和来源。

请运行解析脚本，输出到 output/lineage/。
给我卡片与指标清单、筛选器联动、数据集及源表/SQL 映射。
区分已经确认的内容、缺少的配置和需要继续追踪的上游逻辑。
如果采集不完整，明确告诉我应该打开哪个编辑页面补采。
```

把文件路径和文件关系改成自己的情况；多个不同看板应分别解析。

### 第三步：阅读结果，继续追问

AI 应返回报告位置、关键发现和缺口说明。先看指标血缘与覆盖报告，再决定补采或追踪上游代码。

可以继续问：“哪些指标只有聚合、还缺业务定义？”“这个筛选器影响哪些卡片？”“哪些数据集缺少来源配置？”

**你最终得到：** 一套用于交接、排查和改造的指标资料，以及明确的后续动作。

<details>
<summary>可选：先浏览仓库自带示例</summary>

下载仓库后，双击 `examples/html-bi/index.html` 可以体验截图中的页面。血缘演示命令见 [使用指南](docs/lineage.md)。示例用于理解效果和产物结构，可以直接跳过，开始自己的项目。

</details>

## 📦 仓库地图

```text
guanyuan-bi-toolkit/
├── examples/html-bi/     # 可直接打开的合成看板
├── skills/               # HTML BI、CLI 与指标血缘三套 Skill
├── scripts/              # 示例生成与辅助工具
├── tests/                # 解析与数据适配测试
└── docs/                 # 接入、采集、数据契约
```

## 📚 继续阅读

- [CLI 安装与使用](docs/cli.md)：官方依赖、本地配置、自动发布与更新。
- [HTML BI 接入指南](docs/html-bi.md)：数据契约、平台适配与常见问题。
- [指标血缘使用指南](docs/lineage.md)：HAR 采集、结果解读与解析范围。

## 🌱 一起改进

欢迎分享使用体验、兼容性问题和通用看板模板。

代码与文档采用 [MIT License](LICENSE)。独立社区项目，与观远官方无隶属或背书关系。

如果它帮你少点开了几张卡片、少追问了一次“这个数哪来的”，欢迎留一颗 ⭐。

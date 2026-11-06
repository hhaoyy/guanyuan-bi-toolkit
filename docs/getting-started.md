# 安装与使用详解

[返回首页](../README.md) · [版本更新](updating.md)

## 固定版本安装（推荐）

下载 [v0.1.0-beta.1](https://github.com/hhaoyy/guanyuan-bi-toolkit/releases/tag/v0.1.0-beta.1) 的命名安装包，按 [INSTALL.md](../INSTALL.md) 安装、自检。此方式固定四套 Skill 的版本，适合试用与反馈。

下文 GitHub 路径安装适合需要主分支最新开发内容的人；它不等同于固定发布版。

## 从 GitHub 路径安装与调用

推荐安装完整四套 Skill，然后使用统一入口 **`guanyuan-bi`**。它按任务调用页面开发、CLI 和血缘技能，你无需在它们之间搬运上下文。这里的 Claude 指本地 **Claude Code**。

### Codex

发送下面这段安装请求：

```text
请使用 $skill-installer，从 https://github.com/hhaoyy/guanyuan-bi-toolkit
安装以下四套 Skill：
- skills/guanyuan-bi
- skills/guanyuan-html-bi-generic
- skills/guanyuan-metric-lineage
- skills/guanyuan-cli

保留每个目录内的 SKILL.md、references、scripts、assets 等全部文件。
若已有同名技能，先比较差异，保留我的本地定制。
```

安装后，在技能选择器选择 `guanyuan-bi`；在 Codex CLI / IDE 中可以直接发送：

```text
$guanyuan-bi 帮我制作门店经营看板。先推荐两种布局，
用模拟数据预览，再按我确认的字段接入观远。
```

技能未显示时重启后检查。安装及显式调用方式见 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills)。

### Claude Code

发送下面这段安装请求：

```text
请从 https://github.com/hhaoyy/guanyuan-bi-toolkit 下载：
- skills/guanyuan-bi
- skills/guanyuan-html-bi-generic
- skills/guanyuan-metric-lineage
- skills/guanyuan-cli

把四个完整目录分别安装到 ~/.claude/skills/ 下，保持各自目录名。
保留 SKILL.md、references、scripts、assets 等全部内容。
若已有同名技能，先比较差异，保留我的本地定制。
```

随后发送：

```text
/guanyuan-bi 帮我制作门店经营看板。先推荐两种布局，
用模拟数据预览，再按我确认的字段接入观远。
```

安装位置与 `/skill-name` 调用方式见 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

<details>
<summary>手动安装、项目内安装与专门技能</summary>

下载仓库，将 `skills/` 下四个完整目录复制到对应位置，不能只复制 `SKILL.md`。

| 工具 | 当前项目 | 个人所有项目 |
| --- | --- | --- |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |

| 用途 | Codex CLI / IDE | Claude Code |
| --- | --- | --- |
| 统一入口、分析需求 | `$guanyuan-bi` | `/guanyuan-bi` |
| HTML 看板设计与数据适配 | `$guanyuan-html-bi-generic` | `/guanyuan-html-bi-generic` |
| 官方 CLI 安装检查、平台操作 | `$guanyuan-cli` | `/guanyuan-cli` |
| 指标、筛选器与来源梳理 | `$guanyuan-metric-lineage` | `/guanyuan-metric-lineage` |

</details>

<a id="usage"></a>

## 用自己的需求开始

在 Codex 或 Claude Code 中打开**你自己的项目目录**，调用 `guanyuan-bi` 后接着描述任务。可以给业务问题、字段说明或已有看板链接；不必先自己写好完整的数据契约。

### 1. 新建看板：从问题到预览

```text
使用者：区域运营负责人。
问题：本期经营如何，哪些门店贡献了主要变化？
已有材料：日期、门店、订单数、销售额的字段说明。
对比范围：本周与上周的完整周期；金额单位由我确认。

请先推荐两种布局并说明适合回答什么问题，使用模拟数据制作预览。
保留分组切换、变化分析和可执行调查。
口径不明确的部分先标出来，文件保存到当前项目目录。
```

你会得到：布局建议、需要确认的口径、页面预览，以及接入所需字段。可继续说“采用紧凑主题”“把调查结果放在趋势下面”，再调整设计。

### 2. 接入与发布：沿用同一任务

```text
按我们确认的布局和口径继续。
请使用 guanyuan-cli 检查所需官方组件，复用适合的已有登录。
目标观远实例、目录和数据源使用我提供的信息或项目配置。
创建或复用数据集，完成字段绑定和发布，回读核对数据与交互。
保留源工程和资源映射，后续继续修改同一个看板。
```

安装 Skill 不等于安装官方 CLI。发布需要对应环境的访问与操作权限；没有平台访问条件时，先交付预览和接入文件。详细步骤见 [CLI 使用指南](cli.md)。

### 3. 已有看板：理解口径，再分析变化

```text
请使用 guanyuan-bi 分析这个看板：[替换为我的看板链接]。
先梳理指标公式、默认筛选和数据来源。
在获准的数据范围内比较两个完整周期，找出主要变化分组。
区分数值事实、解释假设与证据缺口；继续执行可支持的调查。
这次只分析，不修改线上看板。
```

当前配置优先通过 CLI 获取，离线或明确缺口再使用 HAR。详见 [指标血缘指南](lineage.md)。


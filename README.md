<div align="center">

# 🪐 Guanyuan BI Toolkit

**用 Codex / Claude Code，把一句需求变成观远 BI 看板。**

描述需求 → 预览设计 → 接入数据 → 发布与维护

[看效果](#preview) · [开始使用](#start) · [版本更新](docs/updating.md)

</div>

## 从一个小需求开始

> “我想做一张门店经营看板：本周卖得怎么样？哪些门店增长、哪些下降？”

把这句话和已有字段说明交给 AI，Skill 会帮助你选择图表、生成可交互页面、梳理指标口径，并通过官方 CLI 完成观远接入。后续改布局、加筛选器，也可以接着用自然语言完成。

适合**已经在使用 AI、又需要在观远 BI 内交付看板**的分析师和开发者。先用字段说明与模拟数据设计，正式交付沿用观远的数据源、数据集和权限管理；交给 AI 的数据范围仍由你的组织决定。

<a id="preview"></a>

### 你能做出什么？

下面是经营总览示例：总指标、周期对比、销售构成和可下钻明细，在一页里讲清整体表现。截图使用虚构的“星际补给站”数据。

[![经营总览示例](docs/assets/templates/overview-layout.png)](docs/assets/templates/overview-layout.png)

布局随任务变化。漏斗突出阶段流失，对比工作台方便逐行比较，监控面板把需要关注的分组放在前面：

| 转化漏斗 | 渠道对比 | 异常监控 |
| --- | --- | --- |
| [![转化漏斗](docs/assets/templates/funnel-layout.png)](docs/assets/templates/funnel-layout.png) | [![渠道对比](docs/assets/templates/channels-layout.png)](docs/assets/templates/channels-layout.png) | [![异常监控](docs/assets/templates/monitor-layout.png)](docs/assets/templates/monitor-layout.png) |
| 哪个环节流失了用户？ | 哪些渠道有规模、转化好？ | 哪些分组达到了关注阈值？ |

这些是可调整的起点。你可以提供喜欢的设计，也可以继续让 AI 改成适合自己的布局。[查看大图、交互与设计参考 →](docs/templates.md)

### Skill 帮你完成哪些工作？

```mermaid
flowchart LR
    A[描述需求<br/>提供字段或已有看板] --> B[AI 梳理指标<br/>选择图表与布局]
    B --> C[生成交互预览<br/>按反馈调整]
    C --> D[接入观远<br/>绑定数据与发布验证]
    D --> E[持续维护<br/>改样式、筛选与指标]
```

- **做看板**：从业务问题到页面设计，支持自定义 HTML，也支持按要求使用观远原生图表。
- **接入与维护**：通过官方 CLI 配置数据集、绑定字段、发布验证，后续更新已有看板。
- **理解数据**：梳理指标公式、筛选和来源；需要分析时，比较变化、拆解贡献，并说明还缺什么证据。

<a id="start"></a>

## 安装并做出第一张看板

### 1. 安装一次

在 Codex 或 Claude Code 中发送：

```text
请从 https://github.com/hhaoyy/guanyuan-bi-toolkit
将 skills/ 下的四个完整技能目录安装到当前工具的个人 skills 目录。
Codex 请使用 $skill-installer；Claude Code 安装到 ~/.claude/skills/。
保留各目录内的全部文件；已有同名技能时保留我的本地定制。
```

安装后统一调用 **guanyuan-bi**：Codex 输入 `$guanyuan-bi`，Claude Code 输入 `/guanyuan-bi`。Codex 中也可通过技能选择器选中它；未出现时重启检查。[完整安装步骤与故障排查 →](docs/getting-started.md)

### 2. 用你的需求开始

在自己的项目目录中调用技能，然后发送下面这个最小案例。把字段和目标换成你的实际需求即可：

```text
帮我做一张门店经营看板，给区域运营负责人看。
我有：日期、门店、销售额、订单数；销售额单位为元。
想看：本周与上周的整体表现，以及各门店的变化。
先用模拟数据制作可交互预览，把需要确认的指标口径列出来。
```

你会先得到**可打开的页面预览和待确认的口径**。继续说“把门店对比放大”“增加门店筛选”，就能在同一个任务中迭代。

### 3. 满意后接入观远

```text
按确认后的设计继续。目标观远看板是：[我的看板链接]，
数据集是：[我有权限使用的数据集]。
请核对字段映射，完成接入，并验证筛选和展示结果。
```

也可以提供目标目录新建看板。平台接入需要对应访问权限；预览阶段无需观远登录。Skill 会检查所需官方 CLI 的版本与能力，再继续交付。

## 需要时再看

- [安装、已有看板改造与更多使用示例](docs/getting-started.md)
- [官方 CLI 与本项目的关系、更新与兼容](docs/updating.md) — 本项目提供社区 Skill，官方 CLI 单独安装和更新。
- [模板画廊与进一步分析](docs/templates.md) · [指标血缘](docs/lineage.md) · [HTML 接入](docs/html-bi.md)
- [超级应用、外接 AI / MCP 与实时刷新](examples/superapp-analysis/README.md)

[MIT License](LICENSE) · 独立社区项目，与观远官方无隶属或背书关系。

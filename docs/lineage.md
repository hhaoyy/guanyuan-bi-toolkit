# 观远指标血缘：CLI 优先，HAR 补充

## 推荐入口

已经安装并登录 `guancli` 时，只需向 Metric Lineage Skill 提供看板链接或页面 ID：

```text
请使用 guanyuan-metric-lineage 梳理这个观远看板。
输出卡片指标与公式、筛选器默认值及作用范围、卡片联动、数据集计算字段和可见的上游来源。
优先使用 guancli 读取当前配置；只有明确缺口无法通过 CLI 获取时再告诉我是否需要 HAR 或其他上游证据。
```

Skill 会先读取页面详情，再按页面实际引用扩展卡片、数据集和 ETL。相同数据集只查询一次。输出区分卡片计算、数据集计算、普通聚合、数据集来源和更上游逻辑，并标明每项证据来自 CLI、HAR 还是其他工具。

CLI 路径依赖目标环境的实际权限和版本。读取成功代表看到了当前配置，不代表公式符合业务定义；需要验数时应明确页面、卡片和筛选上下文。

## CLI 能直接覆盖的重点

| 目标 | 主要证据 |
| --- | --- |
| 看板卡片和字段 | `page get`，必要时补 `card get` |
| 卡片公式、聚合和查询模型 | 页面/卡片完整详情 |
| 筛选器、默认值与目标映射 | 页面详情中的 selector 与 interaction 配置 |
| 自动联动和显式联动 | 源字段、目标卡片/字段及 linkage 配置 |
| 数据集计算字段和来源 | 完整 `ds get` 与关联摘要 |
| ETL 节点与 SQL | `etl get` |
| 特定筛选上下文下的结果 | `card preview` / `ds preview` |

具体过程由技能的 [CLI 优先工作流](../skills/guanyuan-metric-lineage/references/cli-first.md)维护，命令细节以本机安装的官方组件文档为准。

## 什么时候使用 HAR

以下情况才需要 HAR：

- 用户要求离线分析或历史请求快照；
- 当前环境无法安装、登录或连接 CLI；
- 权限或客户端/服务端兼容性导致某项配置无法读取；
- 需要核对浏览器实际请求中、但 CLI 未暴露的内容；
- 用户已经提供 HAR，希望利用已有材料。

只针对缺失项补采，不重新采集 CLI 已经确认的完整页面。CLI 代表读取时的当前状态，HAR 代表捕获时的请求状态，两者不能当成同一时间点无条件合并。

## HAR 合成示例与离线解析

仓库根目录运行：

```bash
python3 scripts/generate_synthetic_har.py
python3 skills/guanyuan-metric-lineage/scripts/analyze_guanyuan_logs.py local/synthetic-cafe.har --output-root output/cafe
```

生成器从零构造一家虚构咖啡店的看板配置。真实 HAR 和解析结果可能包含认证信息、SQL、字段、筛选值、内部地址和资源 ID，必须留在获准的私有环境。

同一看板有多份运行态和编辑态记录时：

```bash
python3 skills/guanyuan-metric-lineage/scripts/analyze_guanyuan_logs.py \
  local/runtime.har local/edit.har --merge --output-root output/merged
```

`--merge` 仅拼接同一看板的请求并选择内容最完整的页面配置，不调和冲突版本。不同看板分别解析。解析限制和精确补采方法见 [HAR 兜底说明](../skills/guanyuan-metric-lineage/references/har-fallback.md)。

## 结果怎么读

统一报告使用以下证据等级：

| 标记 | 说明 |
| --- | --- |
| `confirmed_cli` | 当前平台配置由 CLI 直接读取 |
| `confirmed_har` | 配置或请求由 HAR 响应正文确认 |
| `partial` | 已定位资源，但公式、来源或映射仍缺证据 |
| `missing` | 关键资源或字段身份尚未确认 |

证据等级说明“看到了什么”，不说明业务口径或数值一定正确。报告应同时列出无法通过当前证据回答的具体问题，以及最小的下一步查询、权限或补采动作。

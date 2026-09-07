# 观远指标血缘：怎么采，怎么看

## 先使用合成示例

仓库根目录运行：

```bash
python3 scripts/generate_synthetic_har.py
python3 skills/guanyuan-metric-lineage/scripts/analyze_guanyuan_logs.py local/synthetic-cafe.har --output-root output/cafe
```

生成器从零构造一家虚构咖啡店的看板配置，包含销量聚合、客单价公式、门店筛选器和虚构源表。

## 在获准环境采集自己的看板

1. 打开目标看板及浏览器开发者工具 Network 面板。
2. 清空记录，保留跨页日志，刷新看板并等待卡片加载。
3. 遍历页签、滚动加载内容、展开并切换筛选器。
4. 公式缺失时打开卡片编辑页；源表或 SQL 缺失时打开数据集编辑页。
5. 导出含响应正文的 HAR。浏览器菜单名称取决于版本。
6. 文件保存到仓库外的受控目录，本地运行解析器。

HAR 和解析结果都可能包含敏感信息。不要上传至本仓库或任何未获准服务。不要为了调试输出认证头、Cookie 或令牌。

## 多份文件

同一看板的运行态和编辑态记录：

```bash
python3 skills/guanyuan-metric-lineage/scripts/analyze_guanyuan_logs.py \
  local/runtime.har local/edit.har --merge --output-root output/merged
```

不同看板：去掉 `--merge`，各自生成结果目录。`--merge` 拼接请求记录，解析器取正文最大的页面配置，其他受支持的请求补充运行态信息。它不会合并两个冲突页面，也不会自动把独立数据集编辑接口注入页面的 `dsInfos`。

## 四种计算层

| 标记 | 说明 |
| --- | --- |
| `guanyuan_card` | 卡片内计算公式 |
| `guanyuan_dataset` | 数据集内计算公式 |
| `guanyuan_aggregation` | SUM、COUNT 等聚合 |
| `warehouse_or_source_field` | 直接读取上游字段 |

## 三种来源证据

| 标记 | 说明 |
| --- | --- |
| `confirmed_guanyuan` | 捕获到数据集绑定表或 SQL |
| `partial` | 有数据集信息，缺来源配置 |
| `missing` | 没有该字段的数据集标识 |

这些标记说明捕获证据的范围，不说明业务定义或数值已正确。`requires_warehouse_trace=true` 提醒继续追踪上游；`false` 也不代表所有依赖均已验证。

## 当前限制

- 页面响应需为直接包含 `cards` 和 `dsInfos` 的 JSON 对象。
- 不自动解码 base64 响应，不支持所有嵌套封装。
- SQL 引用通过简单静态规则提取，CTE、引号、注释和复杂方言可能产生误识别，必须核验。
- CSV 保留卡片/数据集公式及源 SQL 全文；Markdown 为便于阅读可能截断。
- 筛选器自动联动、编辑态缺口及业务语义仍需人工确认。
- 只验证合成输入，不声明跨版本全面兼容。

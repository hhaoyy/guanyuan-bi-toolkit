# 安装自检与看板项目初始化

[返回首页](../README.md) · [安装](../INSTALL.md) · [版本更新](updating.md)

## 直接交给 AI

```text
请使用 guanyuan-bi 检查实际加载的技能版本和文件完整性，
然后在我的工作目录下新建一个门店看板项目。
先准备经营总览的页面骨架、字段映射和验收记录；
我接着提供字段说明，请继续完成预览。
```

已有项目先读取 `project.json`，不要重复初始化。工具不会凭空生成业务数据或把创建工程标记为发布成功。

## 命令接口

`<guanyuan-bi目录>` 是当前工具实际加载的技能目录。先检查技能文件，再按需检查当前任务需要的官方组件：

```bash
python3 <guanyuan-bi目录>/scripts/toolkit.py check
python3 <guanyuan-bi目录>/scripts/toolkit.py check --components guancli guands guanvis --bin-dir <选定运行时的bin目录>
```

传入 `--bin-dir` 后只检查该目录，不会回退到 PATH。省略时才使用 PATH。输出区分技能版本与 CLI 版本；只执行本地 `--version` / `--help`，不登录或查询 BI。需要读写平台时仍须执行 CLI 技能中的版本适配和实际权限检查。

初始化一个新目录：

```bash
python3 <guanyuan-bi目录>/scripts/toolkit.py init --project <私有工作目录>/store-dashboard --template overview
```

布局可选 `overview`、`funnel`、`channels`、`monitor`。生成：

```text
store-dashboard/
├── project.json          # 技能版本、页面身份、数据集绑定、CLI 选择与验收状态
├── field-mapping.json    # 字段、粒度、单位、比较范围与质量证据
├── src/                  # 可打开的本地页面及模板资源
├── evidence/             # 私有验收记录
└── README.md             # 继续工作的步骤
```

用浏览器打开 `src/index.html`。初始页面提示尚未完成数据确认；之后由 AI 根据你的材料填写映射、编写适配并完成预览。此骨架不是观远官方发布工程，平台交付仍使用对应 CLI 版本的构建接口，并排除本地数据加载器。

再次初始化已有工程不会覆盖文件。非空的其他目录会被拒绝，避免误改已有项目。工具不会把工程创建在技能包内。

后续自检：

```bash
python3 <guanyuan-bi目录>/scripts/toolkit.py check --project <私有工作目录>/store-dashboard
```

这里只确认工程文件是否齐全；字段映射正确、数字一致、线上发布成功必须分别验收。开始下一次修改时，让 AI 读取工程记录、检查线上状态，再复用原页面和数据集编号。

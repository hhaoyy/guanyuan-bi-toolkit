# 更新与版本兼容

[返回项目首页](../README.md)

## 三个层次，不要混淆

| 层次 | 谁提供 | 更新后改变什么 |
| --- | --- | --- |
| `guanyuan-bi-toolkit` 中的四套 Skill | 本社区项目 | 工作流程、模板、诊断逻辑与适配指导 |
| `@guandata/guancli`、`guanvis` 等 CLI / `guanskill` 套件 | 观远官方 | 命令、平台 API 支持和官方配套文档 |
| 组织部署的观远 BI 服务端 | 组织与观远 | 服务端能力、权限、授权与接口行为 |

名字相似，但本仓库的 `skills/guanyuan-cli/SKILL.md` 是给 AI 的操作说明，不是官方命令行程序。它不会随仓库分发或自动替换官方二进制。官方套件自带的技能文档用于了解对应版本 API；本社区 Skill 负责组合工作流程，两者应保留各自的用途。

## “自动适配”做什么？

平台任务开始时检测所选 CLI 的实际版本及指纹。升级或降级后，重新读取匹配的官方文档，更新用户私有项目中的能力记录，再验证受影响的行为。

**自动适配不等于自动更新 Skill，也不等于自动安装最新 CLI。** 当前没有后台定时升级或自动拉取仓库。它也不能凭版本号证明任意服务端兼容。详见 [机制说明](../skills/guanyuan-cli/references/compatibility.md)。

## 更新已安装 Skill

优先选择 [Release](https://github.com/hhaoyy/guanyuan-bi-toolkit/releases) 中的固定版本，阅读变更说明后运行新安装包的安装器；未修改旧版本会备份，定制冲突会保留。具体见 [安装与升级](../INSTALL.md)。用 `toolkit.py version` 和 `toolkit.py check` 核对实际加载位置。

以下方式用于明确希望跟随主分支开发版本的用户：

推荐在原来安装技能的 Codex / Claude Code 中发送：

```text
请检查 https://github.com/hhaoyy/guanyuan-bi-toolkit 的最新提交，
比较我实际安装的四套 Skill：guanyuan-bi、guanyuan-html-bi-generic、
guanyuan-metric-lineage、guanyuan-cli。

更新到仓库最新版本，保留完整 references、scripts 和 assets。
先保存当前版本；保留我的本地定制，只有无法合并的冲突再问我。
不要改动我的项目数据、登录配置或官方 CLI 安装。
完成后核对实际加载目录，并记录本次安装的提交号。
```

只有用 Git 克隆且工作区干净的仓库副本才适合执行 `git pull --ff-only`。**更新下载目录不会自动更新另行复制到技能目录的版本。** 要同步实际安装位置；避免留下同名旧副本导致加载错版本。安装和发现方式见项目首页。

## 检查官方最新版

在有 npm 的环境中读取官方元数据：

```bash
npm view @guandata/guanskill version dependencies
npm view @guandata/guancli version engines os cpu
npm view @guandata/guanvis version engines os cpu
```

只查询任务涉及的其他组件即可。再用实际选定运行时的 `--version` 对照，不以全局 PATH 中的另一个程序代替。

2026-11-06 查询快照（不是永久固定的最新版）：

| 包 | 当日官方版本 |
| --- | --- |
| `@guandata/guanskill` | 0.1.55 |
| `@guandata/guancli` | 1.0.72 |
| `@guandata/guands` | 0.1.41 |
| `@guandata/guanvis` | 0.1.62 |
| `@guandata/guanetl` | 0.1.45 |
| `@guandata/guanwf` | 0.1.842 |
| `@guandata/guanmetric` | 0.1.23 |

来源：[官方套件元数据](https://registry.npmjs.org/@guandata%2fguanskill/0.1.55)、[GuanCLI](https://registry.npmjs.org/@guandata%2fguancli/1.0.72)、[GuanVis](https://registry.npmjs.org/@guandata%2fguanvis/0.1.62)。套件号与组件号不是同一个版本体系，独立组件和套件也可能不同步。

## 想升级到最新版，如何操作？

可以明确交给 AI：

```text
请使用 guanyuan-cli 检查我当前实际使用的官方组件，
查询官方最新版本、变更说明和系统要求。
将本项目需要的组件升级到当前适用的最新版本，使用隔离安装目录，
保留旧运行时和登录配置，不直接覆盖全局安装。
固定实际选中的版本，加载它们配套的官方文档，
验证本地启动和获准的只读连接，再检查本次受影响的功能。
线上写入验证只在我已授权的目标内执行。
记录旧版本、新版本、测试结果和切回旧版本的方法。
```

升级流程：**发现最新版 → 确认受影响能力 → 隔离安装确切版本 → 验证 → 切换项目运行时**。

使用官方套件时优先采用一套一致的组件组合；独立安装时记录各包的确切版本。不要只替换一个二进制，却继续使用另一个版本的文档。启动成功、认证成功、首次发布成功和同 ID 更新成功是不同层次的证据。

若最新版本尚不适用于当前服务端，就暂时保留已验证版本，记录缺口。遇到权限、商业授权或服务端故障，不应假定升级客户端可以解决。切回旧二进制也不会撤销已经发生的线上变更。

## 我们需要跟随官方每次发版吗？

不需要同步复制每一版官方工具，但需要维护受影响的工作流程：

- 命令参数或结果结构改变：更新对应适配与测试。
- HTML SDK、数据绑定、备份或发布行为改变：验证相应交付路径。
- 新增官方能力：评估是否能改善用户工作，再加入技能。
- 与本项目无关的变化：不用为了版本号重写全部 Skill。

若发现当前说明与安装版本冲突，优先查该版本官方文档，明确缺口，不假装已兼容；可以用合成复现向本仓库反馈。

# 安装这个版本

需要 Python 3.9+。自动化测试使用 Python 3.12；其他 Python / 操作系统组合尚未完成完整验收。

从 [Releases](https://github.com/hhaoyy/guanyuan-bi-toolkit/releases) 下载命名为 `guanyuan-bi-toolkit-版本号.zip` 的安装包，解压后在该目录运行：

```bash
# Codex：安装到 ~/.agents/skills/
python3 scripts/install.py --target codex

# Claude Code：安装到 ~/.claude/skills/
python3 scripts/install.py --target claude
```

安装目录依据 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills) 与 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

两条命令任选其一。若工具配置了其他技能目录，使用 `--skills-dir <实际技能目录>`，也支持项目内的技能目录。安装器复制四个完整目录，不安装官方 CLI，不改动项目文件或登录状态。

也可以把安装包交给 AI，让它按本文件完成安装；无需自己执行命令。

## 确认安装

安装后让 AI 从**实际加载的 guanyuan-bi 技能目录**运行：

```bash
python3 <guanyuan-bi目录>/scripts/toolkit.py version
python3 <guanyuan-bi目录>/scripts/toolkit.py check
```

检查包括四套技能的版本是否一致、配套文件是否完整、是否有本地修改。默认检查该技能的同级目录；若技能分散安装，用 `--skills-dir` 检查对应目录。输出的目录是检查对象，不代表工具自动发现的所有技能来源。

技能未显示时重新加载 / 重启工具，再用 Codex 的 `$guanyuan-bi` 或 Claude Code 的 `/guanyuan-bi` 调用。[完整说明](docs/getting-started.md)。

## 更新与本地定制

新版安装包使用相同命令。完整且未修改的旧版本会先备份到技能根目录旁的 `.guanyuan-bi-backups/`，然后替换；备份目录不在技能发现目录内。版本和安装回执可用于排查问题。

若旧技能缺少版本清单、存在修改或额外文件，安装器会报告冲突并保持四套技能不变。请让 AI 对比并合并定制，或选择另一目录安装；不要为了消除提示直接删除自己的内容。重复安装同一份包不会重复覆盖。

失败时会尝试恢复本次替换前的目录。若进程被强制结束或断电，先运行自检并检查回执；从备份恢复四套技能，确保版本一致后再使用。技能文件回退不会撤销线上 BI 修改。

## 文件校验

发布页提供 `SHA256SUMS`，用于比对安装包下载前后的 SHA-256。包内 `PUBLIC_FILES.sha256` 可通过以下命令检查：

```bash
python3 scripts/check_public_files.py
```

校验用于发现文件差异，不能替代对下载来源的信任。主分支持续变化；试用反馈请附 `VERSION` 中的版本号。

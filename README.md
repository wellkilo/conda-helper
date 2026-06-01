<div align="center">

<h1>conda-helper</h1>

<p>
  <strong>Make Conda environment operations beautiful, safe, and repeatable.</strong><br />
  <strong>让 Conda 环境管理更优雅、更安全、更可复现。</strong>
</p>

<p>
  <a href="#english">English</a> ·
  <a href="#中文">中文</a> ·
  <a href="https://wellkilo.github.io/conda-helper/">Website</a> ·
  <a href="#command-reference--命令速查">Commands</a> ·
  <a href="#development--开发">Development</a>
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-2ea44f?style=for-the-badge" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-0ea5e9?style=for-the-badge" />
  <img alt="CLI" src="https://img.shields.io/badge/CLI-Click-111827?style=for-the-badge" />
  <a href="https://wellkilo.github.io/conda-helper/"><img alt="Website" src="https://img.shields.io/badge/Website-GitHub%20Pages-4ade80?style=for-the-badge&logo=githubpages&logoColor=white" /></a>
</p>

</div>

---

<div align="center">

| Backup | Restore | Clone | Pack | Clean | Doctor | Panel |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Versioned YAML | Name override | One command | Offline archive | Batch + cache | Friendly hints | Interactive UI |

</div>

---

## English

`conda-helper` is a small, cross-platform command-line companion for native [`conda`](https://docs.conda.io/). It wraps frequent but fiddly environment tasks into readable one-liners, adds safer defaults, and translates common failures into actionable hints.

Project website: [`wellkilo.github.io/conda-helper`](https://wellkilo.github.io/conda-helper/)

<table>
  <tr>
    <td width="50%">
      <h3>✨ What it helps with</h3>
      <ul>
        <li><strong>Back up</strong> environments to timestamped YAML files.</li>
        <li><strong>Restore</strong> from any backup with optional name override.</li>
        <li><strong>Clone</strong> environments without memorising long Conda flags.</li>
        <li><strong>Pack</strong> offline archives with <code>conda-pack</code> when available.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🛡️ Why it feels better</h3>
      <ul>
        <li><strong>Batch remove</strong> stale environments safely.</li>
        <li><strong>Purge</strong> caches with dry-run support.</li>
        <li><strong>Doctor</strong> command for health checks and missing optional tools.</li>
        <li><strong>Friendly errors</strong> for network, channel, disk, and permission issues.</li>
      </ul>
    </td>
  </tr>
</table>

> `conda-helper` does not replace Conda. It composes Conda into a smoother workflow for algorithm engineers, research engineers, and anyone who manages many local environments.

---

## 中文

`conda-helper` 是一个轻量、跨平台的 Conda 命令行增强工具。它基于原生 [`conda`](https://docs.conda.io/) 封装常用环境管理动作，把繁琐命令变成清晰的一行命令，并提供更友好的错误提示与交互式面板。

项目介绍网站：[`wellkilo.github.io/conda-helper`](https://wellkilo.github.io/conda-helper/)

<table>
  <tr>
    <td width="50%">
      <h3>✨ 适合解决什么问题</h3>
      <ul>
        <li><strong>备份环境</strong>：自动生成带时间戳的 YAML 文件。</li>
        <li><strong>恢复环境</strong>：从备份文件重建环境，并支持改名。</li>
        <li><strong>克隆环境</strong>：无需记忆复杂的 Conda 参数。</li>
        <li><strong>离线打包</strong>：优先使用 <code>conda-pack</code> 生成可迁移归档。</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🛡️ 为什么更顺手</h3>
      <ul>
        <li><strong>批量删除</strong>：一次清理多个废弃环境。</li>
        <li><strong>缓存清理</strong>：支持 dry-run，先看结果再执行。</li>
        <li><strong>健康检查</strong>：检测 Conda 配置和可选依赖。</li>
        <li><strong>友好报错</strong>：把网络、源、磁盘、权限问题翻译成行动建议。</li>
      </ul>
    </td>
  </tr>
</table>

> `conda-helper` 不替代 Conda，而是把 Conda 常用能力组合成更适合日常研发、算法实验和迁移部署的工作流。

---

## Highlights / 功能亮点

<div align="center">

| Capability / 能力 | Command / 命令 | Benefit / 收益 |
|---|---|---|
| Environment list / 环境列表 | `conda-helper ls` | Show prefix and on-disk size; use `--no-size` for the fastest list / 展示路径与磁盘占用；使用 `--no-size` 可最快列出 |
| Versioned backup / 版本化备份 | `conda-helper backup my_env` | Timestamped YAML / 自动生成时间戳 YAML |
| Portable backup / 可移植备份 | `conda-helper backup my_env --from-history` | Export explicit packages only / 只导出主动安装包 |
| Restore / 恢复 | `conda-helper restore env.yml -n my_env_v2` | Rebuild with name override / 支持恢复时改名 |
| Clone / 克隆 | `conda-helper clone src dst` | Wrapper over native clone / 封装原生克隆能力 |
| Offline pack / 离线打包 | `conda-helper pack my_env -o ./dist/` | Prefer `conda-pack`, fallback to tarball / 优先可迁移打包 |
| Batch remove / 批量删除 | `conda-helper rm old_env exp_env --yes` | Remove multiple envs / 一次删除多个环境 |
| Cache purge / 缓存清理 | `conda-helper purge --dry-run` | Preview reclaimable space / 先预览再清理 |
| Health check / 健康检查 | `conda-helper doctor` | Detect broken config and optional deps / 检测配置与依赖 |
| Interactive panel / 交互面板 | `conda-helper panel` | TTY menu for guided operations / 适合不想记参数的用户 |

</div>

---

## Installation / 安装

<details open>
<summary><strong>Install from PyPI / 从 PyPI 安装</strong></summary>

```bash
pip install conda-helper
```

</details>

<details>
<summary><strong>Install from source / 从源码安装</strong></summary>

```bash
git clone https://github.com/wellkilo/conda-helper.git
cd conda-helper
pip install -e .
```

</details>

<details>
<summary><strong>Optional offline packing dependency / 可选离线打包依赖</strong></summary>

```bash
conda install -n base -c conda-forge conda-pack
```

`conda-helper pack` works best with `conda-pack`. If it is not installed, the tool falls back to a plain tarball with metadata, which should only be restored on identical OS/architecture hosts.

`conda-helper pack` 配合 `conda-pack` 效果最佳。如果未安装，将回退为普通 tarball + 元数据，这种方式只建议在相同系统与架构的机器之间恢复。

</details>

Verify the installation / 验证安装：

```bash
conda-helper --version
conda-helper doctor
```

---

## Quick Start / 快速开始

```bash
# List environments with on-disk size
# 查看环境列表与磁盘占用
conda-helper ls

# Fast list when you do not need size calculation
# 不需要统计磁盘占用时，可跳过目录扫描以获得最快输出
conda-helper ls --no-size

# Back up an environment to the default backup directory
# 备份环境到默认备份目录
conda-helper backup my_env

# Export only explicitly requested packages for better portability
# 只导出主动安装的包，跨平台迁移更友好
conda-helper backup my_env --from-history

# Restore on another machine and rename the environment
# 在另一台机器恢复，并重命名环境
conda-helper restore ./my_env-20260601-101530.yml -n my_env_v2

# Clone an environment
# 克隆环境
conda-helper clone my_env my_env_copy

# Pack for an offline server
# 打包到离线服务器
conda-helper pack my_env -o ./dist/

# Remove stale environments and reclaim disk space
# 批量删除旧环境并清理缓存
conda-helper rm legacy_env exp_2023 --yes
conda-helper purge
```

Prefer a guided UI? / 更喜欢交互式界面？

```bash
conda-helper panel
```

---

## Command Reference / 命令速查

| Long form / 完整命令 | Short / 短命令 | Description / 说明 |
|---|---:|---|
| `conda-helper ls` | `ch l` | List envs with size and prefix. Use `--no-size` for fastest output, or `--json` for machine output. / 列出环境、大小与路径；可用 `--no-size` 最快输出，或用 `--json` 输出机器可读格式。 |
| `conda-helper backup <name>` | `ch b` | Export to versioned YAML. Add `--from-history` for portable backups. / 导出带版本的 YAML，可加 `--from-history` 增强可移植性。 |
| `conda-helper restore <yaml>` | `ch r` | Recreate from YAML. Use `-n` to rename. / 从 YAML 重建环境，可用 `-n` 改名。 |
| `conda-helper clone <src> <dst>` | `ch c` | Wraps `conda create --clone`. / 封装原生克隆能力。 |
| `conda-helper pack <name>` | `ch pk` | Build offline archive, preferring `conda-pack`. / 构建离线归档，优先使用 `conda-pack`。 |
| `conda-helper rm <names...>` | — | Batch remove with confirmation. Add `--yes` to skip prompt. / 批量删除环境，使用 `--yes` 跳过确认。 |
| `conda-helper purge` | `ch p` | Run `conda clean --all`; supports `--dry-run`. / 清理 Conda 缓存，支持 `--dry-run`。 |
| `conda-helper doctor` | — | Health check and missing-tool detector. / 健康检查与可选工具检测。 |
| `conda-helper panel` | — | Interactive menu, TTY only. / 交互式菜单，仅支持 TTY。 |

Run the following for full flags / 查看完整参数：

```bash
conda-helper <cmd> -h
```

### Performance Notes / 性能说明

- `conda-helper ls` calculates on-disk size by scanning each environment directory. This is useful, but it can take a while when environments contain many small files. The command shows a waiting hint in interactive terminals while it is working.
- `conda-helper ls --no-size` skips directory scanning and only asks Conda for the environment list, so it is the fastest way to check names and prefixes.
- Other long-running commands such as `backup`, `restore`, `clone`, `pack`, `rm`, `purge`, and `doctor` also print lightweight waiting hints in interactive terminals.

- `conda-helper ls` 会扫描每个环境目录来计算磁盘占用。这个信息很有用，但当环境里有大量小文件时会变慢；现在交互式终端会显示等待提示。
- `conda-helper ls --no-size` 会跳过目录扫描，只向 Conda 获取环境列表，因此是查看环境名和路径的最快方式。
- `backup`、`restore`、`clone`、`pack`、`rm`、`purge`、`doctor` 等其它可能耗时的命令，也会在交互式终端显示轻量等待提示。

---

## Friendly Errors / 友好错误提示

When a Conda call fails, `conda-helper` parses stderr and appends a hint.

当 Conda 调用失败时，`conda-helper` 会解析 stderr，并附加更容易行动的建议。

```text
$ conda-helper restore env.yml
`conda env create -n my_env -f env.yml` failed with exit code 1.
stderr: CondaHTTPError: HTTP 000 CONNECTION FAILED for url ...
hint: Network problem talking to the channel. Check VPN/proxy or
      switch to a mirror (e.g. TUNA, USTC).
```

You can add custom rules in [`conda_helper/errors.py`](conda_helper/errors.py).

也可以在 [`conda_helper/errors.py`](conda_helper/errors.py) 中添加自定义错误规则。

---

## Cross-platform Notes / 跨平台说明

<table>
  <thead>
    <tr>
      <th>Platform / 平台</th>
      <th>Conda discovery / Conda 查找逻辑</th>
      <th>Default backup directory / 默认备份目录</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Windows</td>
      <td><code>CONDA_EXE</code> → PATH → common install directories</td>
      <td><code>%LOCALAPPDATA%\conda-helper\backups</code></td>
    </tr>
    <tr>
      <td>macOS</td>
      <td><code>CONDA_EXE</code> → PATH → <code>~/miniconda3/bin/conda</code> / <code>~/anaconda3/bin/conda</code></td>
      <td><code>~/Library/Application Support/conda-helper/backups</code></td>
    </tr>
    <tr>
      <td>Linux</td>
      <td><code>CONDA_EXE</code> → PATH → <code>~/miniconda3/bin/conda</code> / <code>/opt/conda/bin/conda</code></td>
      <td><code>~/.local/share/conda-helper/backups</code></td>
    </tr>
  </tbody>
</table>

---

## Why Another Tool? / 为什么还需要一个工具？

| Existing tool / 现有工具 | Gap / 痛点 | How `conda-helper` helps / 如何补足 |
|---|---|---|
| `conda env export` | No backup convention or restore verb. / 缺少备份目录规范与恢复语义。 | Adds timestamped backups and restore workflow. / 提供时间戳备份与恢复流程。 |
| `conda-pack` | Excellent for packing, but only packing. / 打包很强，但能力单一。 | Combines pack with list, backup, clone, clean, and doctor. / 与列表、备份、克隆、清理、检查组合。 |
| `conda clean` | Easy to misuse in scripts. / 脚本中不够直观。 | Adds a friendlier `purge` command with dry-run support. / 提供更清晰的清理命令与预览。 |
| Native `conda` | Verbose flags and cryptic stack traces. / 参数冗长，报错不友好。 | Provides aliases, panel UI, and actionable hints. / 提供短命令、面板与行动建议。 |

---

## Development / 开发

```bash
git clone https://github.com/wellkilo/conda-helper.git
cd conda-helper
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

The test suite stubs out the Conda binary, so it can run without creating or destroying real environments. CI is designed for Ubuntu, macOS, and Windows across multiple Python versions.

测试会 stub Conda 二进制文件，因此不会真实创建或删除环境。CI 设计覆盖 Ubuntu、macOS、Windows 与多个 Python 版本。

Useful project files / 常用项目文件：

- [`pyproject.toml`](pyproject.toml) — package metadata, dependencies, and CLI entry points / 包元信息、依赖与命令入口。
- [`conda_helper/cli.py`](conda_helper/cli.py) — Click command definitions / Click 命令定义。
- [`conda_helper/commands.py`](conda_helper/commands.py) — high-level environment operations / 高层环境操作逻辑。
- [`conda_helper/errors.py`](conda_helper/errors.py) — friendly error translation / 友好错误翻译。
- [`docs/contributing.md`](docs/contributing.md) — contribution guide / 贡献指南。

---

## Roadmap / 路线图

- `conda-helper sync` — diff two environments and patch one to match. / 对比两个环境并同步差异。
- Plugin system for custom error-translation rules. / 支持自定义错误翻译规则插件。
- `rich`-powered panel as an optional extra. / 可选引入 `rich` 增强面板体验。
- Lockfile-aware backups for reproducible CI builds. / 支持 lockfile 感知备份，提升 CI 可复现性。

PRs are welcome. See [`docs/contributing.md`](docs/contributing.md).

欢迎提交 PR，详见 [`docs/contributing.md`](docs/contributing.md)。

---

## License / 许可证

MIT © wellkilo. See [`LICENSE`](LICENSE).

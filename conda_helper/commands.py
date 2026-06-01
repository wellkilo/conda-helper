"""High-level operations on conda environments.

Each function takes a :class:`CondaWrapper` and returns plain Python
data, so they can be unit-tested independently of click.
"""
from __future__ import annotations

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .conda_wrapper import CondaWrapper
from .errors import CondaError, CondaHelperError
from .utils import default_backup_dir, file_sha256, human_size


# ---------------------------------------------------------------------- #
# Listing
# ---------------------------------------------------------------------- #
def list_environments(conda: CondaWrapper) -> List[dict]:
    """Return environments enriched with on-disk size."""
    envs = conda.list_envs()
    for env in envs:
        prefix = Path(env["prefix"])
        env["size_bytes"] = _dir_size(prefix) if prefix.exists() else 0
        env["size_human"] = human_size(env["size_bytes"])
    return envs


def _dir_size(path: Path) -> int:
    total = 0
    for root, _, files in __import__("os").walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                continue
    return total


# ---------------------------------------------------------------------- #
# Backup / Restore
# ---------------------------------------------------------------------- #
def backup_environment(
    conda: CondaWrapper,
    name: str,
    *,
    output_dir: Optional[Path] = None,
    from_history: bool = False,
) -> Path:
    """Export an environment to a versioned YAML file.

    Returns the path of the saved YAML.
    """
    output_dir = output_dir or default_backup_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    yaml_text = conda.env_export(name, from_history=from_history)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = "-history" if from_history else ""
    target = output_dir / f"{name}-{timestamp}{suffix}.yml"
    target.write_text(yaml_text, encoding="utf-8")
    return target


def restore_environment(
    conda: CondaWrapper, yaml_path: Path, *, name: Optional[str] = None
) -> str:
    """Recreate an environment from a backed-up YAML.

    Returns the name of the created environment.
    """
    if not yaml_path.exists():
        raise CondaHelperError(f"Backup file not found: {yaml_path}")

    # If user does not pass an explicit name, derive from the YAML.
    target_name = name or _name_from_yaml(yaml_path) or yaml_path.stem.split("-")[0]
    conda.env_create_from_file(target_name, yaml_path)
    return target_name


def _name_from_yaml(yaml_path: Path) -> Optional[str]:
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


# ---------------------------------------------------------------------- #
# Clone
# ---------------------------------------------------------------------- #
def clone_environment(conda: CondaWrapper, src: str, dst: str) -> str:
    conda.env_clone(src, dst)
    return dst


# ---------------------------------------------------------------------- #
# Cleanup / Purge
# ---------------------------------------------------------------------- #
def purge_caches(conda: CondaWrapper, *, dry_run: bool = False) -> str:
    """Remove conda package caches and unused tarballs."""
    return conda.clean(all_=True, dry_run=dry_run).stdout


def batch_remove(
    conda: CondaWrapper, names: Iterable[str]
) -> List[dict]:
    """Remove multiple environments, returning a per-env status list."""
    results = []
    for n in names:
        try:
            conda.env_remove(n)
            results.append({"name": n, "ok": True, "error": None})
        except CondaError as exc:
            results.append({"name": n, "ok": False, "error": str(exc)})
    return results


# ---------------------------------------------------------------------- #
# Offline pack (uses conda-pack if available, falls back to tar of prefix)
# ---------------------------------------------------------------------- #
def pack_environment(
    conda: CondaWrapper,
    name: str,
    *,
    output_dir: Optional[Path] = None,
) -> Path:
    """Bundle an environment into a relocatable archive for offline use.

    Strategy:

    1. Prefer ``conda pack`` (the ``conda-pack`` plugin) if installed,
       because it rewrites shebangs and ``.pc`` paths so the archive is
       relocatable on the target host.
    2. Fall back to a plain tar.gz of the environment prefix plus a
       ``conda-helper-meta.json`` describing the source platform. The
       fallback is only safe between identical OS / arch hosts.
    """
    output_dir = output_dir or default_backup_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    envs = {e["name"]: e for e in conda.list_envs()}
    if name not in envs:
        raise CondaHelperError(f"Environment '{name}' does not exist.")
    prefix = Path(envs[name]["prefix"])

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = output_dir / f"{name}-{timestamp}.tar.gz"

    if shutil.which("conda-pack"):
        # Use the official tool when available.
        conda.run(
            ["pack", "-n", name, "-o", str(archive), "--ignore-missing-files"],
            timeout=None,
        )
    else:
        info = conda.info()
        meta = {
            "source_platform": info.get("platform"),
            "conda_version": info.get("conda_version"),
            "env_name": name,
            "warning": (
                "Created without conda-pack: archive is NOT relocatable. "
                "Restore only on an identical OS/arch with the same prefix path."
            ),
        }
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(prefix, arcname=name)
            meta_path = archive.with_suffix(".meta.json")
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            tar.add(meta_path, arcname="conda-helper-meta.json")
            meta_path.unlink(missing_ok=True)

    return archive


# ---------------------------------------------------------------------- #
# Doctor
# ---------------------------------------------------------------------- #
def doctor(conda: CondaWrapper) -> dict:
    """Run a quick health check and return a structured report."""
    report: dict = {"ok": True, "issues": [], "info": {}}
    try:
        info = conda.info()
        report["info"] = {
            "conda_version": info.get("conda_version"),
            "platform": info.get("platform"),
            "root_prefix": info.get("root_prefix"),
            "channels": info.get("channels", []),
        }
    except Exception as exc:  # pragma: no cover - defensive
        report["ok"] = False
        report["issues"].append(f"conda info failed: {exc}")
        return report

    if not shutil.which("conda-pack"):
        report["issues"].append(
            "conda-pack is not installed. Offline pack will fall back to "
            "a non-relocatable tar archive. Install via "
            "`conda install -n base -c conda-forge conda-pack`."
        )

    if not info.get("channels"):
        report["issues"].append("No channels configured.")

    report["ok"] = not report["issues"]
    return report

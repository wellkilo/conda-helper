"""High-level operations on conda environments.

Each function takes a :class:`CondaWrapper` and returns plain Python
data, so they can be unit-tested independently of click.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tarfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .conda_wrapper import CondaWrapper
from .errors import CondaError, CondaHelperError
from .utils import default_backup_dir, file_sha256, human_size


# ---------------------------------------------------------------------- #
# Listing
# ---------------------------------------------------------------------- #
def list_environments(conda: CondaWrapper, *, include_size: bool = True) -> List[dict]:
    """Return environments enriched with on-disk size.

    Directory sizing is parallelised because Conda environments often
    contain many small files. Walking them sequentially makes
    ``conda-helper ls`` feel frozen on machines with many or large
    environments.
    """
    envs = conda.list_envs()
    if not include_size:
        for env in envs:
            env["size_bytes"] = None
            env["size_human"] = "-"
        return envs

    max_workers = min(8, max(1, len(envs)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        sizes = list(executor.map(_env_size, envs))

    for env, size in zip(envs, sizes):
        env["size_bytes"] = size
        env["size_human"] = human_size(size)
    return envs


def _env_size(env: dict) -> int:
    """Return one environment's size, tolerating disappearing prefixes."""
    prefix = Path(env["prefix"])
    return _dir_size(prefix) if prefix.exists() else 0


def _dir_size(path: Path) -> int:
    """Fast recursive directory size using ``os.scandir``."""
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        else:
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
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
    target = _unique_backup_path(output_dir / f"{name}-{timestamp}{suffix}.yml")
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
    target_name = name or _name_from_yaml(yaml_path) or _name_from_backup_filename(yaml_path)
    conda.env_create_from_file(target_name, yaml_path)
    return target_name


def _unique_backup_path(path: Path) -> Path:
    """Return a non-existing backup path by appending ``-NN`` if needed."""
    if not path.exists():
        return path
    for idx in range(1, 1000):
        candidate = path.with_name(f"{path.stem}-{idx:02d}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise CondaHelperError(f"Could not allocate a unique backup path for: {path}")


def _name_from_yaml(yaml_path: Path) -> Optional[str]:
    with yaml_path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip()
    return None


def _name_from_backup_filename(yaml_path: Path) -> str:
    """Infer env name from conda-helper backup filenames.

    Examples:
    ``my-env-20260601-101530.yml`` -> ``my-env``
    ``data-tools-20260601-101530-history.yml`` -> ``data-tools``
    """
    stem = yaml_path.stem
    match = re.match(r"^(?P<name>.+)-\d{8}-\d{6}(?:-history)?(?:-\d{2})?$", stem)
    if match:
        return match.group("name")
    return stem


# ---------------------------------------------------------------------- #
# Clone
# ---------------------------------------------------------------------- #
def clone_environment(conda: CondaWrapper, src: str, dst: str) -> str:
    if src == dst:
        raise CondaHelperError("Source and destination environment names must differ.")
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
    seen = set()
    for n in names:
        if n in seen:
            results.append({"name": n, "ok": True, "error": "skipped duplicate"})
            continue
        seen.add(n)
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

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = output_dir / f"{name}-{timestamp}.tar.gz"

    if shutil.which("conda-pack"):
        # Use the official tool when available.
        conda.run(
            ["pack", "-n", name, "-o", str(archive), "--ignore-missing-files"],
            timeout=None,
        )
    else:
        envs = {e["name"]: e for e in conda.list_envs()}
        if name not in envs:
            raise CondaHelperError(f"Environment '{name}' does not exist.")
        prefix = Path(envs[name]["prefix"])
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

    for key in ("pkgs_dirs", "envs_dirs"):
        for directory in info.get(key, []) or []:
            if not os.access(directory, os.W_OK):
                report["issues"].append(f"{key[:-1]} directory is not writable: {directory}")

    report["ok"] = not report["issues"]
    return report

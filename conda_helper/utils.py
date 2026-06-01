"""Small cross-platform utilities (paths, hashing, console)."""
from __future__ import annotations

import hashlib
import platform
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import click


def default_backup_dir() -> Path:
    """Return a sensible default backup directory for the host OS."""
    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Local" / "conda-helper" / "backups"
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "conda-helper" / "backups"
    else:
        base = Path.home() / ".local" / "share" / "conda-helper" / "backups"
    base.mkdir(parents=True, exist_ok=True)
    return base


def file_sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def human_size(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Very small spinner using click's secho for cross-platform safety."""
    click.secho(f"... {message}", fg="cyan")
    try:
        yield
    finally:
        click.secho(f"... done: {message}", fg="green")


def require_tool(name: str) -> str:
    """Ensure an auxiliary CLI tool is on PATH; return its absolute path."""
    found = shutil.which(name)
    if not found:
        click.secho(
            f"Optional tool `{name}` not found on PATH. "
            "Some features may be limited.",
            fg="yellow",
            err=True,
        )
    return found or ""


def is_tty() -> bool:
    return sys.stdout.isatty()

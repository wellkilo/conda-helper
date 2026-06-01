"""Low-level wrapper around the ``conda`` executable.

This module centralises every subprocess call so we can:

* Resolve the ``conda`` binary across Windows / macOS / Linux.
* Capture stdout / stderr in a consistent way.
* Translate raw ``CalledProcessError`` into :class:`CondaError` with
  friendly, actionable hints (see :mod:`conda_helper.errors`).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .errors import CondaError, CondaNotFoundError, translate_stderr


@dataclass
class CondaResult:
    """Structured result of a conda subprocess call."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CondaWrapper:
    """Thin, testable wrapper around the conda binary."""

    def __init__(self, conda_bin: Optional[str] = None) -> None:
        self._conda_bin = conda_bin or self._locate_conda()

    # ------------------------------------------------------------------ #
    # discovery
    # ------------------------------------------------------------------ #
    @staticmethod
    def _locate_conda() -> str:
        """Find the conda binary on PATH or via ``CONDA_EXE`` env var."""
        env_path = os.environ.get("CONDA_EXE")
        if env_path and Path(env_path).exists():
            return env_path

        candidate = shutil.which("conda")
        if candidate:
            return candidate

        if platform.system() == "Windows":
            hints = [
                Path(os.path.expanduser("~")) / "miniconda3" / "Scripts" / "conda.exe",
                Path(os.path.expanduser("~")) / "anaconda3" / "Scripts" / "conda.exe",
            ]
        else:
            hints = [
                Path(os.path.expanduser("~")) / "miniconda3" / "bin" / "conda",
                Path(os.path.expanduser("~")) / "anaconda3" / "bin" / "conda",
                Path("/opt/conda/bin/conda"),
            ]
        for h in hints:
            if h.exists():
                return str(h)
        raise CondaNotFoundError(
            "Could not locate the 'conda' executable. "
            "Install Miniconda/Anaconda or set the CONDA_EXE environment "
            "variable."
        )

    # ------------------------------------------------------------------ #
    # generic runner
    # ------------------------------------------------------------------ #
    @property
    def conda_bin(self) -> str:
        return self._conda_bin

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
        capture: bool = True,
        timeout: Optional[int] = None,
    ) -> CondaResult:
        """Run ``conda <args>`` and return a :class:`CondaResult`."""
        cmd: List[str] = [self._conda_bin, *args]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - defensive
            raise CondaNotFoundError(str(exc)) from exc

        result = CondaResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if check and not result.ok:
            hint = translate_stderr(result.stderr)
            raise CondaError(
                f"`conda {' '.join(args)}` failed with exit code {result.returncode}.",
                stderr=result.stderr,
                hint=hint,
            )
        return result

    # ------------------------------------------------------------------ #
    # high-level helpers
    # ------------------------------------------------------------------ #
    def list_envs(self) -> List[dict]:
        """Return a list of environment descriptors."""
        result = self.run(["env", "list", "--json"])
        data = json.loads(result.stdout or "{}")
        envs = data.get("envs", [])
        root = data.get("root_prefix") or ""
        descriptors = []
        for prefix in envs:
            name = Path(prefix).name
            if prefix == root:
                name = "base"
            descriptors.append({"name": name, "prefix": prefix})
        return descriptors

    def env_export(self, name: str, *, from_history: bool = False) -> str:
        args = ["env", "export", "-n", name]
        if from_history:
            args.append("--from-history")
        return self.run(args).stdout

    def env_create_from_file(self, name: str, file_path: Path) -> CondaResult:
        return self.run(
            ["env", "create", "-n", name, "-f", str(file_path)],
            timeout=None,
        )

    def env_remove(self, name: str) -> CondaResult:
        return self.run(["env", "remove", "-n", name, "-y"])

    def clean(self, *, all_: bool = True, dry_run: bool = False) -> CondaResult:
        args = ["clean", "-y"]
        if all_:
            args.append("--all")
        if dry_run:
            args.append("--dry-run")
        return self.run(args)

    def env_clone(self, src: str, dst: str) -> CondaResult:
        return self.run(["create", "-n", dst, "--clone", src, "-y"])

    def info(self) -> dict:
        result = self.run(["info", "--json"])
        return json.loads(result.stdout or "{}")

"""Friendly error types and stderr → hint translation."""
from __future__ import annotations

import re
from typing import Optional


class CondaHelperError(Exception):
    """Base class for all conda-helper errors."""


class CondaNotFoundError(CondaHelperError):
    """Raised when the conda binary cannot be located."""


class CondaError(CondaHelperError):
    """Raised when a conda subprocess call fails."""

    def __init__(self, message: str, *, stderr: str = "", hint: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
        self.hint = hint

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts = [super().__str__()]
        if self.stderr.strip():
            parts.append(f"stderr: {self.stderr.strip()[:500]}")
        if self.hint:
            parts.append(f"hint: {self.hint}")
        return "\n".join(parts)


# ---------------------------------------------------------------------- #
# Mapping from stderr patterns → human hints
# ---------------------------------------------------------------------- #
_HINT_RULES = [
    (
        re.compile(r"EnvironmentLocationNotFound|prefix already exists", re.I),
        "Environment path conflict. Use `conda-helper ls` to inspect and "
        "`conda-helper rm <name>` to remove the old one before retrying.",
    ),
    (
        re.compile(r"PackagesNotFoundError|ResolvePackageNotFound", re.I),
        "Some packages were not found. Try adding `conda-forge` channel via "
        "`conda config --add channels conda-forge`, or pin a different "
        "version.",
    ),
    (
        re.compile(r"CondaHTTPError|HTTP 000|ConnectionError|SSLError", re.I),
        "Network problem talking to the channel. Check VPN/proxy or switch "
        "to a mirror (e.g. TUNA, USTC).",
    ),
    (
        re.compile(r"PermissionError|Errno 13", re.I),
        "Permission denied. Try running with the appropriate user, or use "
        "`--prefix` to write to a writable directory.",
    ),
    (
        re.compile(r"DiskSpaceError|No space left on device", re.I),
        "Disk is full. Run `conda-helper purge` to reclaim cache space.",
    ),
    (
        re.compile(r"CondaValueError.*environment.*already exists", re.I),
        "The target environment already exists. Use `--force` or pick "
        "another name.",
    ),
]


def translate_stderr(stderr: str) -> str:
    """Return a human-friendly hint for a given stderr blob."""
    if not stderr:
        return ""
    for pattern, hint in _HINT_RULES:
        if pattern.search(stderr):
            return hint
    return ""


def format_error(exc: BaseException) -> str:
    """Render an exception for terminal output."""
    if isinstance(exc, CondaError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


__all__ = [
    "CondaHelperError",
    "CondaNotFoundError",
    "CondaError",
    "translate_stderr",
    "format_error",
]

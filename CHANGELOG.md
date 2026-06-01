# Changelog

All notable changes to **conda-helper** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-01

### Fixed
- `backup`: avoid silently overwriting an existing YAML when two backups
  land in the same second; an incrementing `-NN` suffix is now appended.
- `restore`: correctly recover environment names that contain hyphens
  (e.g. `my-env-20260601-101530.yml` → `my-env`) by stripping only the
  trailing timestamp via a dedicated regex instead of `split("-")[0]`.
- `pack` (tar fallback): write the sibling metadata file as
  `<archive>.tar.gz.meta.json` instead of relying on
  `Path.with_suffix(".meta.json")`, which only stripped `.gz`.
- `doctor`: surface non-writable `pkgs_dirs` / `envs_dirs` so users learn
  about permission problems *before* an install fails.
- `clone`: refuse to clone an environment onto itself (`src == dst`)
  with a clear error instead of letting conda fail opaquely.

### Changed
- Consolidated the duplicated `_wait_status` spinner across `cli.py` and
  `panel.py` into a single `utils.wait_status` helper with explicit
  stream selection and TTY awareness.
- `default_backup_dir()` now honours `CONDA_HELPER_BACKUP_DIR`,
  `XDG_DATA_HOME`, and `LOCALAPPDATA` env vars; previously hard-coded
  paths broke on locked-down hosts and made CI runs awkward.
- `human_size(None)` returns `"-"` instead of raising; negative values
  are clamped to zero. Added `PiB` to the unit ladder.
- `pyproject.toml`: reverted SPDX-string license to the table form
  `{ text = "MIT" }` for compatibility with `setuptools < 77`, added
  OS-specific classifiers, dev extra, and coverage config.

### Added
- `MANIFEST.in` so source distributions include `examples/`, `docs/`,
  `LICENSE`, and `CHANGELOG.md`.
- CI matrix now also tests Python 3.8 and caches pip downloads.
- Publish workflow now runs the unit-test suite before building wheels.

## [0.1.0] - 2026-05-30

### Added
- Initial public release.
- Subcommands: `ls`, `backup`, `restore`, `clone`, `rm`, `purge`,
  `pack`, `doctor`, and interactive `panel`.
- Short aliases (`l`, `b`, `r`, `c`, `p`, `pk`).
- Friendly stderr → hint translation for common conda failure modes.
- Parallel directory sizing for `ls`.
- `conda-pack` integration with tarball fallback.
- Cross-platform default backup directory (Linux / macOS / Windows).
- Mock-based unit-test suite covering both the commands layer and the
  click CLI.

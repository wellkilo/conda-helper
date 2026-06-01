# Contributing

Thanks for considering a contribution!

## Dev setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

## Layout

```
conda_helper/
  __init__.py       package metadata (incl. __version__)
  __main__.py       enables `python -m conda_helper`
  cli.py            click entry-points
  panel.py          interactive menu
  commands.py       high-level operations (testable, no click)
  conda_wrapper.py  subprocess wrapper around `conda`
  errors.py         typed errors + stderr → hint translation
  utils.py          tiny cross-platform helpers (paths, spinner, sizes)
tests/
  __init__.py
  test_conda_helper.py   pytest suite, mocks the wrapper
examples/           runnable usage examples
docs/               GitHub Pages site + contributor docs
.github/workflows/  CI matrix + PyPI Trusted-Publisher release pipeline
```

## Adding a new command

1. Implement the logic in `commands.py` taking a `CondaWrapper` argument.
2. Add a `click` command in `cli.py` that calls it.
3. (Optional) wire it into `panel.py`.
4. Cover it in `tests/test_conda_helper.py` using the `fake_wrapper`
   fixture.

## Adding a new error hint

Append a `(pattern, hint)` tuple to `_HINT_RULES` in `errors.py` and a
parametrised case in `test_translate_stderr_matches_rules`.

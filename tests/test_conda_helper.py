"""Unit tests for conda_helper.

These tests do not require a real conda installation; they stub out the
``CondaWrapper`` with a :class:`unittest.mock.MagicMock` so they run on
Windows / macOS / Linux without side effects.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from conda_helper import cli as cli_module
from conda_helper import commands, errors
from conda_helper.conda_wrapper import CondaResult


# ---------------------------------------------------------------------- #
# fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture
def fake_wrapper(tmp_path):
    """A MagicMock conda wrapper preloaded with a small env list."""
    wrapper = MagicMock()
    env_prefix = tmp_path / "envs" / "demo"
    env_prefix.mkdir(parents=True, exist_ok=True)
    (env_prefix / "dummy").write_text("x" * 1024, encoding="utf-8")
    wrapper.list_envs.return_value = [
        {"name": "base", "prefix": str(tmp_path)},
        {"name": "demo", "prefix": str(env_prefix)},
    ]
    wrapper.env_export.return_value = "name: demo\ndependencies:\n  - python=3.11\n"
    wrapper.env_create_from_file.return_value = CondaResult(0, "", "")
    wrapper.env_remove.return_value = CondaResult(0, "", "")
    wrapper.env_clone.return_value = CondaResult(0, "", "")
    wrapper.clean.return_value = CondaResult(0, "cleaned", "")
    wrapper.info.return_value = {
        "conda_version": "24.0.0",
        "platform": "linux-64",
        "root_prefix": str(tmp_path),
        "channels": ["defaults"],
    }
    return wrapper


# ---------------------------------------------------------------------- #
# error translation
# ---------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "stderr, fragment",
    [
        ("CondaHTTPError: HTTP 000", "Network"),
        ("PackagesNotFoundError: foo", "conda-forge"),
        ("PermissionError: [Errno 13]", "Permission"),
        ("CondaValueError: prefix already exists", "Environment path conflict"),
        ("No space left on device", "Disk is full"),
    ],
)
def test_translate_stderr_matches_rules(stderr, fragment):
    assert fragment in errors.translate_stderr(stderr)


def test_translate_stderr_no_match_returns_empty():
    assert errors.translate_stderr("totally novel weird text") == ""


# ---------------------------------------------------------------------- #
# commands layer
# ---------------------------------------------------------------------- #
def test_list_environments_enriches_size(fake_wrapper):
    envs = commands.list_environments(fake_wrapper)
    assert {e["name"] for e in envs} == {"base", "demo"}
    demo = next(e for e in envs if e["name"] == "demo")
    assert demo["size_bytes"] >= 1024
    assert "B" in demo["size_human"]


def test_backup_environment_writes_yaml(tmp_path, fake_wrapper):
    out = commands.backup_environment(fake_wrapper, "demo", output_dir=tmp_path)
    assert out.exists()
    assert "name: demo" in out.read_text(encoding="utf-8")
    fake_wrapper.env_export.assert_called_once_with("demo", from_history=False)


def test_backup_environment_from_history(tmp_path, fake_wrapper):
    out = commands.backup_environment(
        fake_wrapper, "demo", output_dir=tmp_path, from_history=True
    )
    assert out.name.endswith("-history.yml")
    fake_wrapper.env_export.assert_called_once_with("demo", from_history=True)


def test_restore_environment_uses_name_from_yaml(tmp_path, fake_wrapper):
    yml = tmp_path / "demo.yml"
    yml.write_text("name: restored_demo\n", encoding="utf-8")
    name = commands.restore_environment(fake_wrapper, yml)
    assert name == "restored_demo"
    fake_wrapper.env_create_from_file.assert_called_once()


def test_restore_environment_missing_file_raises(tmp_path, fake_wrapper):
    with pytest.raises(errors.CondaHelperError):
        commands.restore_environment(fake_wrapper, tmp_path / "missing.yml")


def test_batch_remove_collects_errors(fake_wrapper):
    fake_wrapper.env_remove.side_effect = [
        CondaResult(0, "", ""),
        errors.CondaError("boom", stderr="nope", hint=""),
    ]
    results = commands.batch_remove(fake_wrapper, ["a", "b"])
    assert results[0]["ok"] is True
    assert results[1]["ok"] is False
    assert "boom" in results[1]["error"]


def test_doctor_flags_missing_conda_pack(monkeypatch, fake_wrapper):
    monkeypatch.setattr("conda_helper.commands.shutil.which", lambda _: None)
    report = commands.doctor(fake_wrapper)
    assert report["ok"] is False
    assert any("conda-pack" in i for i in report["issues"])


def test_pack_fallback_creates_tar(monkeypatch, tmp_path, fake_wrapper):
    monkeypatch.setattr("conda_helper.commands.shutil.which", lambda _: None)
    archive = commands.pack_environment(fake_wrapper, "demo", output_dir=tmp_path)
    assert archive.exists()
    assert archive.suffix == ".gz"


# ---------------------------------------------------------------------- #
# CLI integration (via CliRunner)
# ---------------------------------------------------------------------- #
def _runner_invoke(fake_wrapper, args):
    runner = CliRunner()
    obj = {"wrapper": fake_wrapper}
    return runner.invoke(cli_module.cli, args, obj=obj)


def test_cli_ls_text(fake_wrapper):
    result = _runner_invoke(fake_wrapper, ["ls"])
    assert result.exit_code == 0
    assert "demo" in result.output
    assert "PREFIX" in result.output


def test_cli_ls_json(fake_wrapper):
    result = _runner_invoke(fake_wrapper, ["ls", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert any(e["name"] == "demo" for e in payload)


def test_cli_backup_writes_file(tmp_path, fake_wrapper):
    result = _runner_invoke(
        fake_wrapper, ["backup", "demo", "-o", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert "backup written" in result.output


def test_cli_clone_calls_wrapper(fake_wrapper):
    result = _runner_invoke(fake_wrapper, ["clone", "demo", "demo2"])
    assert result.exit_code == 0
    fake_wrapper.env_clone.assert_called_once_with("demo", "demo2")


def test_cli_rm_requires_confirmation(fake_wrapper):
    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli, ["rm", "demo"], obj={"wrapper": fake_wrapper}, input="n\n"
    )
    # confirm aborts -> exit non-zero
    assert result.exit_code != 0
    fake_wrapper.env_remove.assert_not_called()


def test_cli_rm_with_yes_flag(fake_wrapper):
    result = _runner_invoke(fake_wrapper, ["rm", "demo", "--yes"])
    assert result.exit_code == 0
    fake_wrapper.env_remove.assert_called_once_with("demo")


def test_cli_version_flag():
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["--version"])
    assert result.exit_code == 0
    assert "." in result.output  # something like 0.1.0


def test_cli_short_alias_ls(fake_wrapper):
    result = _runner_invoke(fake_wrapper, ["l"])
    assert result.exit_code == 0
    assert "demo" in result.output


def test_cli_doctor_renders(fake_wrapper, monkeypatch):
    monkeypatch.setattr("conda_helper.commands.shutil.which", lambda _: "/usr/bin/conda-pack")
    result = _runner_invoke(fake_wrapper, ["doctor"])
    assert result.exit_code == 0
    assert "conda 24.0.0" in result.output
    assert "status" in result.output

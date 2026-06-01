"""Interactive panel built on click prompts (no extra dependencies).

A heavier alternative would use ``questionary`` or ``rich``; this version
sticks to the stdlib + click so the package stays light.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from . import commands
from .conda_wrapper import CondaWrapper
from .errors import CondaHelperError, format_error


_MENU = [
    ("List environments", "ls"),
    ("Backup an environment", "backup"),
    ("Restore from YAML", "restore"),
    ("Clone an environment", "clone"),
    ("Pack for offline use", "pack"),
    ("Batch remove environments", "rm"),
    ("Purge caches", "purge"),
    ("Doctor / health check", "doctor"),
    ("Quit", "q"),
]


def run_panel(wrapper: CondaWrapper) -> None:
    while True:
        click.clear()
        click.secho("=== conda-helper panel ===", bold=True, fg="cyan")
        for idx, (label, _) in enumerate(_MENU, start=1):
            click.echo(f"  [{idx}] {label}")
        choice = click.prompt(
            "Select", type=click.IntRange(1, len(_MENU)), default=1
        )
        action = _MENU[choice - 1][1]
        if action == "q":
            click.secho("bye.", fg="cyan")
            return
        try:
            _dispatch(wrapper, action)
        except click.Abort:
            click.secho("aborted.", fg="yellow")
        except CondaHelperError as exc:
            click.secho(format_error(exc), fg="red", err=True)
        click.pause()


def _dispatch(wrapper: CondaWrapper, action: str) -> None:
    if action == "ls":
        envs = commands.list_environments(wrapper)
        click.secho(f"{'NAME':<24} {'SIZE':>10}  PREFIX", bold=True)
        for env in envs:
            click.echo(f"{env['name']:<24} {env['size_human']:>10}  {env['prefix']}")
        return

    if action == "backup":
        name = click.prompt("Environment name")
        from_history = click.confirm("Use --from-history?", default=False)
        path = commands.backup_environment(wrapper, name, from_history=from_history)
        click.secho(f"backup written: {path}", fg="green")
        return

    if action == "restore":
        yaml_path = click.prompt("Path to YAML", type=click.Path(exists=True))
        new_name = click.prompt("New environment name (blank to keep)", default="", show_default=False)
        created = commands.restore_environment(
            wrapper, Path(yaml_path), name=new_name or None
        )
        click.secho(f"restored as: {created}", fg="green")
        return

    if action == "clone":
        src = click.prompt("Source env")
        dst = click.prompt("Destination name")
        commands.clone_environment(wrapper, src, dst)
        click.secho(f"cloned {src} -> {dst}", fg="green")
        return

    if action == "pack":
        name = click.prompt("Environment to pack")
        archive = commands.pack_environment(wrapper, name)
        click.secho(f"archive ready: {archive}", fg="green")
        return

    if action == "rm":
        names_str = click.prompt(
            "Comma-separated env names to remove (irreversible)"
        )
        names = [n.strip() for n in names_str.split(",") if n.strip()]
        if not names:
            return
        click.echo("About to remove: " + ", ".join(names))
        click.confirm("Proceed?", abort=True)
        results = commands.batch_remove(wrapper, names)
        for r in results:
            color = "green" if r["ok"] else "red"
            status = "OK " if r["ok"] else "ERR"
            click.secho(f"[{status}] {r['name']}", fg=color)
        return

    if action == "purge":
        dry = click.confirm("Dry run?", default=True)
        out = commands.purge_caches(wrapper, dry_run=dry)
        click.echo(out)
        return

    if action == "doctor":
        report = commands.doctor(wrapper)
        click.echo(report)
        return

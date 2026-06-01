"""Click-based command line interface for conda-helper."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__, commands
from .conda_wrapper import CondaWrapper
from .errors import CondaHelperError, format_error
from .utils import is_tty, wait_status


# ---------------------------------------------------------------------- #
# helpers
# ---------------------------------------------------------------------- #
def _get_wrapper(ctx: click.Context) -> CondaWrapper:
    """Lazily instantiate :class:`CondaWrapper` and cache it on the context.

    Tests inject a pre-built ``wrapper`` into ``ctx.obj`` so we never
    require a real conda installation at unit-test time.
    """
    wrapper: Optional[CondaWrapper] = ctx.obj.get("wrapper") if ctx.obj else None
    if wrapper is None:
        wrapper = CondaWrapper()
        if ctx.obj is None:
            ctx.obj = {}
        ctx.obj["wrapper"] = wrapper
    return wrapper


def _print_error(exc: BaseException) -> None:
    click.secho(format_error(exc), fg="red", err=True)


# ---------------------------------------------------------------------- #
# root group
# ---------------------------------------------------------------------- #
@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(__version__, "-V", "--version")
@click.option(
    "--conda-bin",
    type=click.Path(dir_okay=False),
    default=None,
    help="Explicit path to the conda executable (overrides auto-discovery).",
)
@click.pass_context
def cli(ctx: click.Context, conda_bin: Optional[str]) -> None:
    """conda-helper — enhanced CLI on top of conda.

    Run `conda-helper panel` for an interactive menu, or `conda-helper -h`
    to list all sub-commands.
    """
    ctx.ensure_object(dict)
    if conda_bin:
        ctx.obj["wrapper"] = CondaWrapper(conda_bin=conda_bin)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------- #
# ls
# ---------------------------------------------------------------------- #
@cli.command("ls", help="List conda environments with on-disk size.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
@click.option(
    "--no-size",
    is_flag=True,
    help="Skip directory size calculation for the fastest environment list.",
)
@click.pass_context
def cmd_ls(ctx: click.Context, as_json: bool, no_size: bool) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status("loading conda environments", enabled=not as_json):
            envs = commands.list_environments(wrapper, include_size=not no_size)
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    if as_json:
        import json as _json
        click.echo(_json.dumps(envs, indent=2))
        return
    click.secho(f"{'NAME':<24} {'SIZE':>10}  PREFIX", bold=True)
    for env in envs:
        click.echo(f"{env['name']:<24} {env['size_human']:>10}  {env['prefix']}")


# ---------------------------------------------------------------------- #
# backup / restore
# ---------------------------------------------------------------------- #
@cli.command("backup", help="Export an environment to a versioned YAML file.")
@click.argument("name")
@click.option(
    "-o", "--output-dir", type=click.Path(file_okay=False),
    default=None, help="Where to write the YAML (default: user backup dir).",
)
@click.option(
    "--from-history", is_flag=True,
    help="Export only explicitly-requested packages (more portable).",
)
@click.pass_context
def cmd_backup(
    ctx: click.Context, name: str, output_dir: Optional[str], from_history: bool
) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status(f"exporting environment {name!r}"):
            path = commands.backup_environment(
                wrapper,
                name,
                output_dir=Path(output_dir) if output_dir else None,
                from_history=from_history,
            )
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    click.secho(f"backup written: {path}", fg="green")


@cli.command("restore", help="Recreate an environment from a backup YAML.")
@click.argument("yaml_path", type=click.Path(exists=True, dir_okay=False))
@click.option("-n", "--name", default=None, help="Override the env name in the YAML.")
@click.pass_context
def cmd_restore(ctx: click.Context, yaml_path: str, name: Optional[str]) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status("creating environment from YAML"):
            created = commands.restore_environment(wrapper, Path(yaml_path), name=name)
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    click.secho(f"environment restored as: {created}", fg="green")


# ---------------------------------------------------------------------- #
# clone / rm / purge
# ---------------------------------------------------------------------- #
@cli.command("clone", help="Clone an environment under a new name.")
@click.argument("src")
@click.argument("dst")
@click.pass_context
def cmd_clone(ctx: click.Context, src: str, dst: str) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status(f"cloning {src!r} to {dst!r}"):
            commands.clone_environment(wrapper, src, dst)
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    click.secho(f"cloned {src} -> {dst}", fg="green")


@cli.command("rm", help="Remove one or more environments (batch).")
@click.argument("names", nargs=-1, required=True)
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_context
def cmd_rm(ctx: click.Context, names: tuple, yes: bool) -> None:
    wrapper = _get_wrapper(ctx)
    if not yes:
        click.echo("About to remove: " + ", ".join(names))
        click.confirm("Proceed?", abort=True)
    with wait_status("removing environments"):
        results = commands.batch_remove(wrapper, names)
    for r in results:
        color = "green" if r["ok"] else "red"
        status = "OK " if r["ok"] else "ERR"
        click.secho(f"[{status}] {r['name']}", fg=color)
        if not r["ok"]:
            click.echo(f"    {r['error']}")


@cli.command("purge", help="Clean conda caches and unused tarballs.")
@click.option("--dry-run", is_flag=True, help="Show what would be removed.")
@click.pass_context
def cmd_purge(ctx: click.Context, dry_run: bool) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status("cleaning conda caches"):
            out = commands.purge_caches(wrapper, dry_run=dry_run)
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    click.echo(out)


# ---------------------------------------------------------------------- #
# pack (offline)
# ---------------------------------------------------------------------- #
@cli.command("pack", help="Bundle an environment into an offline-deployable archive.")
@click.argument("name")
@click.option(
    "-o", "--output-dir", type=click.Path(file_okay=False), default=None,
    help="Where to write the archive (default: user backup dir).",
)
@click.pass_context
def cmd_pack(ctx: click.Context, name: str, output_dir: Optional[str]) -> None:
    wrapper = _get_wrapper(ctx)
    try:
        with wait_status(f"packing environment {name!r}"):
            archive = commands.pack_environment(
                wrapper, name, output_dir=Path(output_dir) if output_dir else None
            )
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)
    click.secho(f"archive ready: {archive}", fg="green")


# ---------------------------------------------------------------------- #
# doctor
# ---------------------------------------------------------------------- #
@cli.command("doctor", help="Run a health check and report issues.")
@click.pass_context
def cmd_doctor(ctx: click.Context) -> None:
    wrapper = _get_wrapper(ctx)
    with wait_status("checking conda health"):
        report = commands.doctor(wrapper)
    info = report["info"]
    click.secho(
        f"conda {info.get('conda_version')} on {info.get('platform')}",
        bold=True,
    )
    click.echo(f"root prefix : {info.get('root_prefix')}")
    click.echo(f"channels    : {', '.join(info.get('channels', []))}")
    if report["ok"]:
        click.secho("status      : OK", fg="green")
    else:
        click.secho("status      : ISSUES FOUND", fg="yellow")
        for issue in report["issues"]:
            click.secho(f"  - {issue}", fg="yellow")


# ---------------------------------------------------------------------- #
# panel (interactive)
# ---------------------------------------------------------------------- #
@cli.command("panel", help="Interactive menu (TTY only).")
@click.pass_context
def cmd_panel(ctx: click.Context) -> None:
    if not is_tty():
        click.secho("panel requires an interactive terminal.", fg="red", err=True)
        sys.exit(2)
    from .panel import run_panel
    run_panel(_get_wrapper(ctx))


# ---------------------------------------------------------------------- #
# short aliases
# ---------------------------------------------------------------------- #
# Keep duplicates light: register the same callbacks under short names.
cli.add_command(cmd_ls, name="l")
cli.add_command(cmd_backup, name="b")
cli.add_command(cmd_restore, name="r")
cli.add_command(cmd_clone, name="c")
cli.add_command(cmd_purge, name="p")
cli.add_command(cmd_pack, name="pk")


def main() -> None:  # pragma: no cover - entry point
    try:
        cli(prog_name="conda-helper")
    except CondaHelperError as exc:
        _print_error(exc)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

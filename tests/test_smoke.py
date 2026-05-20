from typer.testing import CliRunner

from tinker import __version__
from tinker.cli import app

runner = CliRunner()


def test_version_constant_format() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts)


def test_cli_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tinker" in result.stdout.lower()


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout

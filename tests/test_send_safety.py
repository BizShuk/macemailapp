import pytest

from click.testing import CliRunner
from macmailapp import MailApp
from macmailapp.cli.cli import cli
from macmailapp.script_loader import run_script


def test_send_now_rejects_zero_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(0)


def test_send_now_rejects_negative_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(-5)


def test_sendDraft_handler_exists():
    # We never actually send during tests. We assert the handler is callable
    # by passing an invalid id and expecting a known error string.
    with pytest.raises(Exception) as exc:
        run_script("sendDraft", -1)
    msg = str(exc.value)
    assert "sendDraft" not in msg or "doesn't understand" not in msg


def test_cli_send_default_is_dry_run():
    app = MailApp()
    if not app.accounts:
        return
    result = CliRunner().invoke(cli, [
        "send",
        "--to", "plan-test@example.invalid",
        "--subject", "would never actually go out",
        "--body", "dry run",
        "--from-account", app.accounts[0],
    ])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output


def test_cli_send_without_yes_aborts_when_not_dry_run():
    app = MailApp()
    if not app.accounts:
        return
    result = CliRunner().invoke(cli, [
        "send",
        "--to", "plan-test@example.invalid",
        "--subject", "no yes flag",
        "--body", "should abort",
        "--from-account", app.accounts[0],
        "--no-dry-run",
    ])
    assert result.exit_code != 0
    assert "--yes" in result.output
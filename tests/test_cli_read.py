from click.testing import CliRunner
from macmailapp.cli.cli import cli


def test_cli_accounts_runs_without_error():
    result = CliRunner().invoke(cli, ["accounts"])
    assert result.exit_code == 0


def test_cli_accounts_json_flag_returns_valid_json():
    import json
    result = CliRunner().invoke(cli, ["accounts", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_cli_mailboxes_for_first_account():
    import json
    from macmailapp import MailApp
    acct = MailApp().accounts[0]
    result = CliRunner().invoke(cli, ["mailboxes", "--account", acct, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
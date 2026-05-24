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


def test_cli_list_messages_with_limit():
    import json
    from macmailapp import MailApp
    acct = MailApp().account(MailApp().accounts[0])
    mbox = acct.mailboxes[0].name
    result = CliRunner().invoke(
        cli,
        ["list", "--account", acct.name, "--mailbox", mbox, "--limit", "3", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) <= 3


def test_cli_show_uses_first_message():
    from macmailapp import MailApp
    acct = MailApp().account(MailApp().accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    result = CliRunner().invoke(
        cli,
        ["show", "--account", acct.name, "--mailbox", mbox.name, "--id", str(msgs[0].id)],
    )
    assert result.exit_code == 0
    assert msgs[0].subject in result.output or msgs[0].sender in result.output
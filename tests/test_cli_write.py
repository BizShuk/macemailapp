from click.testing import CliRunner
from macmailapp.cli.cli import cli
from macmailapp import MailApp


def test_cli_move_round_trip():
    app = MailApp()
    if not app.accounts:
        return
    acct = app.accounts[0]
    boxes = app.account(acct).mailboxes
    if len(boxes) < 2:
        return  # cannot test move with fewer than two mailboxes
    src, dst = boxes[0], boxes[1]
    msgs = src.messages(limit=1)
    if not msgs:
        return
    msg_id = msgs[0].id
    runner = CliRunner()
    r1 = runner.invoke(cli, [
        "move",
        "--account", acct,
        "--mailbox", src.name,
        "--id", str(msg_id),
        "--dest-account", acct,
        "--dest-mailbox", dst.name,
    ])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, [
        "move",
        "--account", acct,
        "--mailbox", dst.name,
        "--id", str(msg_id),
        "--dest-account", acct,
        "--dest-mailbox", src.name,
    ])
    assert r2.exit_code == 0


def test_cli_draft_creates_draft():
    app = MailApp()
    if not app.accounts:
        return
    result = CliRunner().invoke(cli, [
        "draft",
        "--to", "plan-test@example.invalid",
        "--subject", "macmailapp cli draft test",
        "--body", "hello",
        "--from-account", app.accounts[0],
    ])
    assert result.exit_code == 0
    assert "draft saved" in result.output.lower()


def test_cli_mark_read_round_trip():
    app = MailApp()
    if not app.accounts:
        return
    mbox = app.account(app.accounts[0]).mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    m = msgs[0]
    original = m.read
    runner = CliRunner()
    r1 = runner.invoke(cli, [
        "mark",
        "--account", app.accounts[0],
        "--mailbox", mbox.name,
        "--id", str(m.id),
        "--read" if not original else "--unread",
    ])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, [
        "mark",
        "--account", app.accounts[0],
        "--mailbox", mbox.name,
        "--id", str(m.id),
        "--read" if original else "--unread",
    ])
    assert r2.exit_code == 0
import click

from macemailapp import MailApp


@click.command(name="mark")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--read/--unread", default=None, help="Set read status.")
@click.option("--flag/--unflag", default=None, help="Set flagged status.")
def mark(account_name, mailbox_name, msg_id, read, flag):
    """Mark a message read/unread or flagged/unflagged."""
    if read is None and flag is None:
        raise click.UsageError("supply at least one of --read/--unread or --flag/--unflag")
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found")
    if read is not None:
        target.mark_read(read)
    if flag is not None:
        target.mark_flagged(flag)
    click.echo(f"updated message {msg_id}")
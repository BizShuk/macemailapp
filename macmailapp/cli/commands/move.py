import click

from macmailapp import MailApp


@click.command(name="move")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--dest-account", required=True)
@click.option("--dest-mailbox", required=True)
def move(account_name, mailbox_name, msg_id, dest_account, dest_mailbox):
    """Move a message to another mailbox (possibly in another account)."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found")
    target.move_to(dest_account, dest_mailbox)
    click.echo(f"moved {msg_id} -> {dest_account}/{dest_mailbox}")
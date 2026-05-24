import click
from rich.console import Console
from rich.panel import Panel

from macemailapp import MailApp


@click.command(name="show")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--source", is_flag=True, help="Show RFC822 source instead of content.")
def show(account_name, mailbox_name, msg_id, source):
    """Show a single message's content."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found in {account_name}/{mailbox_name}")
    body = target.source if source else target.content
    header = (
        f"From: {target.sender}\n"
        f"Subject: {target.subject}\n"
        f"Date: {target.date_received}"
    )
    Console().print(Panel(body, title=header))
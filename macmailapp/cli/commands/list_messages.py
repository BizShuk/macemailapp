import json as _json

import click
from rich.console import Console
from rich.table import Table

from macmailapp import MailApp


@click.command(name="list")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--subject", "-s", default=None, help="Substring filter on subject.")
@click.option("--from", "-f", "sender", default=None, help="Substring filter on sender.")
@click.option("--unread", is_flag=True, help="Only unread messages.")
@click.option("--flagged", is_flag=True, help="Only flagged messages.")
@click.option("--limit", type=int, default=20, help="Max rows to return.")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def list_messages(account_name, mailbox_name, subject, sender, unread, flagged, limit, as_json):
    """List messages in a mailbox with optional filters."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    msgs = mbox.messages(
        subject=subject,
        sender=sender,
        unread_only=unread,
        flagged_only=flagged,
        limit=limit,
    )
    rows = [
        {
            "id": m.id,
            "subject": m.subject,
            "sender": m.sender,
            "date_received": m.date_received.isoformat() if m.date_received else None,
            "read": m.read,
            "flagged": m.flagged,
        }
        for m in msgs
    ]
    if as_json:
        click.echo(_json.dumps(rows))
        return
    table = Table(title=f"{account_name}/{mailbox_name}")
    table.add_column("ID")
    table.add_column("Date")
    table.add_column("From")
    table.add_column("Subject")
    for r in rows:
        table.add_row(str(r["id"]), str(r["date_received"] or ""), r["sender"], r["subject"])
    Console().print(table)
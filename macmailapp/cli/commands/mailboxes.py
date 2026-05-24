import json as _json

import click
from rich.console import Console
from rich.table import Table

from macmailapp import MailApp


@click.command(name="mailboxes")
@click.option("--account", "-a", "account_name", required=True, help="Account name.")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def mailboxes(account_name: str, as_json: bool):
    """List mailboxes (folders) inside an account."""
    acct = MailApp().account(account_name)
    rows = [{"name": m.name, "count": m.count} for m in acct.mailboxes]
    if as_json:
        click.echo(_json.dumps(rows))
        return
    table = Table(title=f"Mailboxes in {account_name}")
    table.add_column("Name")
    table.add_column("Count", justify="right")
    for r in rows:
        table.add_row(r["name"], str(r["count"]))
    Console().print(table)
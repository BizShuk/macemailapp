import json as _json

import click
from rich.console import Console

from macemailapp import MailApp


@click.command(name="accounts")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def accounts(as_json: bool):
    """List Mail accounts."""
    names = MailApp().accounts
    if as_json:
        click.echo(_json.dumps(names))
    else:
        console = Console()
        for n in names:
            console.print(n)
import click
from rich.console import Console
from rich.panel import Panel

from macmailapp import MailApp


@click.command(name="send")
@click.option("--to", required=True)
@click.option("--subject", required=True)
@click.option("--body", required=True)
@click.option("--from-account", "from_account", required=True)
@click.option("--dry-run/--no-dry-run", default=True, help="Default is dry-run (preview only).")
@click.option("--yes", is_flag=True, default=False, help="Required to actually send.")
def send(to, subject, body, from_account, dry_run, yes):
    """Send a message. Default is dry-run; --no-dry-run --yes required to actually send."""
    console = Console()
    preview = (
        f"From: {from_account}\nTo: {to}\nSubject: {subject}\n\n{body}"
    )
    if dry_run:
        console.print(Panel(preview, title="DRY RUN — message NOT sent"))
        return
    if not yes:
        raise click.ClickException(
            "refusing to send without --yes (combine with --no-dry-run --yes to send)"
        )
    app = MailApp()
    draft_id = app.make_draft(to=to, subject=subject, body=body, from_account=from_account)
    sent_id = app.send_now(draft_id)
    console.print(Panel(preview, title=f"SENT (id={sent_id})"))
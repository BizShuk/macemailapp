import click

from macmailapp import MailApp


@click.command(name="draft")
@click.option("--to", required=True, help="Recipient email address.")
@click.option("--subject", required=True)
@click.option("--body", required=True)
@click.option("--from-account", "from_account", required=True, help="Sending account name.")
def draft(to, subject, body, from_account):
    """Compose a draft (saved to Drafts; not sent)."""
    new_id = MailApp().make_draft(to=to, subject=subject, body=body, from_account=from_account)
    click.echo(f"draft saved (id={new_id})")
import click

from macmailapp import __version__
from .commands.accounts import accounts
from .commands.mailboxes import mailboxes


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
cli.add_command(mailboxes)
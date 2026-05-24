import click

from macmailapp import __version__
from .commands.accounts import accounts


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
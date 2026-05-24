"""macmailapp CLI entry point."""

import click


@click.group()
def cli_main():
    """macmailapp - CLI for Apple Mail.app"""
    pass


if __name__ == "__main__":
    cli_main()
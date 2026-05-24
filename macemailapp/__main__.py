"""macemailapp CLI entry point."""

from .cli.cli import cli


def cli_main():
    cli()


if __name__ == "__main__":
    cli_main()
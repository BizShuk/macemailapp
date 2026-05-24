import click
from rich.console import Console


class RichHelpCommand(click.Command):
    def format_help(self, ctx, formatter):
        Console().print(f"[bold]{self.name}[/bold] — {self.help or ''}")
        super().format_help(ctx, formatter)
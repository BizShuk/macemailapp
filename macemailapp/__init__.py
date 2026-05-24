"""macemailapp - CLI tool and Python library for interacting with Apple Mail.app on macOS."""

from macemailapp._version import __version__
from macemailapp.mailapp import MailApp, Account, Mailbox, Message

__all__ = ["MailApp", "Account", "Mailbox", "Message", "__version__"]
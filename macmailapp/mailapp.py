"""Python interface to macOS Mail.app."""

from __future__ import annotations

import re
from datetime import datetime
from functools import cached_property
from typing import Generator, Optional

import AppKit
import ScriptingBridge

from ._version import __version__
from .script_loader import run_script
from .utils import NSDate_to_datetime, get_macos_version

MAC_OS_VERSION = int(get_macos_version()[0])


class AppleScriptError(Exception):
    pass


class ScriptingBridgeError(Exception):
    pass


def parse_id_from_object(obj) -> int | None:
    """Pull a numeric message id out of an SBObject string repr when needed.

    Mail's SBObject string repr looks like:
      <SBObject @0x...: <class ''> id 12345 of application "Mail" (PID)>
    """
    if match := re.search(r'id (\d+) of application "Mail"', str(obj)):
        return int(match[1])
    return None


class MailApp:
    """Represents a running Mail.app instance via ScriptingBridge."""

    def __init__(self):
        self._app = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_(
            "com.apple.mail"
        )

    @property
    def app(self):
        return self._app

    @property
    def version(self) -> str:
        return str(self._app.version())

    @property
    def accounts(self) -> list[str]:
        return [str(a.name()) for a in self._app.accounts()]

    def account(self, name: Optional[str] = None) -> "Account":
        if name is None:
            raise ValueError("account name is required")
        predicate = AppKit.NSPredicate.predicateWithFormat_("name == %@", name)
        matches = self._app.accounts().filteredArrayUsingPredicate_(predicate)
        if not matches:
            raise ValueError(f"Could not find account {name!r}")
        return Account(matches[0])

    def activate(self) -> None:
        run_script("mailActivate")

    def quit(self) -> None:
        run_script("mailQuit")

    def __iter__(self) -> Generator["Account", None, None]:
        for a in self._app.accounts():
            yield Account(a)


class Account:
    """Stub — fleshed out in Task 5."""

    def __init__(self, sb_account):
        self._account = sb_account

    @property
    def name(self) -> str:
        return str(self._account.name())


class Mailbox:
    """Stub — implemented in Task 6."""

    def __init__(self, sb_mailbox, account_name: str):
        self._mailbox = sb_mailbox
        self._account_name = account_name


class Message:
    """Stub — implemented in Task 7."""

    def __init__(self, sb_message, account_name: str, mailbox_name: str):
        self._message = sb_message
        self._account_name = account_name
        self._mailbox_name = mailbox_name
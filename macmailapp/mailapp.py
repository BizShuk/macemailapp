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
    """A Mail account (iCloud, Gmail, IMAP, etc.)."""

    def __init__(self, sb_account):
        self._account = sb_account

    @property
    def name(self) -> str:
        return str(self._account.name())

    @property
    def id(self) -> str:
        return str(self._account.id())

    @cached_property
    def mailboxes(self) -> list["Mailbox"]:
        return [Mailbox(m, self.name) for m in self._account.mailboxes()]

    def mailbox(self, name: str) -> "Mailbox":
        for m in self.mailboxes:
            if m.name == name:
                return m
        raise ValueError(f"Mailbox {name!r} not found in account {self.name!r}")

    def __repr__(self) -> str:
        return f"Account(name={self.name!r})"


class Mailbox:
    """A mailbox (folder) inside a Mail account."""

    def __init__(self, sb_mailbox, account_name: str):
        self._mailbox = sb_mailbox
        self._account_name = account_name

    @property
    def name(self) -> str:
        return str(self._mailbox.name())

    @property
    def account_name(self) -> str:
        return self._account_name

    @property
    def count(self) -> int:
        return int(self._mailbox.messages().count())

    def messages(
        self,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        unread_only: bool = False,
        flagged_only: bool = False,
        limit: Optional[int] = None,
    ) -> list["Message"]:
        predicates = []
        if subject:
            predicates.append(("subject CONTAINS[cd] %@", subject))
        if sender:
            predicates.append(("sender CONTAINS[cd] %@", sender))
        if unread_only:
            predicates.append(("readStatus == NO", None))
        if flagged_only:
            predicates.append(("flaggedStatus == YES", None))

        msgs = self._mailbox.messages()
        if predicates:
            fmt = " AND ".join(p[0] for p in predicates)
            args = [p[1] for p in predicates if p[1] is not None]
            predicate = AppKit.NSPredicate.predicateWithFormat_(fmt, *args)
            msgs = msgs.filteredArrayUsingPredicate_(predicate)

        result = [Message(m, self._account_name, self.name) for m in msgs]
        if limit is not None:
            result = result[:limit]
        return result

    def __repr__(self) -> str:
        return f"Mailbox(name={self.name!r}, account={self._account_name!r})"


class Message:
    """A single email message inside a Mailbox."""

    def __init__(self, sb_message, account_name: str, mailbox_name: str):
        self._message = sb_message
        self._account_name = account_name
        self._mailbox_name = mailbox_name

    @property
    def id(self) -> int:
        raw = self._message.id()
        if raw == 0 or raw is None:
            parsed = parse_id_from_object(self._message)
            if parsed is None:
                raise ScriptingBridgeError("could not resolve message id")
            return parsed
        return int(raw)

    @property
    def subject(self) -> str:
        return str(self._message.subject() or "")

    @property
    def sender(self) -> str:
        return str(self._message.sender() or "")

    @property
    def content(self) -> str:
        return str(self._message.content() or "")

    @property
    def source(self) -> str:
        return str(self._message.source() or "")

    @property
    def date_received(self) -> datetime:
        return NSDate_to_datetime(self._message.dateReceived())

    @property
    def date_sent(self) -> datetime:
        return NSDate_to_datetime(self._message.dateSent())

    @property
    def read(self) -> bool:
        return bool(self._message.readStatus())

    @property
    def flagged(self) -> bool:
        return bool(self._message.flaggedStatus())

    @property
    def account_name(self) -> str:
        return self._account_name

    @property
    def mailbox_name(self) -> str:
        return self._mailbox_name

    def __repr__(self) -> str:
        return (
            f"Message(id={self.id}, subject={self.subject!r}, "
            f"sender={self.sender!r}, mailbox={self._mailbox_name!r})"
        )
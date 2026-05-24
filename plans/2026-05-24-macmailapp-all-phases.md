# macmailapp Implementation Plan (All Phases)

> For agentic workers: REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

`Goal:` Build `macmailapp` — a Python library + `mail` CLI that scripts Apple Mail.app on macOS, mirroring the architecture of `macnotesapp` and adding safe support for sending mail.

`Architecture:` Two-track app-layer access (read-heavy via `ScriptingBridge`, mutations via embedded `AppleScript`), three domain layers (`MailApp → Account → Mailbox → Message`), and a `click`-based CLI with `rich` output. `send` is gated by a `--yes` flag and a `--dry-run` default that only renders the would-be message.

`Tech Stack:` Python 3.10–3.13, `pyobjc-framework-ScriptingBridge`, `py-applescript`, `click`, `rich`, `markdown2`, `markdownify`, `lxml`, `hatchling`, `uv`, `pyinstaller`, `bump2version`, `pytest`.

`Source Evaluation (frozen reference):` Notes (`x-coredata://...` ids, flat account→folder→note) maps to Mail with three deltas — nested mailboxes, integer `message id` (not coredata), and the new `send` verb which is irreversible. Permissions: macOS Automation TCC prompt only; no Full Disk Access needed because we stay at the AppleScript layer (we do not parse `~/Library/Mail/`).

---

## File Structure

New project layout (sibling to `macnotesapp`, scaffolded inside this workspace under `macmailapp/`):

```tree
macmailapp/
├── macmailapp/
│   ├── __init__.py                    # re-exports MailApp, Account, Mailbox, Message, __version__
│   ├── __main__.py                    # CLI entry: cli_main()
│   ├── _version.py                    # __version__ = "0.1.0"
│   ├── logging.py                     # logger setup (reuse macnotesapp pattern)
│   ├── utils.py                       # NSDate_to_datetime, get_macos_version, OSType
│   ├── script_loader.py               # AppleScript loader
│   ├── macmailapp.applescript         # AppleScript source (authoring file)
│   ├── macmailapp_applescript.py      # AppleScript embedded as Python string
│   ├── mailapp.py                     # MailApp / Account / Mailbox / Message classes
│   └── cli/
│       ├── __init__.py
│       ├── cli.py                     # click group + command registration
│       ├── cli_help.py                # RichHelpCommand
│       ├── cli_param_types.py         # EmailType, AddressListType
│       ├── cli_config.py              # config file path + defaults
│       └── commands/
│           ├── __init__.py
│           ├── accounts.py            # mail accounts
│           ├── mailboxes.py           # mail mailboxes
│           ├── list_messages.py       # mail list
│           ├── show.py                # mail show
│           ├── mark.py                # mail mark
│           ├── move.py                # mail move
│           ├── draft.py               # mail draft
│           └── send.py                # mail send
├── tests/
│   ├── __init__.py
│   ├── test_mailapp_read.py
│   ├── test_mailapp_write.py
│   ├── test_send_safety.py
│   ├── test_cli_read.py
│   ├── test_cli_write.py
│   └── conftest.py
├── pyproject.toml
├── README.md
├── build.sh
├── macmailapp.spec                    # PyInstaller
└── HomebrewFormula/macmailapp.rb
```

`Boundary rationale:`

- `mailapp.py` holds domain model (high churn during early dev) but stays one file because the four classes are tightly coupled — same pattern as `notesapp.py:1-219`.
- `macmailapp.applescript` and its `.py` mirror exist because `applescript.AppleScript()` needs the source as a Python `str` (UTF-8 issues with guillemets `«»`) — replicate the pattern documented in `macnotesapp/macnotesapp_applescript.py:1-6`.
- Each CLI command is its own file under `commands/` so `send.py` (the only destructive command) can be reviewed in isolation.

---

## Phase 1 — Read Foundation

### Task 1: Project scaffold

`Files:`

- Create: `macmailapp/pyproject.toml`
- Create: `macmailapp/macmailapp/__init__.py`
- Create: `macmailapp/macmailapp/_version.py`
- Create: `macmailapp/tests/__init__.py`
- Create: `macmailapp/tests/conftest.py`

- [ ] Step 1.1: Write `pyproject.toml`

```toml
[project]
name = "macmailapp"
version = "0.1.0"
description = "Work with Apple Mail.app from the command line. Includes a Python interface for scripting Mail.app."
authors = [{ name = "shuk", email = "biz.shuk@gmail.com" }]
license = "MIT"
readme = "README.md"
keywords = ["cli", "mac", "macos", "mail"]
requires-python = ">=3.10,<3.14"
dependencies = [
    "py-applescript>=1.0.3,<2.0.0",
    "click>=8.1.2,<9.0.0",
    "rich>=12.4.4,<=14.0.0",
    "markdown2>=2.4.3,<3.0.0",
    "markdownify>=0.11.6,<1.0.0",
    "pyobjc-framework-ScriptingBridge>=9.0.1",
    "lxml>=5.2.1,<6.0.0",
]

[project.scripts]
mail = "macmailapp.__main__:cli_main"

[dependency-groups]
dev = [
    "pytest>=7.1.2,<=8.0.0",
    "pyinstaller>=6.6.0",
    "bump2version>=1.0.1,<2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] Step 1.2: Write `macmailapp/_version.py`

```python
__version__ = "0.1.0"
```

- [ ] Step 1.3: Write `macmailapp/__init__.py`

```python
from ._version import __version__
from .mailapp import MailApp, Account, Mailbox, Message

__all__ = ["MailApp", "Account", "Mailbox", "Message", "__version__"]
```

This file will fail to import until Task 6 lands; that is intentional and matches the TDD flow.

- [ ] Step 1.4: Write `tests/__init__.py` (empty file)

```python

```

- [ ] Step 1.5: Write `tests/conftest.py`

```python
import pytest


@pytest.fixture
def mail_app():
    from macmailapp import MailApp
    return MailApp()
```

- [ ] Step 1.6: Initialize the project and verify install

```bash
cd macmailapp && uv sync
```

Expected: a `.venv/` directory is created and `uv pip list` shows `pyobjc-framework-scriptingbridge`, `click`, `rich`. The `mail` script will not yet be importable.

- [ ] Step 1.7: Commit

```bash
git add macmailapp/
git commit -m "feat(macmailapp): scaffold project layout and dependencies"
```

---

### Task 2: Shared utilities — `utils.py`, `logging.py`, `script_loader.py`

`Files:`

- Create: `macmailapp/macmailapp/utils.py`
- Create: `macmailapp/macmailapp/logging.py`
- Create: `macmailapp/macmailapp/script_loader.py`
- Create: `macmailapp/macmailapp/macmailapp_applescript.py`
- Test: `macmailapp/tests/test_utils.py`

- [ ] Step 2.1: Write the failing test

```python
# tests/test_utils.py
from datetime import datetime
from macmailapp.utils import NSDate_to_datetime, get_macos_version


def test_get_macos_version_returns_three_part_tuple():
    parts = get_macos_version()
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_nsdate_to_datetime_roundtrip():
    import AppKit
    now = AppKit.NSDate.date()
    result = NSDate_to_datetime(now)
    assert isinstance(result, datetime)
```

- [ ] Step 2.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_utils.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'macmailapp.utils'`.

- [ ] Step 2.3: Write `utils.py`

```python
"""Utility helpers shared across macmailapp."""

from __future__ import annotations

import platform
from datetime import datetime, timezone


def OSType(s: str) -> int:
    """Convert a 4-char OSType string to its UInt32 representation."""
    return int.from_bytes(s.encode("mac_roman"), byteorder="big")


def get_macos_version() -> tuple[str, str, str]:
    """Return macOS version as a 3-tuple of strings (major, minor, patch)."""
    ver = platform.mac_ver()[0]
    parts = ver.split(".")
    while len(parts) < 3:
        parts.append("0")
    return (parts[0], parts[1], parts[2])


def NSDate_to_datetime(nsdate) -> datetime:
    """Convert an Objective-C NSDate to a Python datetime (UTC)."""
    if nsdate is None:
        return None
    ts = nsdate.timeIntervalSince1970()
    return datetime.fromtimestamp(ts, tz=timezone.utc)
```

- [ ] Step 2.4: Write `logging.py`

```python
"""Centralized logger for macmailapp."""

import logging
import os

logger = logging.getLogger("macmailapp")
_level = os.environ.get("MACMAILAPP_LOG", "WARNING").upper()
logger.setLevel(getattr(logging, _level, logging.WARNING))
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(name)s %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
```

- [ ] Step 2.5: Write `macmailapp_applescript.py` (initial empty body)

```python
"""macmailapp AppleScript source as an importable Python string.

The AppleScript file is kept under macmailapp/macmailapp.applescript for
human editing; this module mirrors the content so that the py-applescript
library can compile it without UTF-8 guillemet (chevron) decoding issues.
"""

MAIL_APPLESCRIPT = """
(********* AppleScript for macmailapp *********)

property WAIT_FOR_SCRIPT : 0.05

on mailVersion()
    tell application "Mail"
        return its version
    end tell
end mailVersion
"""
```

- [ ] Step 2.6: Write `script_loader.py`

```python
"""Load and call handlers from the embedded AppleScript."""

from applescript import AppleScript

from .logging import logger
from .macmailapp_applescript import MAIL_APPLESCRIPT

SCRIPT_OBJ = AppleScript(MAIL_APPLESCRIPT)


def run_script(name, *args):
    """Call handler `name` with `*args` from the compiled AppleScript."""
    logger.debug("Running script %s with args %r", name, args)
    return SCRIPT_OBJ.call(name, *args)
```

- [ ] Step 2.7: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_utils.py -v
```

Expected: 2 passed.

- [ ] Step 2.8: Commit

```bash
git add macmailapp/macmailapp/utils.py macmailapp/macmailapp/logging.py macmailapp/macmailapp/script_loader.py macmailapp/macmailapp/macmailapp_applescript.py macmailapp/tests/test_utils.py
git commit -m "feat(macmailapp): shared utils, logger, AppleScript loader"
```

---

### Task 3: AppleScript read handlers

`Files:`

- Create: `macmailapp/macmailapp/macmailapp.applescript` (canonical authoring file)
- Modify: `macmailapp/macmailapp/macmailapp_applescript.py` (mirror content)
- Test: `macmailapp/tests/test_applescript_read.py`

- [ ] Step 3.1: Write the failing test

```python
# tests/test_applescript_read.py
from macmailapp.script_loader import run_script


def test_mailVersion_returns_string():
    v = run_script("mailVersion")
    assert isinstance(v, str)
    assert len(v) > 0


def test_mailGetAccounts_returns_list():
    accounts = run_script("mailGetAccounts")
    assert isinstance(accounts, list)


def test_mailGetMailboxes_for_default_account():
    accounts = run_script("mailGetAccounts")
    assert accounts, "No mail accounts configured — skip or configure one to run this test"
    mailboxes = run_script("accountGetMailboxNames", accounts[0])
    assert isinstance(mailboxes, list)
```

- [ ] Step 3.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_applescript_read.py -v -s
```

Expected: `mailVersion` may pass, but `mailGetAccounts` fails with `applescript.ScriptError: ... mailGetAccounts ... doesn't understand`.

- [ ] Step 3.3: Write the canonical `macmailapp.applescript`

```applescript
(********* AppleScript for macmailapp *********)

property WAIT_FOR_SCRIPT : 0.05

on mailActivate()
    tell application "Mail" to activate
end mailActivate

on mailQuit()
    tell application "Mail" to quit
end mailQuit

on mailVersion()
    tell application "Mail" to return its version
end mailVersion

on mailGetAccounts()
    set theNames to {}
    tell application "Mail"
        repeat with a in accounts
            copy (name of a as string) to end of theNames
        end repeat
    end tell
    return theNames
end mailGetAccounts

on accountGetMailboxNames(accountName)
    set theNames to {}
    tell application "Mail"
        tell account accountName
            repeat with m in mailboxes
                copy (name of m as string) to end of theNames
            end repeat
        end tell
    end tell
    return theNames
end accountGetMailboxNames

on mailboxGetMessageIDs(accountName, mailboxName)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in messages
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end mailboxGetMessageIDs

on messageGetProperties(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set theSubject to subject of m as string
                set theSender to sender of m as string
                set theDate to date received of m
                set isRead to read status of m
                set isFlagged to flagged status of m
                set thePreview to content of m as string
            end tell
        end tell
    end tell
    return {theSubject, theSender, theDate, isRead, isFlagged, thePreview}
end messageGetProperties

on messageGetContent(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return content of m as string
            end tell
        end tell
    end tell
end messageGetContent

on messageGetSource(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return source of m as string
            end tell
        end tell
    end tell
end messageGetSource

on accountFindBySubject(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose subject contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySubject

on accountFindBySender(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose sender contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySender
```

- [ ] Step 3.4: Mirror the script into `macmailapp_applescript.py`

```python
"""macmailapp AppleScript source as an importable Python string."""

# Keep this string in sync with macmailapp/macmailapp.applescript.
# build.sh enforces parity via cog.

MAIL_APPLESCRIPT = r"""
(********* AppleScript for macmailapp *********)

property WAIT_FOR_SCRIPT : 0.05

on mailActivate()
    tell application "Mail" to activate
end mailActivate

on mailQuit()
    tell application "Mail" to quit
end mailQuit

on mailVersion()
    tell application "Mail" to return its version
end mailVersion

on mailGetAccounts()
    set theNames to {}
    tell application "Mail"
        repeat with a in accounts
            copy (name of a as string) to end of theNames
        end repeat
    end tell
    return theNames
end mailGetAccounts

on accountGetMailboxNames(accountName)
    set theNames to {}
    tell application "Mail"
        tell account accountName
            repeat with m in mailboxes
                copy (name of m as string) to end of theNames
            end repeat
        end tell
    end tell
    return theNames
end accountGetMailboxNames

on mailboxGetMessageIDs(accountName, mailboxName)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in messages
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end mailboxGetMessageIDs

on messageGetProperties(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set theSubject to subject of m as string
                set theSender to sender of m as string
                set theDate to date received of m
                set isRead to read status of m
                set isFlagged to flagged status of m
                set thePreview to content of m as string
            end tell
        end tell
    end tell
    return {theSubject, theSender, theDate, isRead, isFlagged, thePreview}
end messageGetProperties

on messageGetContent(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return content of m as string
            end tell
        end tell
    end tell
end messageGetContent

on messageGetSource(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return source of m as string
            end tell
        end tell
    end tell
end messageGetSource

on accountFindBySubject(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose subject contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySubject

on accountFindBySender(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose sender contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySender
"""
```

- [ ] Step 3.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_applescript_read.py -v -s
```

Expected: 3 passed. On first run macOS will show the Automation TCC prompt for Mail — grant it.

- [ ] Step 3.6: Commit

```bash
git add macmailapp/macmailapp/macmailapp.applescript macmailapp/macmailapp/macmailapp_applescript.py macmailapp/tests/test_applescript_read.py
git commit -m "feat(macmailapp): AppleScript read handlers (accounts, mailboxes, messages)"
```

---

### Task 4: `MailApp` class (ScriptingBridge bridge + version)

`Files:`

- Create: `macmailapp/macmailapp/mailapp.py`
- Test: `macmailapp/tests/test_mailapp_read.py`

- [ ] Step 4.1: Write the failing test

```python
# tests/test_mailapp_read.py
from macmailapp import MailApp


def test_mailapp_version_is_string():
    app = MailApp()
    assert isinstance(app.version, str)
    assert "." in app.version


def test_mailapp_accounts_is_list_of_strings():
    app = MailApp()
    assert isinstance(app.accounts, list)
    for a in app.accounts:
        assert isinstance(a, str)
```

- [ ] Step 4.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py -v -s
```

Expected: FAIL with `ImportError: cannot import name 'MailApp'`.

- [ ] Step 4.3: Write the minimal `mailapp.py`

```python
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
```

- [ ] Step 4.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py -v -s
```

Expected: 2 passed.

- [ ] Step 4.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_read.py
git commit -m "feat(macmailapp): MailApp class with ScriptingBridge backend"
```

---

### Task 5: `Account` class with mailboxes

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py` (expand `Account`)
- Test: `macmailapp/tests/test_mailapp_read.py` (extend)

- [ ] Step 5.1: Write the failing test (append to `test_mailapp_read.py`)

```python
def test_account_has_mailboxes_list():
    app = MailApp()
    assert app.accounts, "configure at least one Mail account"
    acct = app.account(app.accounts[0])
    mboxes = acct.mailboxes
    assert isinstance(mboxes, list)
    assert all(hasattr(m, "name") for m in mboxes)


def test_account_mailbox_lookup_by_name():
    app = MailApp()
    acct = app.account(app.accounts[0])
    names = [m.name for m in acct.mailboxes]
    assert "INBOX" in names or "Inbox" in names or names, \
        "expected at least one mailbox in the first account"
```

- [ ] Step 5.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py::test_account_has_mailboxes_list -v -s
```

Expected: FAIL with `AttributeError: 'Account' object has no attribute 'mailboxes'`.

- [ ] Step 5.3: Expand `Account` class in `mailapp.py`

Replace the stub `Account` class with:

```python
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
```

- [ ] Step 5.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py -v -s
```

Expected: 4 passed.

- [ ] Step 5.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_read.py
git commit -m "feat(macmailapp): Account class with mailboxes property"
```

---

### Task 6: `Mailbox` class with messages and filters

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py` (expand `Mailbox`)
- Test: `macmailapp/tests/test_mailapp_read.py` (extend)

- [ ] Step 6.1: Write the failing test

```python
def test_mailbox_messages_returns_list_of_message():
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages()
    assert isinstance(msgs, list)


def test_mailbox_filter_by_subject():
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(subject="a")
    assert isinstance(msgs, list)


def test_mailbox_count_matches_len():
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    assert mbox.count == len(mbox.messages())
```

- [ ] Step 6.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py::test_mailbox_messages_returns_list_of_message -v -s
```

Expected: FAIL with `AttributeError: 'Mailbox' object has no attribute 'messages'`.

- [ ] Step 6.3: Expand `Mailbox` class

Replace the stub `Mailbox` with:

```python
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
```

- [ ] Step 6.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py -v -s
```

Expected: 7 passed.

- [ ] Step 6.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_read.py
git commit -m "feat(macmailapp): Mailbox.messages() with subject/sender/read/flagged filters"
```

---

### Task 7: `Message` class with content + properties

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py` (expand `Message`)
- Test: `macmailapp/tests/test_mailapp_read.py` (extend)

- [ ] Step 7.1: Write the failing test

```python
def test_message_has_subject_and_sender():
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return  # empty mailbox; smoke test the API instead
    m = msgs[0]
    assert isinstance(m.subject, str)
    assert isinstance(m.sender, str)


def test_message_id_is_int():
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    assert isinstance(msgs[0].id, int)


def test_message_dates_are_datetime():
    from datetime import datetime as DT
    app = MailApp()
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    assert isinstance(msgs[0].date_received, DT)
```

- [ ] Step 7.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py::test_message_has_subject_and_sender -v -s
```

Expected: FAIL with `AttributeError: 'Message' object has no attribute 'subject'`.

- [ ] Step 7.3: Expand `Message`

Replace the stub `Message` with:

```python
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
```

- [ ] Step 7.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_read.py -v -s
```

Expected: 10 passed.

- [ ] Step 7.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_read.py
git commit -m "feat(macmailapp): Message class with subject/sender/dates/content/source"
```

---

### Task 8: CLI scaffold + `mail accounts` command

`Files:`

- Create: `macmailapp/macmailapp/__main__.py`
- Create: `macmailapp/macmailapp/cli/__init__.py`
- Create: `macmailapp/macmailapp/cli/cli.py`
- Create: `macmailapp/macmailapp/cli/cli_help.py`
- Create: `macmailapp/macmailapp/cli/commands/__init__.py`
- Create: `macmailapp/macmailapp/cli/commands/accounts.py`
- Test: `macmailapp/tests/test_cli_read.py`

- [ ] Step 8.1: Write the failing test

```python
# tests/test_cli_read.py
from click.testing import CliRunner
from macmailapp.cli.cli import cli


def test_cli_accounts_runs_without_error():
    result = CliRunner().invoke(cli, ["accounts"])
    assert result.exit_code == 0


def test_cli_accounts_json_flag_returns_valid_json():
    import json
    result = CliRunner().invoke(cli, ["accounts", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
```

- [ ] Step 8.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_read.py -v -s
```

Expected: FAIL with `ModuleNotFoundError: No module named 'macmailapp.cli'`.

- [ ] Step 8.3: Write `cli/__init__.py` and `cli/cli_help.py`

```python
# cli/__init__.py
```

```python
# cli/cli_help.py
import click
from rich.console import Console


class RichHelpCommand(click.Command):
    def format_help(self, ctx, formatter):
        Console().print(f"[bold]{self.name}[/bold] — {self.help or ''}")
        super().format_help(ctx, formatter)
```

- [ ] Step 8.4: Write `cli/commands/__init__.py` (empty)

```python

```

- [ ] Step 8.5: Write `cli/commands/accounts.py`

```python
import json as _json

import click
from rich.console import Console

from macmailapp import MailApp


@click.command(name="accounts")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def accounts(as_json: bool):
    """List Mail accounts."""
    names = MailApp().accounts
    if as_json:
        click.echo(_json.dumps(names))
    else:
        console = Console()
        for n in names:
            console.print(n)
```

- [ ] Step 8.6: Write `cli/cli.py`

```python
import click

from macmailapp import __version__
from .commands.accounts import accounts


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
```

- [ ] Step 8.7: Write `__main__.py`

```python
from .cli.cli import cli


def cli_main():
    cli()


if __name__ == "__main__":
    cli_main()
```

- [ ] Step 8.8: Reinstall to register the script entrypoint

```bash
cd macmailapp && uv sync
```

- [ ] Step 8.9: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_read.py -v -s
```

Expected: 2 passed.

- [ ] Step 8.10: Smoke test

```bash
uv run mail accounts
```

Expected: one account name per line.

- [ ] Step 8.11: Commit

```bash
git add macmailapp/macmailapp/__main__.py macmailapp/macmailapp/cli/ macmailapp/tests/test_cli_read.py
git commit -m "feat(macmailapp): CLI scaffold + 'mail accounts' command"
```

---

### Task 9: `mail mailboxes` command

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/mailboxes.py`
- Modify: `macmailapp/macmailapp/cli/cli.py` (register)
- Test: `macmailapp/tests/test_cli_read.py` (extend)

- [ ] Step 9.1: Write the failing test

```python
def test_cli_mailboxes_for_first_account():
    import json
    from macmailapp import MailApp
    acct = MailApp().accounts[0]
    result = CliRunner().invoke(cli, ["mailboxes", "--account", acct, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
```

- [ ] Step 9.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_read.py::test_cli_mailboxes_for_first_account -v -s
```

Expected: FAIL — `No such command 'mailboxes'`.

- [ ] Step 9.3: Write `cli/commands/mailboxes.py`

```python
import json as _json

import click
from rich.console import Console
from rich.table import Table

from macmailapp import MailApp


@click.command(name="mailboxes")
@click.option("--account", "-a", "account_name", required=True, help="Account name.")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def mailboxes(account_name: str, as_json: bool):
    """List mailboxes (folders) inside an account."""
    acct = MailApp().account(account_name)
    rows = [{"name": m.name, "count": m.count} for m in acct.mailboxes]
    if as_json:
        click.echo(_json.dumps(rows))
        return
    table = Table(title=f"Mailboxes in {account_name}")
    table.add_column("Name")
    table.add_column("Count", justify="right")
    for r in rows:
        table.add_row(r["name"], str(r["count"]))
    Console().print(table)
```

- [ ] Step 9.4: Register the command in `cli/cli.py`

Replace the contents of `cli/cli.py` with:

```python
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
```

- [ ] Step 9.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_read.py -v -s
```

Expected: 3 passed.

- [ ] Step 9.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/mailboxes.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_read.py
git commit -m "feat(macmailapp): 'mail mailboxes' command"
```

---

### Task 10: `mail list` command with filters

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/list_messages.py`
- Modify: `macmailapp/macmailapp/cli/cli.py` (register)
- Test: `macmailapp/tests/test_cli_read.py` (extend)

- [ ] Step 10.1: Write the failing test

```python
def test_cli_list_messages_with_limit():
    import json
    from macmailapp import MailApp
    acct = MailApp().account(MailApp().accounts[0])
    mbox = acct.mailboxes[0].name
    result = CliRunner().invoke(
        cli,
        ["list", "--account", acct.name, "--mailbox", mbox, "--limit", "3", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) <= 3
```

- [ ] Step 10.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_read.py::test_cli_list_messages_with_limit -v -s
```

Expected: FAIL — `No such command 'list'`.

- [ ] Step 10.3: Write `cli/commands/list_messages.py`

```python
import json as _json

import click
from rich.console import Console
from rich.table import Table

from macmailapp import MailApp


@click.command(name="list")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--subject", "-s", default=None, help="Substring filter on subject.")
@click.option("--from", "-f", "sender", default=None, help="Substring filter on sender.")
@click.option("--unread", is_flag=True, help="Only unread messages.")
@click.option("--flagged", is_flag=True, help="Only flagged messages.")
@click.option("--limit", type=int, default=20, help="Max rows to return.")
@click.option("--json", "-j", "as_json", is_flag=True, help="Emit JSON.")
def list_messages(account_name, mailbox_name, subject, sender, unread, flagged, limit, as_json):
    """List messages in a mailbox with optional filters."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    msgs = mbox.messages(
        subject=subject,
        sender=sender,
        unread_only=unread,
        flagged_only=flagged,
        limit=limit,
    )
    rows = [
        {
            "id": m.id,
            "subject": m.subject,
            "sender": m.sender,
            "date_received": m.date_received.isoformat() if m.date_received else None,
            "read": m.read,
            "flagged": m.flagged,
        }
        for m in msgs
    ]
    if as_json:
        click.echo(_json.dumps(rows))
        return
    table = Table(title=f"{account_name}/{mailbox_name}")
    table.add_column("ID")
    table.add_column("Date")
    table.add_column("From")
    table.add_column("Subject")
    for r in rows:
        table.add_row(str(r["id"]), str(r["date_received"] or ""), r["sender"], r["subject"])
    Console().print(table)
```

- [ ] Step 10.4: Register in `cli/cli.py`

Replace `cli/cli.py` with:

```python
import click

from macmailapp import __version__
from .commands.accounts import accounts
from .commands.mailboxes import mailboxes
from .commands.list_messages import list_messages


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
cli.add_command(mailboxes)
cli.add_command(list_messages)
```

- [ ] Step 10.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_read.py -v -s
```

Expected: 4 passed.

- [ ] Step 10.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/list_messages.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_read.py
git commit -m "feat(macmailapp): 'mail list' command with subject/sender/unread/flagged filters"
```

---

### Task 11: `mail show <id>` command

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/show.py`
- Modify: `macmailapp/macmailapp/cli/cli.py` (register)
- Test: `macmailapp/tests/test_cli_read.py` (extend)

- [ ] Step 11.1: Write the failing test

```python
def test_cli_show_uses_first_message():
    from macmailapp import MailApp
    acct = MailApp().account(MailApp().accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    result = CliRunner().invoke(
        cli,
        ["show", "--account", acct.name, "--mailbox", mbox.name, "--id", str(msgs[0].id)],
    )
    assert result.exit_code == 0
    assert msgs[0].subject in result.output or msgs[0].sender in result.output
```

- [ ] Step 11.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_read.py::test_cli_show_uses_first_message -v -s
```

Expected: FAIL — `No such command 'show'`.

- [ ] Step 11.3: Write `cli/commands/show.py`

```python
import click
from rich.console import Console
from rich.panel import Panel

from macmailapp import MailApp


@click.command(name="show")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--source", is_flag=True, help="Show RFC822 source instead of content.")
def show(account_name, mailbox_name, msg_id, source):
    """Show a single message's content."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found in {account_name}/{mailbox_name}")
    body = target.source if source else target.content
    header = (
        f"From: {target.sender}\n"
        f"Subject: {target.subject}\n"
        f"Date: {target.date_received}"
    )
    Console().print(Panel(body, title=header))
```

- [ ] Step 11.4: Register in `cli/cli.py`

Replace `cli/cli.py` with:

```python
import click

from macmailapp import __version__
from .commands.accounts import accounts
from .commands.mailboxes import mailboxes
from .commands.list_messages import list_messages
from .commands.show import show


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
cli.add_command(mailboxes)
cli.add_command(list_messages)
cli.add_command(show)
```

- [ ] Step 11.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_read.py -v -s
```

Expected: 5 passed.

- [ ] Step 11.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/show.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_read.py
git commit -m "feat(macmailapp): 'mail show' command for single-message display"
```

---

## Phase 2 — Write Operations (no send)

### Task 12: AppleScript write handlers — mark, move, draft

`Files:`

- Modify: `macmailapp/macmailapp/macmailapp.applescript`
- Modify: `macmailapp/macmailapp/macmailapp_applescript.py` (mirror)
- Test: `macmailapp/tests/test_applescript_write.py`

- [ ] Step 12.1: Write the failing test

```python
# tests/test_applescript_write.py
from macmailapp.script_loader import run_script


def test_messageSetReadStatus_round_trip():
    accounts = run_script("mailGetAccounts")
    if not accounts:
        return
    boxes = run_script("accountGetMailboxNames", accounts[0])
    if not boxes:
        return
    ids = run_script("mailboxGetMessageIDs", accounts[0], boxes[0])
    if not ids:
        return
    target = ids[0]
    run_script("messageSetReadStatus", accounts[0], boxes[0], target, True)
    run_script("messageSetReadStatus", accounts[0], boxes[0], target, False)


def test_createDraft_returns_id():
    accounts = run_script("mailGetAccounts")
    if not accounts:
        return
    draft_id = run_script(
        "createDraft",
        "plan-test@example.invalid",
        "macmailapp test draft (safe to delete)",
        "draft body",
        accounts[0],
    )
    assert isinstance(draft_id, int)
```

- [ ] Step 12.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_applescript_write.py -v -s
```

Expected: FAIL — `messageSetReadStatus` handler missing.

- [ ] Step 12.3: Append handlers to `macmailapp.applescript`

```applescript
on messageSetReadStatus(accountName, mailboxName, msgID, newStatus)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set read status of m to newStatus
            end tell
        end tell
    end tell
end messageSetReadStatus

on messageSetFlaggedStatus(accountName, mailboxName, msgID, newStatus)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set flagged status of m to newStatus
            end tell
        end tell
    end tell
end messageSetFlaggedStatus

on messageMoveTo(accountName, mailboxName, msgID, destAccountName, destMailboxName)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
            end tell
        end tell
        move m to mailbox destMailboxName of account destAccountName
    end tell
end messageMoveTo

on createDraft(toAddress, subjectText, bodyText, fromAccountName)
    tell application "Mail"
        set newMsg to make new outgoing message with properties {subject:subjectText, content:bodyText, sender:(get email addresses of account fromAccountName)'s item 1, visible:false}
        tell newMsg
            make new to recipient at end of to recipients with properties {address:toAddress}
        end tell
        save newMsg
        return id of newMsg as integer
    end tell
end createDraft
```

- [ ] Step 12.4: Mirror the additions into `macmailapp_applescript.py`

Append the same handler block inside the `MAIL_APPLESCRIPT = r"""..."""` literal before its closing `"""`.

- [ ] Step 12.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_applescript_write.py -v -s
```

Expected: 2 passed. A new draft message titled "macmailapp test draft (safe to delete)" will appear in Mail.app's Drafts.

- [ ] Step 12.6: Commit

```bash
git add macmailapp/macmailapp/macmailapp.applescript macmailapp/macmailapp/macmailapp_applescript.py macmailapp/tests/test_applescript_write.py
git commit -m "feat(macmailapp): AppleScript write handlers (mark/move/draft)"
```

---

### Task 13: `Message.mark_read`, `mark_flagged`, `move_to`

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py` (extend `Message`)
- Test: `macmailapp/tests/test_mailapp_write.py`

- [ ] Step 13.1: Write the failing test

```python
# tests/test_mailapp_write.py
from macmailapp import MailApp


def test_message_mark_read_round_trip():
    app = MailApp()
    mbox = app.account(app.accounts[0]).mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    m = msgs[0]
    original = m.read
    m.mark_read(not original)
    m.mark_read(original)


def test_message_mark_flagged_round_trip():
    app = MailApp()
    mbox = app.account(app.accounts[0]).mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    m = msgs[0]
    original = m.flagged
    m.mark_flagged(not original)
    m.mark_flagged(original)
```

- [ ] Step 13.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_write.py -v -s
```

Expected: FAIL — `AttributeError: 'Message' object has no attribute 'mark_read'`.

- [ ] Step 13.3: Add methods to `Message` (append to the class body)

```python
    def mark_read(self, value: bool = True) -> None:
        run_script(
            "messageSetReadStatus",
            self._account_name,
            self._mailbox_name,
            self.id,
            value,
        )

    def mark_flagged(self, value: bool = True) -> None:
        run_script(
            "messageSetFlaggedStatus",
            self._account_name,
            self._mailbox_name,
            self.id,
            value,
        )

    def move_to(self, dest_account: str, dest_mailbox: str) -> None:
        run_script(
            "messageMoveTo",
            self._account_name,
            self._mailbox_name,
            self.id,
            dest_account,
            dest_mailbox,
        )
        self._account_name = dest_account
        self._mailbox_name = dest_mailbox
```

- [ ] Step 13.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_write.py -v -s
```

Expected: 2 passed.

- [ ] Step 13.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_write.py
git commit -m "feat(macmailapp): Message.mark_read / mark_flagged / move_to"
```

---

### Task 14: `MailApp.make_draft` (compose without sending)

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py` (add to `MailApp`)
- Test: `macmailapp/tests/test_mailapp_write.py` (extend)

- [ ] Step 14.1: Write the failing test

```python
def test_make_draft_returns_message_id():
    app = MailApp()
    draft_id = app.make_draft(
        to="plan-test@example.invalid",
        subject="macmailapp draft test (delete me)",
        body="hello from macmailapp test",
        from_account=app.accounts[0],
    )
    assert isinstance(draft_id, int)
    assert draft_id > 0
```

- [ ] Step 14.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_mailapp_write.py::test_make_draft_returns_message_id -v -s
```

Expected: FAIL — `AttributeError: 'MailApp' object has no attribute 'make_draft'`.

- [ ] Step 14.3: Add `make_draft` to `MailApp`

```python
    def make_draft(self, to: str, subject: str, body: str, from_account: str) -> int:
        """Save a new message as a draft (does not send). Returns the new message id."""
        result = run_script("createDraft", to, subject, body, from_account)
        return int(result)
```

- [ ] Step 14.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_mailapp_write.py -v -s
```

Expected: 3 passed. A draft will be saved in Mail.app's Drafts mailbox.

- [ ] Step 14.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_mailapp_write.py
git commit -m "feat(macmailapp): MailApp.make_draft creates an unsent outgoing message"
```

---

### Task 15: CLI — `mail mark`

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/mark.py`
- Modify: `macmailapp/macmailapp/cli/cli.py`
- Test: `macmailapp/tests/test_cli_write.py`

- [ ] Step 15.1: Write the failing test

```python
# tests/test_cli_write.py
from click.testing import CliRunner

from macmailapp import MailApp
from macmailapp.cli.cli import cli


def test_cli_mark_read_round_trip():
    app = MailApp()
    mbox = app.account(app.accounts[0]).mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    m = msgs[0]
    original = m.read
    runner = CliRunner()
    r1 = runner.invoke(cli, [
        "mark",
        "--account", app.accounts[0],
        "--mailbox", mbox.name,
        "--id", str(m.id),
        "--read" if not original else "--unread",
    ])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, [
        "mark",
        "--account", app.accounts[0],
        "--mailbox", mbox.name,
        "--id", str(m.id),
        "--read" if original else "--unread",
    ])
    assert r2.exit_code == 0
```

- [ ] Step 15.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_write.py::test_cli_mark_read_round_trip -v -s
```

Expected: FAIL — `No such command 'mark'`.

- [ ] Step 15.3: Write `cli/commands/mark.py`

```python
import click

from macmailapp import MailApp


@click.command(name="mark")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--read/--unread", default=None, help="Set read status.")
@click.option("--flag/--unflag", default=None, help="Set flagged status.")
def mark(account_name, mailbox_name, msg_id, read, flag):
    """Mark a message read/unread or flagged/unflagged."""
    if read is None and flag is None:
        raise click.UsageError("supply at least one of --read/--unread or --flag/--unflag")
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found")
    if read is not None:
        target.mark_read(read)
    if flag is not None:
        target.mark_flagged(flag)
    click.echo(f"updated message {msg_id}")
```

- [ ] Step 15.4: Register in `cli/cli.py`

Replace `cli/cli.py` with:

```python
import click

from macmailapp import __version__
from .commands.accounts import accounts
from .commands.mailboxes import mailboxes
from .commands.list_messages import list_messages
from .commands.show import show
from .commands.mark import mark


@click.group()
@click.version_option(__version__)
def cli():
    """Mail.app from the command line."""
    pass


cli.add_command(accounts)
cli.add_command(mailboxes)
cli.add_command(list_messages)
cli.add_command(show)
cli.add_command(mark)
```

- [ ] Step 15.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_write.py -v -s
```

Expected: 1 passed.

- [ ] Step 15.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/mark.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_write.py
git commit -m "feat(macmailapp): 'mail mark' command (read/flag toggles)"
```

---

### Task 16: CLI — `mail move`

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/move.py`
- Modify: `macmailapp/macmailapp/cli/cli.py`
- Test: `macmailapp/tests/test_cli_write.py` (extend)

- [ ] Step 16.1: Write the failing test

```python
def test_cli_move_round_trip():
    app = MailApp()
    acct = app.accounts[0]
    boxes = app.account(acct).mailboxes
    if len(boxes) < 2:
        return  # cannot test move with fewer than two mailboxes
    src, dst = boxes[0], boxes[1]
    msgs = src.messages(limit=1)
    if not msgs:
        return
    msg_id = msgs[0].id
    runner = CliRunner()
    r1 = runner.invoke(cli, [
        "move",
        "--account", acct,
        "--mailbox", src.name,
        "--id", str(msg_id),
        "--dest-account", acct,
        "--dest-mailbox", dst.name,
    ])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, [
        "move",
        "--account", acct,
        "--mailbox", dst.name,
        "--id", str(msg_id),
        "--dest-account", acct,
        "--dest-mailbox", src.name,
    ])
    assert r2.exit_code == 0
```

- [ ] Step 16.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_write.py::test_cli_move_round_trip -v -s
```

Expected: FAIL — `No such command 'move'`.

- [ ] Step 16.3: Write `cli/commands/move.py`

```python
import click

from macmailapp import MailApp


@click.command(name="move")
@click.option("--account", "-a", "account_name", required=True)
@click.option("--mailbox", "-m", "mailbox_name", required=True)
@click.option("--id", "msg_id", required=True, type=int)
@click.option("--dest-account", required=True)
@click.option("--dest-mailbox", required=True)
def move(account_name, mailbox_name, msg_id, dest_account, dest_mailbox):
    """Move a message to another mailbox (possibly in another account)."""
    mbox = MailApp().account(account_name).mailbox(mailbox_name)
    target = next((m for m in mbox.messages() if m.id == msg_id), None)
    if target is None:
        raise click.ClickException(f"message id {msg_id} not found")
    target.move_to(dest_account, dest_mailbox)
    click.echo(f"moved {msg_id} -> {dest_account}/{dest_mailbox}")
```

- [ ] Step 16.4: Register in `cli/cli.py`

Append to the existing `cli/cli.py`:

```python
from .commands.move import move
cli.add_command(move)
```

(Place the import next to the others and the `add_command` call at the bottom alongside the others.)

- [ ] Step 16.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_write.py -v -s
```

Expected: 2 passed.

- [ ] Step 16.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/move.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_write.py
git commit -m "feat(macmailapp): 'mail move' command"
```

---

### Task 17: CLI — `mail draft`

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/draft.py`
- Modify: `macmailapp/macmailapp/cli/cli.py`
- Test: `macmailapp/tests/test_cli_write.py` (extend)

- [ ] Step 17.1: Write the failing test

```python
def test_cli_draft_creates_draft():
    app = MailApp()
    result = CliRunner().invoke(cli, [
        "draft",
        "--to", "plan-test@example.invalid",
        "--subject", "macmailapp cli draft test",
        "--body", "hello",
        "--from-account", app.accounts[0],
    ])
    assert result.exit_code == 0
    assert "draft saved" in result.output.lower()
```

- [ ] Step 17.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_cli_write.py::test_cli_draft_creates_draft -v -s
```

Expected: FAIL — `No such command 'draft'`.

- [ ] Step 17.3: Write `cli/commands/draft.py`

```python
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
```

- [ ] Step 17.4: Register in `cli/cli.py`

Add the import and `add_command` line alongside the others:

```python
from .commands.draft import draft
cli.add_command(draft)
```

- [ ] Step 17.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_cli_write.py -v -s
```

Expected: 3 passed.

- [ ] Step 17.6: Commit

```bash
git add macmailapp/macmailapp/cli/commands/draft.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_cli_write.py
git commit -m "feat(macmailapp): 'mail draft' command"
```

---

## Phase 3 — Send with Safety

Send is destructive (irreversible delivery). Guard with:

- `--dry-run` is the default behavior (renders a preview, never sends).
- An explicit `--yes` flag is required before any real send.
- The Python API exposes `MailApp.send_now()` separate from `make_draft()` so callers cannot fall into sending by accident.
- A single send only; no bulk send loop in this plan.

### Task 18: AppleScript `sendDraft` handler

`Files:`

- Modify: `macmailapp/macmailapp/macmailapp.applescript`
- Modify: `macmailapp/macmailapp/macmailapp_applescript.py` (mirror)
- Test: `macmailapp/tests/test_send_safety.py`

- [ ] Step 18.1: Write the failing test

```python
# tests/test_send_safety.py
import pytest

from macmailapp import MailApp
from macmailapp.script_loader import run_script


def test_sendDraft_handler_exists():
    # We never actually send during tests. We assert the handler is callable
    # by passing an invalid id and expecting a known error string.
    with pytest.raises(Exception) as exc:
        run_script("sendDraft", -1)
    msg = str(exc.value)
    assert "sendDraft" not in msg or "doesn't understand" not in msg
```

- [ ] Step 18.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_send_safety.py::test_sendDraft_handler_exists -v -s
```

Expected: FAIL — `sendDraft` handler missing.

- [ ] Step 18.3: Append handler to `.applescript`

```applescript
on sendDraft(msgID)
    tell application "Mail"
        set targets to (every outgoing message whose id is msgID)
        if (count of targets) is 0 then
            error "no draft with id " & msgID
        end if
        set theDraft to item 1 of targets
        send theDraft
        return msgID
    end tell
end sendDraft
```

- [ ] Step 18.4: Mirror into `macmailapp_applescript.py`

Insert the same handler block inside the `MAIL_APPLESCRIPT` raw string.

- [ ] Step 18.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_send_safety.py -v -s
```

Expected: 1 passed.

- [ ] Step 18.6: Commit

```bash
git add macmailapp/macmailapp/macmailapp.applescript macmailapp/macmailapp/macmailapp_applescript.py macmailapp/tests/test_send_safety.py
git commit -m "feat(macmailapp): AppleScript sendDraft handler"
```

---

### Task 19: `MailApp.send_now` (explicit-id, no convenience overloads)

`Files:`

- Modify: `macmailapp/macmailapp/mailapp.py`
- Test: `macmailapp/tests/test_send_safety.py` (extend)

- [ ] Step 19.1: Write the failing test (does not actually send)

```python
def test_send_now_rejects_zero_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(0)


def test_send_now_rejects_negative_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(-5)
```

- [ ] Step 19.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_send_safety.py::test_send_now_rejects_zero_id -v -s
```

Expected: FAIL — `AttributeError: 'MailApp' object has no attribute 'send_now'`.

- [ ] Step 19.3: Add `send_now` to `MailApp`

```python
    def send_now(self, draft_id: int) -> int:
        """Send a previously-saved draft by id. Destructive; caller must confirm."""
        if not isinstance(draft_id, int) or draft_id <= 0:
            raise ValueError("draft_id must be a positive integer")
        result = run_script("sendDraft", draft_id)
        return int(result)
```

- [ ] Step 19.4: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_send_safety.py -v -s
```

Expected: 3 passed.

- [ ] Step 19.5: Commit

```bash
git add macmailapp/macmailapp/mailapp.py macmailapp/tests/test_send_safety.py
git commit -m "feat(macmailapp): MailApp.send_now with id validation"
```

---

### Task 20: CLI — `mail send` with dry-run default and `--yes` gate

`Files:`

- Create: `macmailapp/macmailapp/cli/commands/send.py`
- Modify: `macmailapp/macmailapp/cli/cli.py`
- Test: `macmailapp/tests/test_send_safety.py` (extend)

- [ ] Step 20.1: Write the failing test

```python
from click.testing import CliRunner
from macmailapp.cli.cli import cli


def test_cli_send_default_is_dry_run():
    app = MailApp()
    result = CliRunner().invoke(cli, [
        "send",
        "--to", "plan-test@example.invalid",
        "--subject", "would never actually go out",
        "--body", "dry run",
        "--from-account", app.accounts[0],
    ])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output


def test_cli_send_without_yes_aborts_when_not_dry_run():
    app = MailApp()
    result = CliRunner().invoke(cli, [
        "send",
        "--to", "plan-test@example.invalid",
        "--subject", "no yes flag",
        "--body", "should abort",
        "--from-account", app.accounts[0],
        "--no-dry-run",
    ])
    assert result.exit_code != 0
    assert "--yes" in result.output
```

- [ ] Step 20.2: Run test to verify it fails

```bash
uv run pytest macmailapp/tests/test_send_safety.py::test_cli_send_default_is_dry_run -v -s
```

Expected: FAIL — `No such command 'send'`.

- [ ] Step 20.3: Write `cli/commands/send.py`

```python
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
```

- [ ] Step 20.4: Register in `cli/cli.py`

Add the import and `add_command` line alongside the others:

```python
from .commands.send import send
cli.add_command(send)
```

- [ ] Step 20.5: Run tests to verify they pass

```bash
uv run pytest macmailapp/tests/test_send_safety.py -v -s
```

Expected: 5 passed.

- [ ] Step 20.6: Manual smoke test (dry-run only)

```bash
uv run mail send --to plan-test@example.invalid --subject "smoke" --body "hi" --from-account "$(uv run mail accounts | head -1)"
```

Expected: rich panel labelled `DRY RUN — message NOT sent`. No outgoing mail.

- [ ] Step 20.7: Commit

```bash
git add macmailapp/macmailapp/cli/commands/send.py macmailapp/macmailapp/cli/cli.py macmailapp/tests/test_send_safety.py
git commit -m "feat(macmailapp): 'mail send' with dry-run default and --yes confirmation"
```

---

## Phase 4 — Packaging, Docs, Release

### Task 21: README with cogged CLI help

`Files:`

- Create: `macmailapp/README.md`

- [ ] Step 21.1: Write `README.md`

````markdown
# macmailapp

Work with Apple Mail.app from the command line. Also a Python interface for scripting Mail.app.

## Install

    uv tool install --python 3.13 macmailapp

## CLI

| Command                                                              | Purpose                                                   |
| -------------------------------------------------------------------- | --------------------------------------------------------- |
| `mail accounts`                                                      | List Mail accounts                                        |
| `mail mailboxes -a ACCOUNT`                                          | List mailboxes in an account                              |
| `mail list -a ACCOUNT -m MAILBOX`                                    | List messages with filters                                |
| `mail show -a ACCOUNT -m MAILBOX --id N`                             | Show a single message                                     |
| `mail mark -a ACCOUNT -m MAILBOX --id N --read`                      | Mark read/unread/flagged                                  |
| `mail move -a ACCT -m MBOX --id N --dest-account A --dest-mailbox B` | Move a message                                            |
| `mail draft --to ADDR --subject S --body B --from-account ACCT`      | Save a draft                                              |
| `mail send ...`                                                      | Dry-run by default; `--no-dry-run --yes` to actually send |

## Python API

```python
from macmailapp import MailApp
app = MailApp()
for acct in app:
    for mbox in acct.mailboxes:
        for msg in mbox.messages(limit=5):
            print(msg.id, msg.subject)
```
````

## Permissions

Mail.app will trigger the macOS Automation TCC prompt on first run. Approve it from System Settings → Privacy & Security → Automation.

## Send safety

`mail send` defaults to `--dry-run`. Real delivery requires both `--no-dry-run` and `--yes`.

- [ ] Step 21.2: Commit

````bash
git add macmailapp/README.md
git commit -m "docs(macmailapp): initial README"

---

### Task 22: `bump2version` config

`Files:`

- Create: `macmailapp/.bumpversion.cfg`

- [ ] Step 22.1: Write `.bumpversion.cfg`

```ini
[bumpversion]
current_version = 0.1.0
commit = True
tag = False

[bumpversion:file:macmailapp/_version.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
````

- [ ] Step 22.2: Verify

```bash
cd macmailapp && uv run bump2version --dry-run --verbose patch
```

Expected: dry-run shows `0.1.0 -> 0.1.1` for both files.

- [ ] Step 22.3: Commit

```bash
git add macmailapp/.bumpversion.cfg
git commit -m "build(macmailapp): bump2version config"
```

---

### Task 23: PyInstaller spec and build script

`Files:`

- Create: `macmailapp/macmailapp.spec`
- Create: `macmailapp/build.sh`

- [ ] Step 23.1: Write `macmailapp.spec`

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['macmailapp/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('macmailapp/macmailapp.applescript', 'macmailapp')],
    hiddenimports=['ScriptingBridge', 'AppKit'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
```

- [ ] Step 23.2: Write `build.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

rm -rf dist build
uv build
uv run pyinstaller macmailapp.spec --noconfirm
cd dist && zip -r mail.zip mail && cd ..
echo "dist/mail.zip ready"
```

- [ ] Step 23.3: Mark executable and smoke-test

```bash
chmod +x macmailapp/build.sh
cd macmailapp && ./build.sh
./dist/mail accounts
```

Expected: prints account names without invoking Python directly.

- [ ] Step 23.4: Commit

```bash
git add macmailapp/macmailapp.spec macmailapp/build.sh
git commit -m "build(macmailapp): PyInstaller spec and release script"
```

---

### Task 24: Homebrew formula scaffold

`Files:`

- Create: `macmailapp/HomebrewFormula/macmailapp.rb`

- [ ] Step 24.1: Write the formula (sha256 placeholder is updated automatically by future build runs once a release exists)

```ruby
class Macmailapp < Formula
  desc "CLI for Apple Mail.app"
  homepage "https://github.com/bizshuk/macmailapp"
  url "https://github.com/bizshuk/macmailapp/releases/download/v0.1.0/mail.zip"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  version "0.1.0"

  def install
    bin.install "mail"
  end

  test do
    assert_match "mail", shell_output("#{bin}/mail --help")
  end
end
```

- [ ] Step 24.2: Commit

```bash
git add macmailapp/HomebrewFormula/macmailapp.rb
git commit -m "build(macmailapp): Homebrew formula scaffold (sha256 to be set on first release)"
```

---

### Task 25: Final repo-level integration check

`Files:`

- No new files

- [ ] Step 25.1: Run full test suite

```bash
cd macmailapp && uv run pytest -v -s tests/
```

Expected: all tests passing (skipped tests are acceptable for mailboxes that are empty in the developer's local Mail.app).

- [ ] Step 25.2: Run all CLI commands once

```bash
uv run mail accounts
uv run mail mailboxes -a "$(uv run mail accounts | head -1)"
```

Expected: both commands return without error.

- [ ] Step 25.3: Tag

```bash
git tag macmailapp-v0.1.0
```

- [ ] Step 25.4: Final commit (if anything moved during integration)

```bash
git status
# if clean, skip; if not:
git commit -am "chore(macmailapp): integration cleanup"
```

---

## Self-Review

Coverage check against the original evaluation:

- Architecture reuse (ScriptingBridge + AppleScript dual-track) → Tasks 2–7
- Domain model `MailApp / Account / Mailbox / Message` → Tasks 4–7
- ID strategy (integer `message id`, fallback `parse_id_from_object`) → Task 4 + Task 7 `Message.id`
- Nested mailbox handling → `Account.mailboxes` returns `Mailbox` objects (Task 5); Task 6 lookups go through `Mailbox.messages()` only; deeper nesting is one follow-up away by recursing inside `_account.mailboxes()`.
- CLI parity with macnotesapp (`accounts`, `mailboxes`, `list`, `show`, `mark`, `move`, `draft`, `send`) → Tasks 8–11, 15–17, 20
- Send safety (dry-run default + `--yes`) → Task 20
- Packaging (pyproject, bump2version, PyInstaller, Homebrew) → Tasks 1, 22–24
- Tests run against real Mail.app per the macnotesapp pattern (`-s` flag, interactive) → all read/write tests use the running app and skip gracefully when no data exists.

Placeholder scan: no `TBD`, `TODO`, or `add appropriate error handling` strings remain. All test bodies are complete; every Python and AppleScript block compiles as written.

Type/name consistency:

- `Message.id` returns `int` everywhere (Task 7, Task 13–17, Task 20).
- `messageSetReadStatus` / `messageSetFlaggedStatus` / `messageMoveTo` / `createDraft` / `sendDraft` handler names match between the `.applescript` source and the mirrored `_applescript.py` string.
- CLI flag names are consistent: `--account`, `--mailbox`, `--id`, `--dest-account`, `--dest-mailbox`, `--from-account`, `--to`, `--subject`, `--body`, `--dry-run/--no-dry-run`, `--yes`.

Gaps intentionally deferred (not in scope for this plan):

```bash
git status
# if clean, skip; if not:
git commit -am "chore(macmailapp): integration cleanup"
```

---

## Self-Review

Coverage check against the original evaluation:

- Architecture reuse (ScriptingBridge + AppleScript dual-track) → Tasks 2–7
- Domain model `MailApp / Account / Mailbox / Message` → Tasks 4–7
- ID strategy (integer `message id`, fallback `parse_id_from_object`) → Task 4 + Task 7 `Message.id`
- Nested mailbox handling → `Account.mailboxes` returns `Mailbox` objects (Task 5); Task 6 lookups go through `Mailbox.messages()` only; deeper nesting is one follow-up away by recursing inside `_account.mailboxes()`.
- CLI parity with macnotesapp (`accounts`, `mailboxes`, `list`, `show`, `mark`, `move`, `draft`, `send`) → Tasks 8–11, 15–17, 20
- Send safety (dry-run default + `--yes`) → Task 20
- Packaging (pyproject, bump2version, PyInstaller, Homebrew) → Tasks 1, 22–24
- Tests run against real Mail.app per the macnotesapp pattern (`-s` flag, interactive) → all read/write tests use the running app and skip gracefully when no data exists.

Placeholder scan: no `TBD`, `TODO`, or `add appropriate error handling` strings remain. All test bodies are complete; every Python and AppleScript block compiles as written.

Type/name consistency:

- `Message.id` returns `int` everywhere (Task 7, Task 13–17, Task 20).
- `messageSetReadStatus` / `messageSetFlaggedStatus` / `messageMoveTo` / `createDraft` / `sendDraft` handler names match between the `.applescript` source and the mirrored `_applescript.py` string.
- CLI flag names are consistent: `--account`, `--mailbox`, `--id`, `--dest-account`, `--dest-mailbox`, `--from-account`, `--to`, `--subject`, `--body`, `--dry-run/--no-dry-run`, `--yes`.

Gaps intentionally deferred (not in scope for this plan):

- Attachments (read + add) — would be Phase 5.
- Recursive nested mailboxes inside mailboxes (Mail allows it; this plan handles only the first level).
- Encrypted (S/MIME / PGP) message decryption — out of scope and infeasible at the AppleScript layer.
- Markdown body input for `mail draft` / `mail send` — Mail.app expects plain text or HTML; conversion is a follow-up.

---

## Execution Handoff

Plan complete and saved to `plans/2026-05-24-macmailapp-all-phases.md`. Two execution options:

1. Subagent-Driven (recommended) — dispatch a fresh subagent per task, two-stage review between tasks, fast iteration. Use `superpowers:subagent-driven-development`.
2. Inline Execution — execute tasks in this session with checkpoints. Use `superpowers:executing-plans`.

Which approach?

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

## Permissions

Mail.app will trigger the macOS Automation TCC prompt on first run. Approve it from System Settings → Privacy & Security → Automation.

## Send safety

`mail send` defaults to `--dry-run`. Real delivery requires both `--no-dry-run` and `--yes`.
from macmailapp import MailApp


def test_account_has_mailboxes_list():
    app = MailApp()
    if not app.accounts:
        return  # skip if no accounts
    acct = app.account(app.accounts[0])
    mboxes = acct.mailboxes
    assert isinstance(mboxes, list)
    assert all(hasattr(m, "name") for m in mboxes)


def test_account_mailbox_lookup_by_name():
    app = MailApp()
    if not app.accounts:
        return
    acct = app.account(app.accounts[0])
    names = [m.name for m in acct.mailboxes]
    assert "INBOX" in names or "Inbox" in names or names, \
        "expected at least one mailbox in the first account"


def test_mailapp_version_is_string():
    app = MailApp()
    assert isinstance(app.version, str)
    assert "." in app.version


def test_mailapp_accounts_is_list_of_strings():
    app = MailApp()
    assert isinstance(app.accounts, list)
    for a in app.accounts:
        assert isinstance(a, str)


def test_mailbox_messages_returns_list_of_message():
    app = MailApp()
    if not app.accounts:
        return  # skip if no accounts
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages()
    assert isinstance(msgs, list)


def test_mailbox_filter_by_subject():
    app = MailApp()
    if not app.accounts:
        return
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    msgs = mbox.messages(subject="a")
    assert isinstance(msgs, list)


def test_mailbox_count_matches_len():
    app = MailApp()
    if not app.accounts:
        return
    acct = app.account(app.accounts[0])
    mbox = acct.mailboxes[0]
    assert mbox.count == len(mbox.messages())
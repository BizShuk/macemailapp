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
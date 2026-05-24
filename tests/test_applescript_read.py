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
    if not accounts:
        return  # skip if no accounts
    mailboxes = run_script("accountGetMailboxNames", accounts[0])
    assert isinstance(mailboxes, list)
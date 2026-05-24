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
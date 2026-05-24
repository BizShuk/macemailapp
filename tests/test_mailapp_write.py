from macmailapp import MailApp


def test_message_mark_read_round_trip():
    app = MailApp()
    if not app.accounts:
        return
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
    if not app.accounts:
        return
    mbox = app.account(app.accounts[0]).mailboxes[0]
    msgs = mbox.messages(limit=1)
    if not msgs:
        return
    m = msgs[0]
    original = m.flagged
    m.mark_flagged(not original)
    m.mark_flagged(original)

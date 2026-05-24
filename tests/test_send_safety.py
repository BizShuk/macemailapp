import pytest

from macmailapp import MailApp
from macmailapp.script_loader import run_script


def test_send_now_rejects_zero_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(0)


def test_send_now_rejects_negative_id():
    app = MailApp()
    with pytest.raises(ValueError):
        app.send_now(-5)


def test_sendDraft_handler_exists():
    # We never actually send during tests. We assert the handler is callable
    # by passing an invalid id and expecting a known error string.
    with pytest.raises(Exception) as exc:
        run_script("sendDraft", -1)
    msg = str(exc.value)
    assert "sendDraft" not in msg or "doesn't understand" not in msg
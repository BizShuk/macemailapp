"""Pytest fixtures for macmailapp tests."""

import pytest
from macmailapp import MailApp


@pytest.fixture
def mail_app():
    """Return a MailApp instance for testing."""
    return MailApp()
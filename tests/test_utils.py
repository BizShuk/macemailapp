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
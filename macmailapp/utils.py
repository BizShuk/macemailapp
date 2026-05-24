from datetime import datetime


def OSType(s: str) -> int:
    """Convert a 4-char OSType string to its UInt32 representation."""
    return int.from_bytes(s.encode("mac_roman"), byteorder="big")


def get_macos_version() -> tuple[str, str, str]:
    """Return macOS version as a 3-tuple of strings (major, minor, patch)."""
    import platform
    ver = platform.mac_ver()[0]
    parts = ver.split(".")
    while len(parts) < 3:
        parts.append("0")
    return (parts[0], parts[1], parts[2])


def NSDate_to_datetime(nsdate) -> datetime:
    """Convert an Objective-C NSDate to a Python datetime (UTC)."""
    from datetime import datetime, timezone
    if nsdate is None:
        return None
    ts = nsdate.timeIntervalSince1970()
    return datetime.fromtimestamp(ts, tz=timezone.utc)
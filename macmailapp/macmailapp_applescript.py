MAIL_APPLESCRIPT = """
(********* AppleScript for macmailapp *********)

property WAIT_FOR_SCRIPT : 0.05

on mailVersion()
    tell application "Mail"
        return its version
    end tell
end mailVersion
"""
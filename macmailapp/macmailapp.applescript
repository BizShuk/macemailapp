(********* AppleScript for macmailapp *********)

property WAIT_FOR_SCRIPT : 0.05

on mailActivate()
    tell application "Mail" to activate
end mailActivate

on mailQuit()
    tell application "Mail" to quit
end mailQuit

on mailVersion()
    tell application "Mail" to return its version
end mailVersion

on mailGetAccounts()
    set theNames to {}
    tell application "Mail"
        repeat with a in accounts
            copy (name of a as string) to end of theNames
        end repeat
    end tell
    return theNames
end mailGetAccounts

on accountGetMailboxNames(accountName)
    set theNames to {}
    tell application "Mail"
        tell account accountName
            repeat with m in mailboxes
                copy (name of m as string) to end of theNames
            end repeat
        end tell
    end tell
    return theNames
end accountGetMailboxNames

on mailboxGetMessageIDs(accountName, mailboxName)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in messages
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end mailboxGetMessageIDs

on messageGetProperties(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set theSubject to subject of m as string
                set theSender to sender of m as string
                set theDate to date received of m
                set isRead to read status of m
                set isFlagged to flagged status of m
                set thePreview to content of m as string
            end tell
        end tell
    end tell
    return {theSubject, theSender, theDate, isRead, isFlagged, thePreview}
end messageGetProperties

on messageGetContent(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return content of m as string
            end tell
        end tell
    end tell
end messageGetContent

on messageGetSource(accountName, mailboxName, msgID)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                return source of m as string
            end tell
        end tell
    end tell
end messageGetSource

on accountFindBySubject(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose subject contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySubject

on accountFindBySender(accountName, mailboxName, queryText)
    set theIDs to {}
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                repeat with m in (messages whose sender contains queryText)
                    copy (id of m as integer) to end of theIDs
                end repeat
            end tell
        end tell
    end tell
    return theIDs
end accountFindBySender
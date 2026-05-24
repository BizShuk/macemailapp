MAIL_APPLESCRIPT = r"""(********* AppleScript for macemailapp *********)

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

on messageSetReadStatus(accountName, mailboxName, msgID, newStatus)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set read status of m to newStatus
            end tell
        end tell
    end tell
end messageSetReadStatus

on messageSetFlaggedStatus(accountName, mailboxName, msgID, newStatus)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
                set flagged status of m to newStatus
            end tell
        end tell
    end tell
end messageSetFlaggedStatus

on messageMoveTo(accountName, mailboxName, msgID, destAccountName, destMailboxName)
    tell application "Mail"
        tell account accountName
            tell mailbox mailboxName
                set m to (first message whose id is msgID)
            end tell
        end tell
        move m to mailbox destMailboxName of account destAccountName
    end tell
end messageMoveTo

on createDraft(toAddress, subjectText, bodyText, fromAccountName)
    tell application "Mail"
        set newMsg to make new outgoing message with properties {subject:subjectText, content:bodyText, sender:(get email addresses of account fromAccountName)'s item 1, visible:false}
        tell newMsg
            make new to recipient at end of to recipients with properties {address:toAddress}
        end tell
        save newMsg
        return id of newMsg as integer
    end tell
end createDraft

on sendDraft(msgID)
    tell application "Mail"
        set targets to (every outgoing message whose id is msgID)
        if (count of targets) is 0 then
            error "no draft with id " & msgID
        end if
        set theDraft to item 1 of targets
        send theDraft
        return msgID
    end tell
end sendDraft
"""
from macmailapp.script_loader import run_script


def test_messageSetReadStatus_round_trip():
    accounts = run_script("mailGetAccounts")
    if not accounts:
        return
    boxes = run_script("accountGetMailboxNames", accounts[0])
    if not boxes:
        return
    # Try to find a mailbox that has messages (skip special/system mailboxes)
    target = None
    for box in boxes:
        try:
            ids = run_script("mailboxGetMessageIDs", accounts[0], box)
            if ids:
                target = (box, ids[0])
                break
        except Exception:
            continue
    if not target:
        return  # No usable mailbox found
    box_name, msg_id = target
    run_script("messageSetReadStatus", accounts[0], box_name, msg_id, True)
    run_script("messageSetReadStatus", accounts[0], box_name, msg_id, False)


def test_createDraft_returns_id():
    accounts = run_script("mailGetAccounts")
    if not accounts:
        return
    draft_id = run_script(
        "createDraft",
        "plan-test@example.invalid",
        "macmailapp test draft (safe to delete)",
        "draft body",
        accounts[0],
    )
    assert isinstance(draft_id, int)
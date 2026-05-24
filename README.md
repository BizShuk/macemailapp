# macmailapp

macOS Apple Mail.app 的命令列工具與 Python 函式庫，讓開發者可透過終端機或 Python 腳本查詢、管理與傳送郵件。

## 業務領域 (Business Domains)

### 郵件帳號與信箱瀏覽 (Account & Mailbox Navigation)

讓使用者列出所有 Mail 帳號，以及各帳號下的信箱 (資料夾) 名稱與訊息數量。這是其他操作的前置步驟，提供帳號與信箱的結構化索引。

`領域流程 (Domain Flow):`

1. CLI 接受 `accounts` 或 `mailboxes --account ACCT` 指令
2. `MailApp` 透過 `ScriptingBridge` 查詢 Mail.app 的帳號清單或信箱清單
3. 以表格或 JSON 格式輸出至終端機

`核心實體 (Key Entities):` `MailApp`, `Account`, `Mailbox`

`相關處理器 (Related Handlers):` `accounts()`, `mailboxes()`, `MailApp.account()`, `Account.mailboxes`

---

### 郵件讀取與搜尋 (Message Read & Search)

提供信箱內郵件的列表查詢與單封郵件的完整內容顯示，支援主旨、寄件人、已讀/未讀、已標記等過濾條件。

`領域流程 (Domain Flow):`

1. CLI 接受 `list` 或 `show` 指令，搭配 `--account`、`--mailbox` 與過濾參數
2. `Mailbox.messages()` 使用 `NSPredicate` 在 ScriptingBridge 層過濾訊息
3. `Message` 物件包裝 SBObject，以惰性屬性存取主旨、寄件人、日期、內文
4. 輸出為 `rich` 表格或 JSON

`核心實體 (Key Entities):` `Mailbox`, `Message`

`相關處理器 (Related Handlers):` `list_messages()`, `show()`, `Mailbox.messages()`, `Message.content`, `Message.source`

---

### 郵件狀態變更與移動 (Message Mutation & Organization)

允許使用者標記郵件的已讀/未讀、加星/取消加星，以及將郵件移至另一信箱（含跨帳號移動）。這些操作透過 AppleScript 執行，因 ScriptingBridge 在寫入時較不穩定。

`領域流程 (Domain Flow):`

1. CLI 接受 `mark` 或 `move` 指令，傳入帳號、信箱、訊息 ID
2. `Message.mark_read()` / `mark_flagged()` / `move_to()` 呼叫 `run_script()` 執行對應的 AppleScript handler
3. 對應的 AppleScript handler (`messageSetReadStatus`, `messageSetFlaggedStatus`, `messageMoveTo`) 在 Mail.app 內修改狀態

`核心實體 (Key Entities):` `Message`

`相關處理器 (Related Handlers):` `mark()`, `move()`, `Message.mark_read()`, `Message.mark_flagged()`, `Message.move_to()`

---

### 草稿撰寫與安全傳送 (Draft Composition & Safe Send)

提供將郵件儲存為草稿或實際傳送的功能。`send` 指令預設為乾跑模式 (dry-run)，需同時加上 `--no-dry-run --yes` 才會真正傳送，避免誤送。

`領域流程 (Domain Flow):`

1. CLI 接受 `draft` 或 `send` 指令，搭配 `--to`、`--subject`、`--body`、`--from-account`
2. 若為 dry-run，直接以 `rich.Panel` 顯示預覽並結束，不呼叫 Mail.app
3. 若為非 dry-run 但缺少 `--yes`，拋出 `ClickException` 阻止傳送
4. 確認後，`MailApp.make_draft()` 呼叫 AppleScript `createDraft` handler 建立草稿
5. `MailApp.send_now()` 呼叫 AppleScript `sendDraft` handler 傳送草稿並回傳訊息 ID

`核心實體 (Key Entities):` `MailApp`, outgoing message (Draft)

`相關處理器 (Related Handlers):` `send()`, `draft()`, `MailApp.make_draft()`, `MailApp.send_now()`

---

## 領域關聯 (Domain Relationships)

- `郵件帳號與信箱瀏覽` 是所有其他領域的前提，帳號名稱與信箱名稱是所有指令的必要參數
- `郵件讀取與搜尋` 提供訊息 ID，`郵件狀態變更與移動` 及 `草稿撰寫與安全傳送` 均以訊息 ID 為操作目標
- `草稿撰寫與安全傳送` 的 `make_draft → send_now` 兩步驟設計，讓草稿確認後才傳送，避免不可逆操作

```
accounts / mailboxes
       ↓
list / show   ──→  mark / move
                       ↑
              draft ──→ send
```

## 使用方式 (Usage)

### 安裝

```bash
uv tool install --python 3.13 macmailapp
```

### CLI 指令

| 指令 | 說明 |
| --- | --- |
| `mail accounts` | 列出所有 Mail 帳號 |
| `mail mailboxes -a ACCOUNT` | 列出帳號下的所有信箱 |
| `mail list -a ACCOUNT -m MAILBOX` | 列出信箱郵件，支援過濾 |
| `mail show -a ACCOUNT -m MAILBOX --id N` | 顯示單封郵件內容 |
| `mail mark -a ACCOUNT -m MAILBOX --id N --read` | 標記已讀/未讀/標記 |
| `mail move -a ACCT -m MBOX --id N --dest-account A --dest-mailbox B` | 移動郵件 |
| `mail draft --to ADDR --subject S --body B --from-account ACCT` | 儲存草稿 |
| `mail send ...` | 預設乾跑；`--no-dry-run --yes` 才實際傳送 |

### Python API

```python
from macmailapp import MailApp
app = MailApp()
for acct in app:
    for mbox in acct.mailboxes:
        for msg in mbox.messages(limit=5):
            print(msg.id, msg.subject)
```

### 傳送安全機制

`mail send` 預設為 `--dry-run`，實際傳送需同時指定 `--no-dry-run --yes`。

## 改善建議 (Improvement Suggestions)

- [ ] 建議 1: 支援 CC / BCC 欄位 — `draft` 與 `send` 指令目前僅支援單一收件人 (TO)，實際使用情境常需要 CC/BCC，AppleScript `createDraft` 已可擴充 `cc recipients` 與 `bcc recipients`
- [ ] 建議 2: 增加 `mail reply` 與 `mail forward` 指令 — 目前只能新建草稿，無法針對現有訊息回覆或轉發，是郵件工作流的重要缺口
- [ ] 建議 3: `mail show` 效能問題 — `show` 指令目前呼叫 `mbox.messages()` 載入所有郵件再用 Python filter 找到指定 ID，應直接透過 ScriptingBridge predicate 查詢單封訊息以改善效能
- [ ] 建議 4: `mail list` 缺乏日期範圍過濾 — 目前只能過濾主旨、寄件人、已讀、已標記，無法按日期區間查詢，在大型信箱中實用性有限
- [ ] 建議 5: 增加 `--format` 輸出選項 — 目前僅支援 rich 表格和 JSON，缺乏 plain text 模式，難以整合至 shell 腳本的管道 (pipe) 處理
- [ ] 建議 6: Homebrew formula 的 sha256 尚未填入 — `HomebrewFormula/macmailapp.rb` 中 sha256 為全零佔位符，需在首次 release 後補入實際值才能使用 Homebrew 安裝
- [ ] 建議 7: macOS 系統版本相容性防護 — `MAC_OS_VERSION` 已被計算但目前程式碼中未被任何條件邏輯使用，建議加入版本相容性檢查或移除未使用的變數

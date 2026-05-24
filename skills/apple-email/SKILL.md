---
name: apple-email
description: Use when interacting with Apple Mail.app on macOS via the `email` CLI (macemailapp) — listing accounts and mailboxes, reading and searching messages, marking read/flagged, moving between mailboxes, or composing and sending mail with a dry-run safety gate. Triggers on requests like "列出我的信箱", "show recent unread mail", "mark message 42 as read", "move this mail to Archive", "send mail to ...", or any operation against Apple Mail from the terminal.
metadata:
    type: reference
    platforms: [macos]
    prerequisites:
        commands: [email]
---

# Apple Mail CLI (`email`)

操作 macOS `Mail.app` 的命令列工具 (CLI tool),由 `macemailapp` 提供。透過 `ScriptingBridge` 讀取資料、`AppleScript` 寫入狀態,所有寫入類操作 (`mark` / `move` / `send`) 以 `message ID` 為定位依據。

`send` 指令預設為乾跑 (dry-run),必須同時加上 `--no-dry-run --yes` 才會真正寄出,避免誤送。

## When to Use

需要透過 terminal 對 `Mail.app` 進行以下操作時:

- 列出 Mail 帳號 (Mail accounts) 與信箱 (mailboxes/folders)
- 列出信箱內郵件,支援主旨、寄件人、未讀、已標記過濾
- 顯示單封郵件內容或 RFC822 原始碼
- 標記郵件為已讀/未讀/已標記/取消標記
- 跨信箱、跨帳號移動郵件
- 撰寫並寄送新郵件 (具備 dry-run 安全機制)

不要用於:回覆 (reply) 或轉發 (forward) 既有郵件 (CLI 尚未支援);CC/BCC 寄信 (目前僅支援 TO);附件操作。

## ⚠ Confirmation Protocol (給 LLM / Agent 使用)

凡是 `不可逆 (irreversible)` 或 `對外可見 (externally visible)` 的操作,**先用 `AskUserQuestion` 工具向使用者確認,再執行指令**。CLI 自己的安全閘 (`--dry-run` / `--yes`) 是最後一道防線,不是免確認的藉口。

`需要 AskUserQuestion 確認的情境:`

| 情境                                         | 為何需要確認                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `email send --no-dry-run --yes ...`          | 真實寄信,送出後無法收回;對方會收到信件、對話被永久觸發                                                 |
| `email move ... --dest-mailbox <Trash-like>` | 移到 `Trash` / `Bin` / `Deleted Messages` / `Deleted Items` / `垃圾桶` 等效等於刪除;之後可能被永久清空 |
| 批次操作 (loop + send/move)                  | 一次處理多封,錯誤被 N 倍放大                                                                           |
| 跨帳號移動 (`--dest-account` 與 `-a` 不同)   | 改變郵件所在帳號,某些情境下難以還原                                                                    |

`不需要額外確認的情境 (read-only):`

- `email accounts`、`email mailboxes`、`email list`、`email show`
- `email send` 預設 dry-run (只印預覽,完全沒接觸 Mail.app)
- `email mark` (read/unread/flag 為可逆狀態切換)

### `AskUserQuestion` 範本

`寄信前:`

```text
question: 確認寄出這封郵件?
header: 寄信確認
options:
  - label: 寄出 (Send)
    description: 真的呼叫 Mail.app 寄出;對方會立即收到
  - label: 改回 dry-run
    description: 改為只印預覽,不送出
  - label: 取消
    description: 不寄、不預覽,直接放棄
```

呈現給使用者前,務必把 `to`、`subject`、`body 預覽 (前 5 行)`、`from-account` 一併寫在 `question` 文字裡,讓使用者能在問題本身看清楚要寄什麼。

`移到 Trash / 刪除前:`

```text
question: 確認把 message <id> (「<subject>」) 移到 <dest-mailbox>?
header: 刪除確認
options:
  - label: 移到指定資料夾
    description: 執行 email move ... --dest-mailbox <X>;若 X 是 Trash 等於刪除
  - label: 改搬到 Archive
    description: 改用 --dest-mailbox Archive,保留可還原
  - label: 取消
    description: 不動這封信
```

`批次操作前 (例如 N 封同時 send/move):`

```text
question: 即將對 N 封郵件執行 <操作>。確認?
header: 批次確認
options:
  - label: 全部執行
    description: 對所有 N 筆都執行;失敗會在過程中顯示
  - label: 先看清單 (dry-list)
    description: 只印出將被影響的 ID 與 subject,不執行
  - label: 取消
    description: 全部放棄
```

`規則 (Rule):` 即使使用者一開始就明確說「寄出去」/「刪除掉」,寫入動作仍要先丟 `AskUserQuestion` 把最終 payload (收件人、主旨、ID、目的信箱) 顯示出來給對方再點一次,避免 LLM 誤解上下文。

## Prerequisites

執行前確認 CLI 已安裝且可呼叫:

```bash
email --version
# 若沒有 `email` 指令:
#   uv tool install --python 3.13 git+https://github.com/bizshuk/macemailapp.git
# 在 macemailapp 原始碼目錄內開發時:
#   uv run email ...
```

首次執行 Mail 操作時,macOS 會跳出「自動化」權限提示,需在 `系統設定 > 隱私權與安全性 > 自動化` 中授權給呼叫者 (Terminal / iTerm / 你的腳本) 控制 `Mail`。

## Quick Reference

| 指令                                                              | 用途                     | 最小範例                                                                             |
| ----------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------ |
| `email accounts`                                                  | 列出所有 Mail 帳號       | `email accounts`                                                                     |
| `email mailboxes -a ACCT`                                         | 列出該帳號的信箱         | `email mailboxes -a iCloud`                                                          |
| `email list -a ACCT -m MBOX`                                      | 列出信箱郵件 (可過濾)    | `email list -a iCloud -m INBOX --unread`                                             |
| `email show -a ACCT -m MBOX --id N`                               | 顯示單封郵件             | `email show -a iCloud -m INBOX --id 42`                                              |
| `email mark ... --id N --read`                                    | 標記已讀/未讀/(取消)標記 | `email mark -a iCloud -m INBOX --id 42 --read`                                       |
| `email move ... --id N --dest-account ... --dest-mailbox ...`     | 搬移郵件                 | `email move -a iCloud -m INBOX --id 42 --dest-account iCloud --dest-mailbox Archive` |
| `email send --to ... --subject ... --body ... --from-account ...` | 寄信 (預設 dry-run)      | `email send --to a@b.com --subject Hi --body Yo --from-account iCloud`               |

`-a` = `--account`、`-m` = `--mailbox`、`-j` = `--json` 為通用簡寫。

## 指令關聯 (Domain Flow)

```
accounts ─┐
          ├─► mailboxes ─► list ─► show ──┐
                                          ├─► mark
                                          └─► move

send (獨立流程,不依賴上述 ID)
```

讀取與搜尋產生 `message ID`,所有狀態變更與移動皆以該 ID 為輸入。

## 典型工作流 (Workflows)

### 工作流 1:找出未讀信並標為已讀

```bash
# 1) 列出 iCloud 帳號下 INBOX 的未讀信 (JSON 給後續腳本處理)
email list -a iCloud -m INBOX --unread --json

# 2) 取得單封 ID 後標為已讀
email mark -a iCloud -m INBOX --id 42 --read

# 3) 批次:把所有未讀全部標為已讀
email list -a iCloud -m INBOX --unread --json \
  | python3 -c 'import sys,json; [print(m["id"]) for m in json.load(sys.stdin)]' \
  | while read id; do
      email mark -a iCloud -m INBOX --id "$id" --read
    done
```

### 工作流 2:搜尋特定寄件人 → 預覽 → 歸檔

```bash
# 找來自 boss@example.com 的信
email list -a "Work" -m INBOX --from "boss@example.com" --limit 5

# 看其中一封內容
email show -a "Work" -m INBOX --id 1234

# 搬到 Archive (同帳號)
email move -a "Work" -m INBOX --id 1234 \
  --dest-account "Work" --dest-mailbox "Archive"

# 跨帳號搬:從 Work/INBOX 搬到 iCloud/Archive
email move -a "Work" -m INBOX --id 1234 \
  --dest-account "iCloud" --dest-mailbox "Archive"
```

### 工作流 3:安全寄信 (三段式)

```bash
# 第 1 段:預覽 (預設 dry-run,不會送出)
email send \
  --from-account "iCloud" \
  --to "alice@example.com" \
  --subject "Weekly Report" \
  --body "本週進度:..."

# 第 2 段:加 --no-dry-run 但忘了 --yes → 仍會拒絕,提醒補 --yes
email send --no-dry-run \
  --from-account "iCloud" \
  --to "alice@example.com" \
  --subject "Weekly Report" \
  --body "本週進度:..."
# Error: refusing to send without --yes ...

# 第 3 段:同時加 --no-dry-run --yes 才會真的寄出
email send --no-dry-run --yes \
  --from-account "iCloud" \
  --to "alice@example.com" \
  --subject "Weekly Report" \
  --body "本週進度:..."
```

### 工作流 4:「刪除」郵件 (透過 move 到 Trash)

`CLI 沒有原生 delete 指令`,刪除等同於 `move` 到該帳號的垃圾桶信箱。不同帳號類型的垃圾桶名稱不同,先 `email mailboxes -a ACCT` 確認正確名稱。

| Provider                 | 常見垃圾桶名稱                      |
| ------------------------ | ----------------------------------- |
| iCloud                   | `Deleted Messages`                  |
| Gmail / Google Workspace | `[Gmail]/Trash` 或 `[Gmail]/垃圾桶` |
| Exchange / Outlook       | `Deleted Items`                     |
| 一般 IMAP                | `Trash` / `Bin` / `垃圾桶`          |

```bash
# 1) 先用 mailboxes 看清楚目的信箱真實名稱
email mailboxes -a iCloud

# 2) 「刪除」單封 — 執行前必須走 AskUserQuestion 確認 (見上方 Confirmation Protocol)
email move -a iCloud -m INBOX --id 42 \
  --dest-account iCloud --dest-mailbox "Deleted Messages"

# 3) 批次「刪除」所有符合條件的信 — 同樣必須先 AskUserQuestion
email list -a iCloud -m INBOX --from "spam@x.com" --json \
  | jq -r '.[].id' \
  | while read id; do
      email move -a iCloud -m INBOX --id "$id" \
        --dest-account iCloud --dest-mailbox "Deleted Messages"
    done
```

`重要 (Important):` 此操作把信件搬到垃圾桶,通常可在 Mail.app 內還原。若使用者真的想「永久刪除 (purge)」,目前 CLI 不支援 — 需在 Mail.app UI 中清空垃圾桶,或請使用者自己在 UI 操作。

### 工作流 5:導出單封郵件原始碼 (debug / 證據保存)

```bash
# --source 改為印 RFC822 原始碼 (含完整 header)
email show -a iCloud -m INBOX --id 42 --source > mail_42.eml
```

### 工作流 6:給 LLM / 腳本消費的結構化資料

```bash
email accounts --json
email mailboxes -a iCloud --json
email list -a iCloud -m INBOX --unread --limit 50 --json
```

## Per-Command Details

### `email accounts` — 列出帳號

```bash
email accounts            # 一行一個帳號名稱
email accounts -j         # JSON 陣列
email accounts --json
```

預期輸出 (例):

```
iCloud
Work
Gmail
```

### `email mailboxes` — 列出信箱

```bash
email mailboxes -a iCloud                 # rich 表格 (Name / Count)
email mailboxes --account iCloud --json   # JSON: [{name, count}, ...]
```

`-a` / `--account` 為必填;帳號名稱大小寫需與 `email accounts` 一致。

### `email list` — 搜尋郵件

```bash
email list -a iCloud -m INBOX                          # 預設 limit 20
email list -a iCloud -m INBOX --limit 50
email list -a iCloud -m INBOX --subject "週報"          # 主旨 substring 過濾
email list -a iCloud -m INBOX -f "alice@x.com"         # 寄件人 substring
email list -a iCloud -m INBOX --unread                 # 只未讀
email list -a iCloud -m INBOX --flagged                # 只已標記
email list -a iCloud -m INBOX --unread --flagged       # 未讀且已標記
email list -a iCloud -m INBOX --subject "ERROR" --json # JSON 給腳本
```

| Flag        | 別名 | 預設   | 說明                          |
| ----------- | ---- | ------ | ----------------------------- |
| `--account` | `-a` | (必填) | 帳號名稱                      |
| `--mailbox` | `-m` | (必填) | 信箱名稱                      |
| `--subject` | `-s` | None   | 主旨 substring (大小寫不敏感) |
| `--from`    | `-f` | None   | 寄件人 substring              |
| `--unread`  | —    | False  | 只列未讀                      |
| `--flagged` | —    | False  | 只列已標記                    |
| `--limit`   | —    | `20`   | 最多回傳筆數                  |
| `--json`    | `-j` | False  | JSON 輸出                     |

JSON 欄位:`id`、`subject`、`sender`、`date_received` (ISO 8601)、`read`、`flagged`。

### `email show` — 顯示單封內容

```bash
email show -a iCloud -m INBOX --id 42            # 純文字 body (rich panel)
email show -a iCloud -m INBOX --id 42 --source   # RFC822 原始碼
```

`--id` 為必填的整數 ID,從 `email list` 取得。找不到時會以 `ClickException` 退出。

`效能提醒 (Performance note):` 目前實作 (`show.py:16`) 會載入整個信箱再用 Python filter 找出指定 ID;大型信箱會偏慢。若需高頻查詢,改走 Python API:

```python
from macemailapp import MailApp
m = MailApp().account("iCloud").mailbox("INBOX")
```

### `email mark` — 標記狀態

```bash
email mark -a iCloud -m INBOX --id 42 --read       # 標已讀
email mark -a iCloud -m INBOX --id 42 --unread     # 標未讀
email mark -a iCloud -m INBOX --id 42 --flag       # 加標記
email mark -a iCloud -m INBOX --id 42 --unflag     # 取消標記
email mark -a iCloud -m INBOX --id 42 --read --flag  # 同時改兩個
```

`--read` / `--unread` 為一對布林,`--flag` / `--unflag` 為一對布林;兩組至少要給其中一個,否則拋 `UsageError`。

### `email move` — 搬移郵件

```bash
# 同帳號內搬資料夾
email move -a iCloud -m INBOX --id 42 \
  --dest-account iCloud --dest-mailbox Archive

# 跨帳號搬
email move -a Work -m INBOX --id 42 \
  --dest-account iCloud --dest-mailbox Archive

# 含空白的信箱名稱:用雙引號
email move -a iCloud -m INBOX --id 42 \
  --dest-account iCloud --dest-mailbox "Sent Messages"
```

`--dest-account` 與 `--dest-mailbox` 皆必填;搬完輸出 `moved <id> -> <dest-account>/<dest-mailbox>`。

### `email send` — 寄信 (安全機制)

```bash
# 預設 dry-run:只印預覽,完全不接觸 Mail.app
email send \
  --to alice@example.com \
  --subject "Hello" \
  --body "Hi Alice" \
  --from-account iCloud

# 真的寄出 (必須兩個 flag 同時給)
email send --no-dry-run --yes \
  --to alice@example.com \
  --subject "Hello" \
  --body "Hi Alice" \
  --from-account iCloud

# 多行 body:用 $'...\n...' 或 heredoc
email send \
  --to alice@example.com \
  --subject "Report" \
  --body $'Hi Alice,\n\n本週進度如下:\n- 完成 A\n- 進行 B\n\n--\nShuk' \
  --from-account iCloud
```

| Flag                       | 必填 | 預設        | 說明                                      |
| -------------------------- | ---- | ----------- | ----------------------------------------- |
| `--to`                     | ✓    | —           | 單一收件人 (TO);目前不支援 CC/BCC         |
| `--subject`                | ✓    | —           | 主旨                                      |
| `--body`                   | ✓    | —           | 內文 (純文字)                             |
| `--from-account`           | ✓    | —           | 寄送帳號名稱 (對應 `email accounts` 結果) |
| `--dry-run / --no-dry-run` | —    | `--dry-run` | 預設預覽不送                              |
| `--yes`                    | —    | False       | 配合 `--no-dry-run` 才真正寄出            |

`安全機制 (Safety gate):`

| `--dry-run / --no-dry-run` | `--yes` | 行為                               |
| -------------------------- | ------- | ---------------------------------- |
| `--dry-run` (預設)         | —       | 印預覽,完全不送                    |
| `--no-dry-run`             | (缺)    | `ClickException`,拒絕送            |
| `--no-dry-run`             | `--yes` | 真的送出,輸出 `SENT (id=<msg_id>)` |

## Output Formats

| 格式                     | 觸發            | 適用場景       |
| ------------------------ | --------------- | -------------- |
| 預設 (rich 表格 / panel) | 不加 flag       | 終端機人讀     |
| JSON                     | `--json` / `-j` | LLM / 腳本消費 |

只有 `accounts`、`mailboxes`、`list` 支援 `--json`;`show`、`mark`、`move`、`send` 沒有 JSON 輸出。

## Exit Codes

| Code  | 意義                                                                             |
| ----- | -------------------------------------------------------------------------------- |
| `0`   | 成功                                                                             |
| `1`   | `ClickException` (例:`message id N not found`、`refusing to send without --yes`) |
| `2`   | `UsageError` (例:`mark` 沒給任何 read/flag flag、缺必填參數)                     |
| `130` | 使用者中斷 (Ctrl+C)                                                              |

## Common Mistakes

| 錯誤                                                | 修正                                                                                                   |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 加 `--no-dry-run` 但忘了 `--yes`                    | 兩個一定要同時給;只給 `--no-dry-run` 會被拒絕                                                          |
| 用 `--dry-run --yes` 期待會寄出                     | `dry-run` 永遠不送;要寄必須改為 `--no-dry-run --yes`                                                   |
| 帳號 / 信箱名稱大小寫不符                           | 先 `email accounts` / `email mailboxes -a X` 確認確切名稱                                              |
| 含空白的信箱名稱沒 quote                            | `--mailbox "Sent Messages"`,別寫成 `--mailbox Sent Messages`                                           |
| 拿 `email list` 表格的 ID 直接用,但碰到表格輸出截斷 | 改用 `--json` 取得完整 ID 與所有欄位                                                                   |
| `email show --id N` 找不到                          | ID 是該信箱內的 ID,跨信箱不通用;先 `email list -a A -m M` 確認                                         |
| 期望 `email send` 支援 CC/BCC                       | 目前不支援,只有 TO;暫時改在 `Mail.app` UI 操作                                                         |
| 期望 `email reply` 或 `email forward`               | 目前不支援,僅能 `send` 全新郵件                                                                        |
| 期待 `email draft` 指令                             | 原始碼有 `draft.py` 但未在 `cli.py` 註冊,實際不可呼叫;若需要,可在 `cli.py` 加 `cli.add_command(draft)` |
| 大信箱 `email show` 慢                              | `show` 會 load 整個信箱再 filter;改用 Python API 或縮小 mailbox                                        |

## Composing with Other Tools

```bash
# 用 jq 取 ID
email list -a iCloud -m INBOX --unread --json | jq -r '.[].id'

# 用未讀數量觸發 macOS 通知
n=$(email list -a iCloud -m INBOX --unread --json | jq 'length')
[ "$n" -gt 0 ] && osascript -e "display notification \"$n unread\" with title \"Mail\""

# 把指定主旨的信全部歸檔
email list -a iCloud -m INBOX --subject "Newsletter" --json \
  | jq -r '.[].id' \
  | while read id; do
      email move -a iCloud -m INBOX --id "$id" \
        --dest-account iCloud --dest-mailbox "Newsletters"
    done

# 取 source 後丟給 ripmime / mhonarc / 自家解析器
email show -a iCloud -m INBOX --id 42 --source | head -50
```

## See Also

- 專案 README:[`README.md`](../../README.md)
- CLI 入口:`macemailapp/cli/cli.py`
- 指令實作目錄:`macemailapp/cli/commands/`
- Python API 對應實作:`macemailapp/mailapp.py`
- AppleScript handlers:`macemailapp/macmailapp.applescript`

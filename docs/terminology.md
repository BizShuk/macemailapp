# macmailapp — 術語表 (Terminology)

本檔是領域名詞、狀態值與縮寫的單一定義來源。CLI、Python API 與文件使用同一組正名。

## 郵件領域模型 (Mail Domain Model)

| 術語 (Term) | 英文 (English) | 定義 (Definition) | 出處 (Source) |
| --- | --- | --- | --- |
| 郵件應用 | Mail App | Apple Mail.app 的程式化入口，是所有操作的起點 | `MailApp`、`mailapp.py` |
| 帳號 | Account | Mail.app 中設定的一個郵件帳號 | `Account` |
| 信箱 | Mailbox | 帳號下的資料夾，例如收件匣、寄件備份 | `Mailbox` |
| 訊息 | Message | 一封郵件；屬性以惰性方式從 SBObject 取出 | `Message` |
| 草稿 | Draft | 尚未寄出、儲存在 Mail.app 中的郵件 | `cli/commands/draft.py` |

## 存取機制 (Access Mechanisms)

macOS 自動化有兩條路徑，本專案`刻意`依動作性質分開使用：

| 術語 (Term) | 英文 (English) | 定義 (Definition) | 使用時機 |
| --- | --- | --- | --- |
| ScriptingBridge | ScriptingBridge | Objective-C 橋接層，以物件方式存取 Mail.app | `讀取`路徑：帳號、信箱、訊息查詢 |
| AppleScript | AppleScript | 以腳本語言驅動 Mail.app | `寫入`路徑：標記、移動、寄送；ScriptingBridge 在寫入時較不穩定 |
| 述詞過濾 | NSPredicate | 在 ScriptingBridge 層就完成的訊息過濾條件，避免把整個信箱拉進記憶體 | `Mailbox.messages()` |
| 腳本載入器 | Script Loader | 執行 AppleScript 的包裝層 | `script_loader.run_script()` |
| 嵌入腳本 | Embedded Script | AppleScript 原始碼被轉成 Python 字串常數的形式，供發佈時免除外部檔案相依 | `macemailapp_applescript.py` 的 `MAIL_APPLESCRIPT` |

> `維護規則`：`macmailapp.applescript` 是人工編輯的原始碼，
> `macemailapp_applescript.py` 是它的嵌入版本。改了前者必須同步後者，否則執行的是舊行為。

## 業務領域 (Business Domains)

| 領域 (Domain) | 定義 (Definition) | 相關處理器 (Handlers) |
| --- | --- | --- |
| 帳號與信箱瀏覽 | 列出帳號與其下信箱名稱與訊息數，是其他操作的前置步驟 | `accounts()`、`mailboxes()` |
| 郵件讀取與搜尋 | 信箱內的列表查詢與單封郵件完整內容顯示 | `list_messages()`、`show()` |
| 郵件狀態變更與移動 | 已讀/未讀、加星/取消加星、跨信箱與跨帳號移動 | `mark()`、`move()` |
| 郵件撰寫與寄送 | 建立草稿與實際寄出；寄送路徑帶安全防護 | `draft()`、`send()` |

## 輸出與慣例 (Output and Conventions)

| 術語 (Term) | 英文 (English) | 定義 (Definition) | 出處 (Source) |
| --- | --- | --- | --- |
| 表格輸出 | Rich Table | 給人閱讀的預設輸出格式 | `rich`、`cli_help.py` |
| JSON 輸出 | JSON Output | 給腳本與 LLM workflow 使用的結構化輸出 | 各 command 的 `--json` |
| 日誌開關 | Log Switch | 以環境變數 `MACEMAILAPP_LOG` 控制的統一 logger | `logging.py` |

## 命名注意事項 (Naming Caveat)

`目錄名、套件名、產品名三者不同`，文件中務必分辨：

- 目錄與 repo 名：`macemailapp`
- Python 套件名：`macemailapp`
- 產品／README 標題名：`macmailapp`（少一個 `e`）
- CLI 命令名：`mail`

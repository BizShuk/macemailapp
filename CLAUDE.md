# macmailapp — 技術脈絡 (Technical Context)

## 專案結構 (Project Structure)

```
macemailapp/
├── macemailapp/                        # 核心套件
│   ├── __init__.py                     # 公開 API: MailApp, Account, Mailbox, Message
│   ├── __main__.py                     # CLI 進入點: cli_main()
│   ├── _version.py                     # 版本號: __version__ = "0.1.0"
│   ├── logging.py                      # 統一 logger (MACEMAILAPP_LOG env)
│   ├── utils.py                        # NSDate_to_datetime, get_macos_version, OSType
│   ├── script_loader.py                # run_script() 包裝 py-applescript
│   ├── macmailapp.applescript          # AppleScript 原始碼 (人工編輯用)
│   ├── macemailapp_applescript.py      # AppleScript 嵌入為 Python str (MAIL_APPLESCRIPT)
│   ├── mailapp.py                      # 領域模型: MailApp / Account / Mailbox / Message
│   └── cli/
│       ├── cli.py                      # click group + 指令註冊
│       ├── cli_help.py                 # RichHelpCommand
│       └── commands/
│           ├── accounts.py             # mail accounts
│           ├── mailboxes.py            # mail mailboxes
│           ├── list_messages.py        # mail list
│           ├── show.py                 # mail show
│           ├── mark.py                 # mail mark
│           ├── move.py                 # mail move
│           ├── draft.py                # mail draft
│           └── send.py                 # mail send (含安全防護)
├── tests/
│   ├── conftest.py                     # mail_app fixture
│   ├── test_applescript_read.py        # AppleScript read handler 測試
│   ├── test_applescript_write.py       # AppleScript write handler 測試
│   ├── test_mailapp_read.py            # MailApp/Account/Mailbox/Message 讀取測試
│   ├── test_mailapp_write.py           # Message 寫入操作測試
│   ├── test_cli_read.py                # CLI 讀取指令測試
│   ├── test_cli_write.py               # CLI 寫入指令測試
│   ├── test_send_safety.py             # send 安全防護測試
│   └── test_utils.py                   # utils 單元測試
├── HomebrewFormula/macmailapp.rb       # Homebrew formula scaffold
├── plans/                              # 實作計畫文件
├── pyproject.toml                      # 套件設定 (hatchling)
├── .bumpversion.cfg                    # bump2version 版本管理設定
└── uv.lock                             # uv 鎖定檔
```

## 技術棧 (Tech Stack)

- Language: Python 3.10–3.13
- Framework: `click` (CLI), `rich` (終端機輸出)
- Build tool: `hatchling` + `uv`
- Distribution: `PyInstaller` (standalone binary) + Homebrew formula
- Key dependencies:
  - `pyobjc-framework-ScriptingBridge` — 直接呼叫 Mail.app Objective-C API (讀取為主)
  - `py-applescript` — 執行嵌入式 AppleScript (寫入操作)
  - `AppKit` (via pyobjc) — `NSPredicate` 過濾、`NSDate` 轉換
  - `markdown2` + `markdownify` + `lxml` — 郵件內容 HTML/Markdown 轉換 (未來擴充用)
  - `bump2version` — 版本號管理 (`_version.py` + `pyproject.toml` 同步更新)

## 關鍵決策 (Key Decisions)

- 雙軌存取架構 (Two-track access): 讀取優先使用 `ScriptingBridge` (效能好、NSPredicate 過濾)，寫入操作使用嵌入式 AppleScript (ScriptingBridge 在寫入時行為不穩定)
- AppleScript 嵌入為 Python str: `macemailapp_applescript.py` 以 `MAIL_APPLESCRIPT = r"""..."""` 方式嵌入，因 `py-applescript.AppleScript()` 需要 Python str，避免 UTF-8 guillemet 解碼問題；`macmailapp.applescript` 為人工編輯的同步參考檔
- `send` 雙重確認安全設計: `send` 指令預設 `--dry-run=True`，即使加上 `--no-dry-run` 也必須同時傳入 `--yes`，防止兩步驟操作中途誤送
- 每個 CLI 指令獨立一個檔案: `commands/send.py` (唯一破壞性操作) 可單獨被 code review，符合最小化審查範圍的設計原則
- `Message.id` fallback 解析: ScriptingBridge 回傳的 SBObject 有時 `id()` 返回 0，需以正規表達式從物件字串表示中解析 `id \d+ of application "Mail"`
- `cached_property` 用於 `Account.mailboxes`: 避免重複呼叫 ScriptingBridge 的 `mailboxes()` 影響效能

## 模組對應 (Module Mapping)

| 業務領域 (Domain) | 套件/模組 (Package/Module) | 進入點 (Entry Point) |
| --- | --- | --- |
| 郵件帳號與信箱瀏覽 | `mailapp.py`, `cli/commands/accounts.py`, `cli/commands/mailboxes.py` | `accounts()`, `mailboxes()` |
| 郵件讀取與搜尋 | `mailapp.py`, `cli/commands/list_messages.py`, `cli/commands/show.py` | `list_messages()`, `show()` |
| 郵件狀態變更與移動 | `mailapp.py`, `macemailapp_applescript.py`, `cli/commands/mark.py`, `cli/commands/move.py` | `mark()`, `move()` |
| 草稿撰寫與安全傳送 | `mailapp.py`, `macemailapp_applescript.py`, `cli/commands/draft.py`, `cli/commands/send.py` | `draft()`, `send()` |

## 開發指南 (Development Guide)

### 前置需求 (Prerequisites)

- macOS (需要 Apple Mail.app)
- Python 3.10–3.13
- `uv` 套件管理工具
- 首次執行時需在「系統設定 → 隱私權與安全性 → 自動化」批准 Mail.app 存取權限

### 安裝 (Installation)

```bash
# 開發模式安裝
uv sync

# 工具模式安裝 (正式使用)
uv tool install --python 3.13 macmailapp
```

### 建置 (Build)

```bash
# 建置 Python wheel
uv build

# 建置 standalone binary (PyInstaller)
cd macemailapp && bash build.sh
# 產出: macemailapp/dist/mail.zip
```

### 測試 (Test)

```bash
# 執行所有測試 (需要 Mail.app 與至少一個郵件帳號)
uv run pytest tests/ -v

# 只執行 utils 單元測試 (不需要 Mail.app)
uv run pytest tests/test_utils.py -v
```

注意: 大部分測試需要 macOS 上的 Mail.app 與已設定的郵件帳號，CI 環境無法直接執行。

### 版本更新 (Version Bump)

```bash
# 更新 patch 版本 (_version.py 與 pyproject.toml 同步更新)
uv run bump2version patch
```

### 部署 (Deploy)

1. 執行 `build.sh` 產出 `dist/mail.zip`
2. 建立 GitHub Release，上傳 `mail.zip`
3. 計算 sha256: `sha256sum dist/mail.zip`
4. 更新 `HomebrewFormula/macmailapp.rb` 中的 `sha256` 與 `version`

## 慣例 (Conventions)

- Naming: 類別使用 PascalCase (`MailApp`, `Account`)，CLI 函式使用 snake_case，AppleScript handler 使用 camelCase (`mailGetAccounts`, `createDraft`)
- Error handling: 使用 `click.ClickException` 從 CLI 層拋出使用者可見的錯誤；底層使用標準 `ValueError` 與自訂 `ScriptingBridgeError`
- Logging: 透過 `macemailapp/logging.py` 的單一 `logger`，預設 WARNING 等級，可透過 `MACEMAILAPP_LOG=DEBUG` 環境變數控制
- Testing: TDD 流程，先寫失敗測試再實作；測試分類: `test_applescript_*` (AppleScript 層)、`test_mailapp_*` (Python API 層)、`test_cli_*` (CLI 層)、`test_send_safety.py` (安全防護層)

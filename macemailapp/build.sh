#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

rm -rf dist build
uv build
uv run pyinstaller macmailapp.spec --noconfirm
cd dist && zip -r mail.zip mail && cd ..
echo "dist/mail.zip ready"
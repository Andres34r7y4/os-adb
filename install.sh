#!/usr/bin/env bash
# OS-ADB one-shot installer: creates .venv + installs CLI + seeds demo data
set -e
cd "$(dirname "$0")"

echo "🛠️  OS-ADB installer"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e ".[dev]" -q

echo "✔ Installed. Seeding demo data..."
.venv/bin/adb seed || true
echo ""
echo "Try:"
echo "  source .venv/bin/activate"
echo "  adb list            # if installed as script"
echo "  adb list                  # via ~/.local/bin symlink"
echo "  adb                       # TUI mode"
echo "  make demo test"

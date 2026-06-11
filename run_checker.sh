#!/bin/bash
# Script to run the checker with optional message_id for Telegram reply/citation
# Usage: bash run_checker.sh [message_id]
# When message_id is provided, the checker will quote (reply to) that message in Telegram

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 checker.py "$@"

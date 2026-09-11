#!/bin/bash
set -e
if [ -f apply_updates.py ]; then
  python apply_updates.py || true
fi
if [ -f runtime_patch.py ]; then
  python runtime_patch.py || true
fi
if [ -f chat_install.py ]; then
  python chat_install.py || true
fi
exec python app.py

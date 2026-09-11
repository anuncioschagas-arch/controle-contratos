#!/bin/bash
set -e
if [ -f apply_updates.py ]; then
  python apply_updates.py || true
fi
if [ -f runtime_patch.py ]; then
  python runtime_patch.py || true
fi
exec python app.py

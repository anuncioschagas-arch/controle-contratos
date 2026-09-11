#!/bin/bash
set -e
if [ -f apply_updates.py ]; then
  python apply_updates.py || true
fi
if [ -f runtime_patch.py ]; then
  python runtime_patch.py || true
fi
if [ ! -f app.py ] && [ -f join_bootstrap.py ]; then
  python join_bootstrap.py || true
fi
if [ ! -f app.py ] && [ -f bootstrap_extract.py ]; then
  python bootstrap_extract.py || true
fi
exec python app.py

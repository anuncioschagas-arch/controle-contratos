#!/bin/bash
set -e
if [ ! -f app.py ] || [ -f bootstrap_extract.py ]; then
  if [ -f bootstrap_extract.py ]; then
    python bootstrap_extract.py
  fi
fi
exec python app.py

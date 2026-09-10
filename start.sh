#!/bin/bash
set -e
if [ ! -f app.py ]; then
  if [ -f join_bootstrap.py ]; then
    python join_bootstrap.py
  elif [ -f bootstrap_extract.py ]; then
    python bootstrap_extract.py
  fi
fi
exec python app.py

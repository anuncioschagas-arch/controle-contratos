#!/usr/bin/env python3
import base64, zlib, json, os
from pathlib import Path
parts = sorted(Path(".").glob("full_part_*.txt"))
if not parts:
    parts = sorted(Path(".").glob("upd_part_*.txt"))
if parts:
    blob = "".join(p.read_text() for p in parts)
    data = json.loads(zlib.decompress(base64.b64decode(blob)))
    for path, content in data.items():
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        print("updated", path)
    print("full updates applied", len(data), "files")
else:
    print("no payload parts found")

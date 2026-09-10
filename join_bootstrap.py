#!/usr/bin/env python3
"""Junta as partes do bootstrap e extrai o app."""
from pathlib import Path
parts = sorted(Path('.').glob('blob_part_*.txt'))
if not parts:
    raise SystemExit('blob_part_*.txt nao encontrados')
blob = ''.join(p.read_text() for p in parts)
code = '#!/usr/bin/env python3\nimport base64, zlib, json, os\nBLOB = """' + blob + '"""\ndata = json.loads(zlib.decompress(base64.b64decode(BLOB)))\nfor path, content in data.items():\n    d = os.path.dirname(path)\n    if d:\n        os.makedirs(d, exist_ok=True)\n    with open(path, "w", encoding="utf-8") as f:\n        f.write(content)\n    print("wrote", path)\nprint("OK")\n'
Path('bootstrap_extract.py').write_text(code)
print('bootstrap_extract.py gerado')
exec(compile(code, 'bootstrap_extract.py', 'exec'))

#!/usr/bin/env python3
"""Test the optional reader patch against its reviewed upstream source in /tmp."""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen

from apply_reader_search import BASE_SHA256, PATCHED_SHA256, PREVIOUS_SHA256, apply

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://raw.githubusercontent.com/bookorbit/bookorbit/c0759ea1bf6bd591f40ee0f82e7f109e480ef264/koreader-plugin/bookorbit.koplugin/bookorbit_catalog.lua'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--catalog', type=Path, help='use a local unmodified catalog instead of downloading the pinned source')
parser.add_argument('--lua', default='lua5.1')
args = parser.parse_args()
if args.catalog:
    original = args.catalog.read_bytes()
else:
    with urlopen(UPSTREAM, timeout=30) as response:
        original = response.read()
assert hashlib.sha256(original).hexdigest() == BASE_SHA256, 'Upstream fixture differs from the reviewed source'
with tempfile.TemporaryDirectory(prefix='bookorbit-reader-search-') as tmp:
    catalog = Path(tmp) / 'bookorbit_catalog.lua'
    catalog.write_bytes(original)
    apply(Path(tmp))
    patched = catalog.read_bytes()
    assert hashlib.sha256(patched).hexdigest() == PATCHED_SHA256
    apply(Path(tmp))
    assert catalog.read_bytes() == patched, 'Reapplying changed the catalog'
    subprocess.run([args.lua, str(ROOT / 'scripts/test_reader_search.lua'), str(catalog)], check=True)
    subprocess.run(['git','apply','--reverse',str(ROOT/'patches/bookorbit-kindlefetch-import-upgrade.patch')],cwd=tmp,check=True)
    assert hashlib.sha256(catalog.read_bytes()).hexdigest()==PREVIOUS_SHA256
    apply(Path(tmp))
    assert catalog.read_bytes()==patched, 'Upgrading the previous patch produced different bytes'
    catalog.write_bytes(original + b'\n-- another local modification\n')
    try:
        apply(Path(tmp))
    except SystemExit:
        pass
    else:
        raise AssertionError('Modified upstream source was not rejected')
    assert catalog.read_bytes() == original + b'\n-- another local modification\n'
print('PASS: reader patch applies to reviewed upstream, is idempotent, and refuses unknown versions')

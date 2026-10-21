#!/usr/bin/env python3
"""Apply the optional Kindle Fetch search bridge to BookOrbit's reader plugin.

Accept a bookorbit.koplugin directory or the pinned BookOrbit source checkout.
Only the reviewed 1.5.5 catalog file is supported; settings are never touched.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA256 = 'c15250c6481652334b81d780fc49d40346260555cb036df25e92822a8a4661c4'
# Filled from the reviewed patch; verifies idempotency as well as output bytes.
PATCHED_SHA256 = '2849b9b3c78ca3f8f3e08aab1eb69f6a5b9962fdb493bca49a4d33d524d05509'


def apply(source: Path):
    source = source.resolve()
    plugin = source if (source / 'bookorbit_catalog.lua').is_file() else source / 'koreader-plugin' / 'bookorbit.koplugin'
    catalog = plugin / 'bookorbit_catalog.lua'
    if not catalog.is_file():
        raise SystemExit('BookOrbit reader plugin not found at this path.')
    digest = hashlib.sha256(catalog.read_bytes()).hexdigest()
    if digest == PATCHED_SHA256:
        print('Reader search bridge already applied.')
        return
    if digest != BASE_SHA256:
        raise SystemExit('Unsupported or modified catalog. This patch requires the reviewed BookOrbit plugin 1.5.5; preserve your current files.')
    patch = ROOT / 'patches' / 'bookorbit-kindlefetch-search.patch'
    command = ['git', 'apply']
    subprocess.run(command + ['--check', str(patch)], cwd=plugin, check=True)
    subprocess.run(command + [str(patch)], cwd=plugin, check=True)
    if hashlib.sha256(catalog.read_bytes()).hexdigest() != PATCHED_SHA256:
        raise SystemExit('Unexpected patched file hash; do not deploy it.')
    print('Reader search bridge applied. Install Kindle Fetch 0.9.1+ and restart KOReader.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)

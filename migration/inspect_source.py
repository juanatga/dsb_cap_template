"""Print source fingerprints and cell summaries to help an instructor write a mapping."""
import argparse
import json
from pathlib import Path
from common import inventory, source

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    a = p.parse_args()
    root = Path(a.source)
    for name, fingerprint in inventory(root).items():
        print(json.dumps({'source': name, 'sha256': fingerprint, 'bytes': (root/name).stat().st_size}))
        if name.endswith('.ipynb'):
            for i,c in enumerate(json.loads((root/name).read_text())['cells']):
                print(f'  {i:04d} {c["cell_type"]}: {source(c)[:160].replace(chr(10), " | ")}')

"""Shared format, path and inventory helpers; no student code is executed."""
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

LIMIT = 25_000_000
EDA = ['TL;DR', 'Introduction & motivation', 'Data provenance', 'Data dictionary', 'Setup', 'First look', 'Data quality audit', 'Univariate exploration', 'Bivariate exploration', 'Key findings', 'Decisions carried forward', 'Export', 'Appendix']
MODEL = ['TL;DR', 'Recap of the goal', 'Setup & data loading', 'Feature preparation', 'Train/test split', 'Baseline model', 'Candidate models', 'Evaluation & comparison', 'Error analysis', 'Interpretation', 'Limitations & ethics', 'Conclusion & next steps']
NOTEBOOKS = {'notebooks/01_eda.ipynb': EDA, 'notebooks/02_modelling.ipynb': MODEL}
README_HEADINGS = ['The problem', 'Key result', 'The data', 'How to navigate this repo', 'How to reproduce', 'Repository structure', 'Author & credits', 'License']
REQUIRED = ['README.md', 'SETUP.md', 'REVIEW_CHECKLIST.md', 'LICENSE', 'requirements.txt', '.gitignore', 'data/README.md', 'data/raw/README.md', 'data/processed/README.md', 'docs/README.md', *NOTEBOOKS]
MANUAL = ['fresh_local_run', 'fresh_colab_run', 'data_provenance_and_permissions', 'baseline_and_evaluation', 'chart_labels_and_captions', 'plain_language_and_decisions', 'limitations_and_ethics', 'public_reader_test']


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def safe(root, name):
    if not isinstance(name, str):
        raise ValueError('Relative path must be a string')
    p = PurePosixPath(name)
    if not name or p.as_posix() != name or name == '.' or p.is_absolute() or '..' in p.parts or '\\' in name or '.git' in p.parts:
        raise ValueError(f'Unsafe relative path: {name!r}')
    root = Path(root).resolve()
    target = root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError(f'Path leaves root: {name}')
    if any(part.is_symlink() for part in [target, *target.parents] if part != root.parent):
        raise ValueError(f'Symlink not supported: {name}')
    return target


def inventory(root, published=False):
    root = Path(root)
    included = None
    if published and (root / '.git').exists():
        result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root, capture_output=True, text=True, check=True)
        included = set(result.stdout.split('\0'))
    result = {}
    paths = (root / name for name in sorted(included) if name) if included is not None else sorted(root.rglob('*'))
    for p in paths:
        rel = p.relative_to(root).as_posix()
        if included is not None and rel not in included:
            continue
        if p.relative_to(root).parts[0] == '.git':
            continue
        if '.git' in p.relative_to(root).parts:
            raise ValueError(f'Nested Git repository requires manual handling: {rel}')
        if p.is_symlink():
            raise ValueError(f'Symlink requires manual handling: {rel}')
        if p.is_file():
            result[rel] = sha(p)
    return result


def digest(root):
    files = inventory(root, published=True)
    files.pop('.migration/review.json', None)
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def source(cell):
    s = cell.get('source', '')
    return ''.join(s) if isinstance(s, list) else s


def cell(kind, text, instruction=False):
    result = {'cell_type': kind, 'metadata': {}, 'source': text}
    if instruction:
        result['metadata']['tags'] = ['template-instruction']
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


def notebook(cells):
    for i, c in enumerate(cells):
        c['id'] = f'cell-{i:04d}'
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'cells': cells}


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')

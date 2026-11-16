"""Static checks, not an execution or scientific-quality certification."""
import argparse
import json
import re
from pathlib import Path
import nbformat
from common import LIMIT, MANUAL, NOTEBOOKS, README_HEADINGS, REQUIRED, digest, inventory, source


def validate(repo, mode='structure', artifact='draft'):
    repo = Path(repo)
    findings = []
    def add(path, message, level='error'):
        findings.append({'level': level, 'path': path, 'message': message})
    gap = 'error' if mode == 'readiness' else 'warning'
    try:
        files = inventory(repo, published=True)
    except ValueError as exc:
        return [{'level': 'error', 'path': '.', 'message': str(exc)}]
    for name in REQUIRED:
        if name not in files:
            add(name, 'Required file missing')
    for name in files:
        p = repo / name
        if p.stat().st_size > LIMIT:
            add(name, 'File exceeds 25,000,000 bytes; keep outside Git and document acquisition')
        if name.endswith('.ipynb'):
            if not name.startswith('notebooks/') or not re.match(r'notebooks/\d\d_[^/]+\.ipynb$', name):
                add(name, 'Notebook must live directly in notebooks/ with a two-digit prefix')
            try:
                raw = json.loads(p.read_text())
                nbformat.validate(raw)
                cells = raw['cells']
            except Exception as exc:
                add(name, f'Invalid notebook: {exc}')
                continue
            expected = NOTEBOOKS.get(name)
            headings = [source(c).strip() for c in cells if c['cell_type'] == 'markdown' and re.match(r'^## \d+\. ', source(c))]
            if expected and headings != [f'## {i}. {t}' for i, t in enumerate(expected, 1)]:
                add(name, 'Required numbered sections missing, duplicated, or out of order')
            for i, c in enumerate(cells):
                loc = f'{name}:cell {i}'
                s = source(c)
                if c['cell_type'] == 'code':
                    if i == 0 or cells[i-1]['cell_type'] != 'markdown' or not source(cells[i-1]).strip() or source(cells[i-1]).lstrip().startswith('## '):
                        add(loc, 'Add a plain-language Markdown explanation immediately before this code', gap)
                    if artifact == 'template':
                        if any(line.strip() and not line.lstrip().startswith('# TODO') for line in s.splitlines()):
                            add(loc, 'Template code must contain only TODO comments')
                        if c.get('outputs') or c.get('execution_count') is not None:
                            add(loc, 'Template must have no saved outputs or execution counts')
                    else:
                        if re.search(r'/content/|/Users/|/home/|[A-Za-z]:\\|drive\.mount\(', s):
                            add(loc, 'Machine-specific path or Drive mount in analysis code', gap)
                        if name.endswith('02_modelling.ipynb') and re.search(r'data[/\\]raw|\bRAW\s*[/\[]|https?://[^\s\"\']+\.(csv|parquet)', s):
                            add(loc, 'Possible raw/remote data loading in modelling; use processed inputs', gap)
                if artifact != 'template' and ('template-instruction' in c.get('metadata', {}).get('tags', []) or re.search(r'\bTODO\b|\{[A-Z][A-Z_ ]*\}', s)):
                    add(loc, 'Unfinished instruction or placeholder', gap)
        elif artifact != 'template' and (name.endswith('.md') or name == 'LICENSE') and name not in {'SETUP.md', 'REVIEW_CHECKLIST.md'}:
            s = p.read_text(errors='replace')
            if re.search(r'\{[A-Z][A-Z_ ]*\}|\bTODO\b|\*Replace this', s):
                add(name, 'Unfilled documentation placeholder', gap)
    readme = repo / 'README.md'
    if readme.exists():
        s = readme.read_text()
        if not re.search(r'^# .+', s, re.M):
            add('README.md', 'Missing project title')
        headings = re.findall(r'^## (.+)$', s, re.M)
        if headings[:8] != README_HEADINGS:
            add('README.md', 'Expected the eight section headings after the title, in specification order')
    req = repo / 'requirements.txt'
    if req.exists() and artifact != 'template':
        for line in req.read_text().splitlines():
            line = line.split('#')[0].strip()
            if line and not re.fullmatch(r'[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^\s*;]+', line):
                add('requirements.txt', f'Pin a tested package version: {line}', gap)
    state = repo / '.migration/state.json'
    if state.exists():
        try:
            st = json.loads(state.read_text())
            if st.get('version') != 1 or not st.get('mapping_sha256') or not st.get('source_inventory'):
                raise ValueError('Missing migration provenance')
            for book, record in st['cell_accounting'].items():
                if sorted(record['accounted']) != list(range(record['total'])):
                    raise ValueError(f'Incomplete cell accounting: {book}')
        except (ValueError, KeyError, TypeError) as exc:
            add('.migration/state.json', str(exc))
    if mode == 'readiness':
        review = repo / '.migration/review.json'
        try:
            evidence = json.loads(review.read_text())
        except (OSError, ValueError):
            evidence = {}
        current = digest(repo)
        if evidence.get('content_sha256') != current:
            add('.migration/review.json', f'Manual review missing or stale. Current content fingerprint: {current}')
        for key in MANUAL:
            item = evidence.get('checks', {}).get(key, {})
            if item.get('passed') is not True or not item.get('evidence', '').strip():
                add('.migration/review.json', f'Unverified manual check: {key}')
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--mode', choices=['structure', 'readiness'], default='structure')
    p.add_argument('--artifact', choices=['template', 'draft'], default='draft')
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    result = validate(a.repo, a.mode, a.artifact)
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result:
            print(f'{f["level"].upper()} {f["path"]}: {f["message"]}')
        print(f'{sum(f["level"] == "error" for f in result)} errors; {sum(f["level"] == "warning" for f in result)} warnings. Static checks do not execute notebooks.')
    return int(any(f['level'] == 'error' for f in result))


if __name__ == '__main__':
    raise SystemExit(main())

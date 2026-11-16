"""Build a mapped draft in a NEW directory. Never mutate the source."""
import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
import jsonschema
import nbformat
from common import LIMIT, NOTEBOOKS, cell, inventory, notebook, safe, sha, source, write_json
from validate import validate


def inspect(source_dir, mapping_path, template):
    src, template = Path(source_dir).resolve(), Path(template).resolve()
    m = json.loads(Path(mapping_path).read_text())
    schema = json.loads(Path(__file__).with_name('mapping.schema.json').read_text())
    try:
        jsonschema.Draft202012Validator(schema).validate(m)
    except jsonschema.ValidationError as exc:
        raise ValueError(f'Invalid mapping at {list(exc.absolute_path)}: {exc.message}') from exc
    if m.get('version') != 1:
        raise ValueError('Unsupported mapping version; expected 1')
    actual = inventory(src)
    entries = m.get('files', [])
    paths = [e['source'] for e in entries]
    if len(paths) != len(set(paths)):
        raise ValueError('Each source file must appear exactly once')
    if set(paths) != set(actual):
        raise ValueError(f'Unclassified files: {sorted(set(actual)-set(paths))}; missing files: {sorted(set(paths)-set(actual))}')
    template_files = inventory(template)
    actions, accounting, destinations = [], {}, set()
    for e in entries:
        name = e['source']
        p = safe(src, name)
        if e.get('sha256') != actual[name]:
            raise ValueError(f'Stale mapping for {name}; regenerate and review mapping')
        action = e.get('action')
        if action not in {'keep', 'copy', 'remove', 'notebook'}:
            raise ValueError(f'Unknown action for {name}: {action}')
        if not e.get('reason', '').strip():
            raise ValueError(f'Explain action for {name}')
        if name.endswith('.ipynb') and action != 'notebook':
            raise ValueError('All source notebooks require cell accounting via action=notebook')
        if action in {'copy', 'keep'}:
            target = name if action == 'keep' else e['target']
            safe(template, target)
            if target.endswith('.ipynb'):
                raise ValueError('Notebook targets require action=notebook')
            if target.startswith('.migration/') or target in destinations:
                raise ValueError(f'Reserved or duplicate target: {target}')
            if target in template_files and not e.get('replace_template'):
                raise ValueError(f'Explicit replace_template required: {target}')
            if p.stat().st_size > LIMIT:
                raise ValueError(f'{name} exceeds 25 MB; map as remove and document acquisition')
            destinations.add(target)
        if action == 'notebook':
            n = json.loads(p.read_text())
            nbformat.validate(n)
            count = len(n['cells'])
            used = []
            for b in e.get('blocks', []):
                target = b['target']
                if target not in NOTEBOOKS or not 1 <= b['section'] <= len(NOTEBOOKS[target]):
                    raise ValueError(f'Invalid notebook section: {b}')
                for c in b.get('cells', []):
                    if 'index' in c:
                        index = c['index']
                        if type(index) is not int or not 0 <= index < count:
                            raise ValueError(f'Invalid source cell index: {index}')
                        used.append(index)
                        text = source(n['cells'][index])
                        for change in c.get('replace', []):
                            if text.count(change['old']) != 1:
                                raise ValueError(f'Replacement must match exactly once: {name} cell {index}')
                            text = text.replace(change['old'], change['new'])
                    elif c.get('type') not in {'markdown', 'code'} or not isinstance(c.get('text'), str):
                        raise ValueError('Inserted cells need type and text')
                    if 'index' not in c and not c.get('reason'):
                        raise ValueError('Inserted cells need a reason')
            for omission in e.get('omit', []):
                if not omission.get('reason'):
                    raise ValueError('Omitted cells need a reason')
                used.append(omission['index'])
            if sorted(used) != list(range(count)):
                raise ValueError(f'Every cell must be mapped or omitted exactly once: {name}')
            accounting[name] = {'total': count, 'accounted': sorted(used), 'blocks': e.get('blocks', []), 'omit': e.get('omit', [])}
        actions.append({'source': name, 'action': action, 'target': e.get('target', name if action == 'keep' else None), 'reason': e['reason']})
    for name, text in m.get('documents', {}).items():
        safe(template, name)
        if name.startswith('.migration/') or name.endswith('.ipynb') or name in destinations or not isinstance(text, str):
            raise ValueError(f'Invalid/duplicate document target: {name}')
        destinations.add(name)
    for dependency in m.get('dependencies', []):
        import re
        if not re.fullmatch(r'[A-Za-z0-9_.-]+(?:==[A-Za-z0-9_.+-]+)?', dependency):
            raise ValueError(f'Invalid dependency: {dependency}')
    return m, {'version': 1, 'mapping_sha256': sha(mapping_path), 'source_inventory': actual, 'template_inventory': template_files, 'actions': actions, 'cell_accounting': accounting, 'notes': m.get('notes', []), 'status': 'draft; analysis not executed'}


def build(source_dir, mapping_path, template, output, dry_run=False):
    src, template, output = Path(source_dir).resolve(), Path(template).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Output already exists; choose a new directory. Never regenerate over student edits.')
    if output.with_name(output.name + '-report.json').exists():
        raise ValueError('Report already exists; choose a new output directory name')
    if output.is_relative_to(src) or output.is_relative_to(template) or src.is_relative_to(output) or template.is_relative_to(output):
        raise ValueError('Source, template, and output must be separate directories')
    m, report = inspect(src, mapping_path, template)
    if dry_run:
        return report
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.draft-', dir=output.parent) as temp:
        draft = Path(temp) / 'repo'
        shutil.copytree(template, draft)
        groups = {}
        for e in m['files']:
            p = safe(src, e['source'])
            if e['action'] in {'keep', 'copy'}:
                target = e['source'] if e['action'] == 'keep' else e['target']
                dest = safe(draft, target)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)
            elif e['action'] == 'notebook':
                original = json.loads(p.read_text())
                for block in e.get('blocks', []):
                    group = groups.setdefault((block['target'], block['section']), [])
                    for spec in block.get('cells', []):
                        if 'index' in spec:
                            old = original['cells'][spec['index']]
                            c = cell(old['cell_type'], source(old))
                            if old.get('attachments'):
                                c['attachments'] = copy.deepcopy(old['attachments'])
                            text = source(c)
                            for change in spec.get('replace', []):
                                if not change.get('reason') or not change['old'] or text.count(change['old']) != 1:
                                    raise ValueError(f'Replacement must match exactly once and give reason: {e["source"]} cell {spec["index"]}')
                                text = text.replace(change['old'], change['new'])
                            c['source'] = text
                        else:
                            c = cell(spec['type'], spec['text'], spec.get('instruction', False))
                        if c['cell_type'] not in {'markdown', 'code'}:
                            raise ValueError('Raw cells need an explicit omission or manual conversion')
                        if c['cell_type'] == 'code' and (not group or group[-1]['cell_type'] != 'markdown' or not source(group[-1]).strip() or source(group[-1]).lstrip().startswith('#')):
                            group.append(cell('markdown', '*Replace this with what the following code does and why it matters.*', True))
                        group.append(c)
        for target, titles in NOTEBOOKS.items():
            original = json.loads((draft / target).read_text())
            sections, current = {}, 0
            for c in original['cells'][1:]:
                if c['cell_type'] == 'markdown' and source(c).startswith('## '):
                    current += 1
                sections.setdefault(current, []).append(c)
            cells = [original['cells'][0]]
            for i in range(1, len(titles)+1):
                cells.extend([sections[i][0], *groups[(target, i)] ] if (target, i) in groups else sections[i])
            write_json(draft / target, notebook(cells))
        for name, text in m.get('documents', {}).items():
            dest = safe(draft, name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text.rstrip()+'\n')
        if m.get('dependencies'):
            with (draft / 'requirements.txt').open('a') as f:
                f.write('\n# Additional packages from the instructor mapping; verify and pin versions.\n')
                existing = {line.split('#')[0].split('==')[0].strip().lower() for line in (draft/'requirements.txt').read_text().splitlines()}
                for dep in m['dependencies']:
                    if dep.split('==')[0].lower() not in existing:
                        f.write(dep+'\n')
                        existing.add(dep.split('==')[0].lower())
        write_json(draft / '.migration/state.json', report)
        findings = validate(draft)
        if any(f['level'] == 'error' for f in findings):
            raise ValueError('Generated structure invalid: '+json.dumps(findings))
        # Check again before publish, so changed inputs cannot silently escape fingerprint validation.
        if inventory(src) != report['source_inventory'] or inventory(template) != report['template_inventory']:
            raise ValueError('Inputs changed during generation; retry after reviewing')
        draft.rename(output)
    write_json(output.parent / (output.name + '-report.json'), {**report, 'validation': findings})
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'mapping', 'template', 'output']:
        p.add_argument('--'+name, required=True)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    try:
        print(json.dumps(build(a.source, a.mapping, a.template, a.output, a.dry_run), indent=2))
    except (ValueError, KeyError, OSError) as exc:
        p.exit(1, f'Migration stopped: {exc}\n')


if __name__ == '__main__':
    main()

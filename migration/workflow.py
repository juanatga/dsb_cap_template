"""Branch operations used by the Colab launcher; never reset or force-push."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from common import LIMIT, inventory, safe
from migrate import build
from validate import validate

BRANCH = 'tidy_work'


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.returncode:
        raise ValueError(f'{args[0]} operation failed: {p.stderr.strip() or p.stdout.strip()}')
    return p.stdout.strip()


def git(repo, *args):
    return run(['git', *args], cwd=repo)


def github_url(url):
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?', url.strip())
    if not match or any(x in {'.', '..'} for x in match.groups()):
        raise ValueError('Enter an HTTPS GitHub repository URL, without credentials, branch, or notebook path')
    return f'https://github.com/{match[1]}/{match[2]}.git'


def clean(repo):
    if git(repo, 'status', '--porcelain'):
        raise ValueError('Unsaved local changes: review/save them before syncing or migrating')


def exists(repo, ref):
    return subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref], cwd=repo, capture_output=True).returncode == 0


def on_branch(repo):
    if git(repo, 'branch', '--show-current') != BRANCH:
        raise ValueError('Operation allowed only on tidy_work; main will not be modified')


def sync(repo):
    on_branch(repo)
    clean(repo)
    git(repo, 'fetch', 'origin')
    remote = f'origin/{BRANCH}'
    if exists(repo, remote):
        ahead, behind = map(int, git(repo, 'rev-list', '--left-right', '--count', f'HEAD...{remote}').split())
        if behind and ahead:
            raise ValueError('Local and remote work diverged. Ask your instructor to reconcile; no reset was performed.')
        if behind:
            git(repo, 'merge', '--ff-only', remote)


def prepare(url, checkout):
    """url may be a local remote for tests; launcher enforces github_url first."""
    repo = Path(checkout).resolve()
    if not repo.exists():
        run(['git', 'clone', '--', url, str(repo)])
    if git(repo, 'remote', 'get-url', 'origin') != url:
        raise ValueError('Checkout belongs to a different repository; use a new session folder')
    clean(repo)
    git(repo, 'fetch', 'origin')
    if exists(repo, f'refs/heads/{BRANCH}'):
        git(repo, 'switch', BRANCH)
    elif exists(repo, f'refs/remotes/origin/{BRANCH}'):
        git(repo, 'switch', '--track', '-c', BRANCH, f'origin/{BRANCH}')
    else:
        if not exists(repo, 'refs/remotes/origin/main'):
            raise ValueError('No main branch found. Ask the instructor to configure this repository.')
        git(repo, 'switch', '-c', BRANCH, 'origin/main')
        # Do not accidentally push to main via an inherited upstream.
        git(repo, 'branch', '--unset-upstream')
    sync(repo)
    return repo


def preview(repo, mapping, template, draft):
    on_branch(repo)
    clean(repo)
    if (Path(repo)/'.migration/state.json').exists():
        raise ValueError('Migration already recorded. Resume editing/checking; do not regenerate.')
    report = build(repo, mapping, template, draft, dry_run=True)
    # Generate only after the separate Apply step, not during preview.
    source_files = set(report['source_inventory'])
    outputs = set(report['template_inventory']) | set(json.loads(Path(mapping).read_text()).get('documents', {})) | {'.migration/state.json'}
    for action in report['actions']:
        if action['action'] in {'keep', 'copy'}:
            outputs.add(action['target'])
    return {**report, 'file_preview': {'add': sorted(outputs-source_files), 'review_or_update': sorted(outputs & source_files), 'remove': sorted(source_files-outputs)}}


def apply(repo, mapping, template, draft, approved):
    current = preview(repo, mapping, template, draft)
    if current != approved:
        raise ValueError('Preview changed. Run Preview again before applying.')
    build(repo, mapping, template, draft)
    report = json.loads((Path(draft)/'.migration/state.json').read_text())
    if inventory(repo) != report['source_inventory']:
        raise ValueError('Working files changed after preview; no draft was applied')
    new = inventory(draft)
    # All source files were explicitly classified; only the reviewed deletions are applied.
    for name in sorted(set(report['source_inventory'])-set(new)):
        safe(repo, name).unlink()
    for directory in sorted(Path(repo).rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if directory.is_dir() and '.git' not in directory.relative_to(repo).parts and not any(directory.iterdir()):
            directory.rmdir()
    for name in new:
        target = safe(repo, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(draft, name), target)
    return Path(draft).parent / (Path(draft).name+'-report.json')


def set_identity(repo, name, email):
    if not name.strip() or not re.fullmatch(r'[^\s@]+@[^\s@]+', email):
        raise ValueError('Enter your own commit name and verified or GitHub noreply email')
    git(repo, 'config', '--local', 'user.name', name.strip())
    git(repo, 'config', '--local', 'user.email', email)


def check_remote(repo):
    git(repo, 'fetch', 'origin')
    if exists(repo, f'origin/{BRANCH}'):
        _, behind = map(int, git(repo, 'rev-list', '--left-right', '--count', f'HEAD...origin/{BRANCH}').split())
        if behind:
            raise ValueError('GitHub has newer work. Preserve local edits and reconcile with your instructor before saving.')


def save(repo, message):
    on_branch(repo)
    check_remote(repo)
    if not message.strip():
        raise ValueError('Write a short commit message')
    if not git(repo, 'config', 'user.name') or not git(repo, 'config', 'user.email'):
        raise ValueError('Set your own commit identity first')
    findings = validate(repo)
    errors = [f for f in findings if f['level'] == 'error']
    if errors:
        raise ValueError('Fix structural errors before saving: '+json.dumps(errors))
    candidates = git(repo, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
    for name in filter(None, candidates):
        p = safe(repo, name)
        if p.name == '.env' or p.name.startswith('.env.') or p.suffix in {'.pem', '.key'}:
            raise ValueError(f'Potential credential file requires manual review: {name}')
        if p.exists() and p.stat().st_size > LIMIT:
            raise ValueError(f'Too large to commit: {name}')
    git(repo, 'add', '-A')
    if git(repo, 'diff', '--cached', '--name-only'):
        git(repo, 'commit', '-m', message.strip())
    git(repo, 'push', '--set-upstream', 'origin', f'HEAD:refs/heads/{BRANCH}')
    return git(repo, 'rev-parse', 'HEAD')


def import_artifacts(repo, folder):
    """Import only figures/processed outputs from a shared Drive transfer folder."""
    on_branch(repo)
    folder = Path(folder).resolve()
    items = inventory(folder)
    for name in items:
        if not name.startswith(('docs/', 'data/processed/')) or name.endswith(('.ipynb', '.py', '.md')):
            raise ValueError(f'Transfer only figures/data under docs/ or data/processed/: {name}')
        if safe(folder, name).stat().st_size > LIMIT:
            raise ValueError(f'Keep oversized artifact external and document its location: {name}')
        safe(repo, name)
    for name in items:
        target = safe(repo, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(folder, name), target)
    return list(items)

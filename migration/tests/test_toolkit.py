import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'migration'))
import nbformat
from common import LIMIT, MANUAL, digest, inventory, safe, sha, write_json
from migrate import build
from validate import validate
import workflow as w

FIXTURES = ROOT/'migration/tests/fixtures'


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.src = self.base/'source'
        shutil.copytree(FIXTURES/'source', self.src)
        self.mapping = self.base/'mapping.json'
        shutil.copyfile(FIXTURES/'synthetic.mapping.json', self.mapping)
        self.out = self.base/'draft'

    def alter(self, fn):
        m=json.loads(self.mapping.read_text());fn(m);write_json(self.mapping,m)

    def build(self, **kwargs):
        return build(self.src,self.mapping,ROOT/'template',self.out,**kwargs)

    def test_template_schema_and_headers(self):
        self.assertEqual(validate(ROOT/'template', artifact='template'), [])
        for p in (ROOT/'template/notebooks').glob('*.ipynb'):
            nbformat.validate(json.loads(p.read_text()))

    def test_dry_run_no_writes(self):
        before=inventory(self.base)
        report=self.build(dry_run=True)
        self.assertEqual(inventory(self.base),before)
        self.assertEqual(report['cell_accounting']['analysis.ipynb']['accounted'],[0,1,2])

    def test_migration_preserves_source_and_data(self):
        before=inventory(self.src)
        self.build()
        self.assertEqual(inventory(self.src),before)
        self.assertEqual(sha(self.src/'measurements.csv'),sha(self.out/'data/raw/measurements.csv'))
        cells=json.loads((self.out/'notebooks/01_eda.ipynb').read_text())['cells']
        self.assertTrue(any('values = [1, 2, 3]' in c['source'] for c in cells))
        self.assertTrue(all(c.get('execution_count') is None and not c.get('outputs') for c in cells))
        self.assertFalse(any(f['level']=='error' for f in validate(self.out)))
        self.assertTrue(any(f['level']=='error' for f in validate(self.out,'readiness')))
        self.assertTrue((self.base/'draft-report.json').exists())

    def test_no_overwrite(self):
        self.build()
        (self.out/'README.md').write_text('Student edits')
        with self.assertRaisesRegex(ValueError,'already exists'):self.build()
        self.assertEqual((self.out/'README.md').read_text(),'Student edits')

    def test_stale_mapping(self):
        (self.src/'README.md').write_text('new content')
        with self.assertRaisesRegex(ValueError,'Stale'):self.build()
        self.assertFalse(self.out.exists())

    def test_unknown_file(self):
        (self.src/'other.txt').write_text('keep me')
        with self.assertRaisesRegex(ValueError,'Unclassified'):self.build()

    def test_duplicate_and_missing_cells(self):
        self.alter(lambda m:m['files'][0]['blocks'][0]['cells'].append({'index':1}))
        with self.assertRaisesRegex(ValueError,'exactly once'):self.build()

    def test_path_traversal(self):
        self.alter(lambda m:m['files'][1].update(target='../escape.csv'))
        with self.assertRaisesRegex(ValueError,'Unsafe|Invalid mapping'):self.build()
        self.assertFalse((self.base/'escape.csv').exists())

    def test_symlink_refused(self):
        (self.src/'link').symlink_to(self.src/'README.md')
        with self.assertRaisesRegex(ValueError,'Symlink'):self.build()

    def test_template_overwrite_requires_explicit_flag(self):
        self.alter(lambda m:m['files'][1].update(target='README.md'))
        with self.assertRaisesRegex(ValueError,'replace_template'):self.build()

    def test_large_file_refused(self):
        with (self.src/'measurements.csv').open('wb') as f:f.truncate(LIMIT+1)
        self.alter(lambda m:m['files'][1].update(sha256=sha(self.src/'measurements.csv')))
        with self.assertRaisesRegex(ValueError,'25 MB'):self.build()

    def test_unknown_mapping_keys_refused(self):
        self.alter(lambda m:m.update(misspelled_option=True))
        with self.assertRaisesRegex(ValueError,'Invalid mapping'):self.build()

    def test_insert_and_adapt_with_provenance(self):
        def edit(m):
            m['files'][0]['blocks'][0]['cells'][1]['replace']=[{'old':'values =','new':'measurements =','reason':'Deliberate synthetic adaptation'}]
            m['files'][0]['blocks'][0]['cells'].append({'type':'markdown','text':'Inserted explanation.','reason':'Document adaptation'})
        self.alter(edit)
        self.build()
        text=(self.out/'notebooks/01_eda.ipynb').read_text()
        self.assertIn('measurements =',text)
        self.assertIn('Inserted explanation.',text)

    def test_bad_replacement_does_not_publish_output(self):
        self.alter(lambda m:m['files'][0]['blocks'][0]['cells'][1].update(replace=[{'old':'NOT PRESENT','new':'x','reason':'test'}]))
        with self.assertRaisesRegex(ValueError,'exactly once'):self.build()
        self.assertFalse(self.out.exists())

    def test_readiness_manual_review_stale(self):
        self.build()
        review={'content_sha256':digest(self.out),'checks':{k:{'passed':True,'evidence':'Synthetic test evidence'} for k in MANUAL}}
        write_json(self.out/'.migration/review.json',review)
        findings=validate(self.out,'readiness')
        self.assertFalse(any('Manual review missing or stale' in f['message'] for f in findings))
        (self.out/'docs/figure.txt').write_text('changed')
        self.assertTrue(any('stale' in f['message'] for f in validate(self.out,'readiness')))

    def test_launcher_schema_and_python(self):
        n=json.loads((ROOT/'launcher/student_migration.ipynb').read_text())
        nbformat.validate(n)
        for i,c in enumerate(n['cells']):
            if c['cell_type']=='code':compile(c['source'],f'launcher-cell-{i}','exec')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict('os.environ', {'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'})
        env.start(); self.addCleanup(env.stop)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.seed=self.base/'seed';shutil.copytree(FIXTURES/'source',self.seed)
        w.run(['git','init','-b','main',str(self.seed)])
        w.set_identity(self.seed,'Synthetic Student','student@example.test')
        w.git(self.seed,'add','.')
        w.git(self.seed,'commit','-m','Original student work')
        self.remote=self.base/'remote.git'
        w.run(['git','clone','--bare',str(self.seed),str(self.remote)])
        self.main=w.git(self.seed,'rev-parse','HEAD')
        self.repo=w.prepare(str(self.remote),self.base/'checkout')
        w.set_identity(self.repo,'Synthetic Student','student@example.test')
        self.mapping=FIXTURES/'synthetic.mapping.json'
        self.draft=self.base/'draft'

    def migrate(self):
        preview=w.preview(self.repo,self.mapping,ROOT/'template',self.draft)
        self.assertIn('analysis.ipynb',preview['file_preview']['remove'])
        w.apply(self.repo,self.mapping,ROOT/'template',self.draft,preview)

    def test_branch_apply_save_and_resume(self):
        self.assertEqual(w.git(self.repo,'branch','--show-current'),'tidy_work')
        self.migrate()
        w.save(self.repo,'Reorganize project')
        self.assertEqual(w.git(self.remote,'rev-parse','main'),self.main)
        self.assertEqual(w.git(self.remote,'log','-1','--format=%an','tidy_work'),'Synthetic Student')
        new=w.prepare(str(self.remote),self.base/'resumed')
        self.assertTrue((new/'.migration/state.json').exists())
        with self.assertRaisesRegex(ValueError,'already recorded'):
            w.preview(new,self.mapping,ROOT/'template',self.base/'new-draft')

    def test_resume_preserves_student_edits(self):
        self.migrate();w.save(self.repo,'Migrate')
        (self.repo/'docs/student.txt').write_text('student work')
        with self.assertRaisesRegex(ValueError,'Unsaved'):w.prepare(str(self.remote),self.repo)
        self.assertEqual((self.repo/'docs/student.txt').read_text(),'student work')

    def test_apply_rejects_changed_preview(self):
        preview=w.preview(self.repo,self.mapping,ROOT/'template',self.draft)
        preview['notes'].append('tampered')
        with self.assertRaisesRegex(ValueError,'Preview changed'):
            w.apply(self.repo,self.mapping,ROOT/'template',self.draft,preview)
        self.assertTrue((self.repo/'analysis.ipynb').exists())

    def test_main_guard(self):
        w.git(self.repo,'switch','main')
        with self.assertRaisesRegex(ValueError,'only on tidy_work'):w.save(self.repo,'No')

    def test_remote_update_blocks_save(self):
        self.migrate();w.save(self.repo,'Migrate')
        other=w.prepare(str(self.remote),self.base/'other')
        w.set_identity(other,'Synthetic Student','student@example.test')
        (other/'docs/new.txt').write_text('remote edit')
        w.save(other,'Remote edit')
        (self.repo/'docs/local.txt').write_text('local edit')
        with self.assertRaisesRegex(ValueError,'newer work'):w.save(self.repo,'Local edit')
        self.assertEqual((self.repo/'docs/local.txt').read_text(),'local edit')

    def test_clean_remote_fast_forward(self):
        self.migrate();w.save(self.repo,'Migrate')
        other=w.prepare(str(self.remote),self.base/'other')
        w.set_identity(other,'Synthetic Student','student@example.test')
        (other/'docs/new.txt').write_text('remote edit');w.save(other,'Remote edit')
        w.sync(self.repo)
        self.assertEqual((self.repo/'docs/new.txt').read_text(),'remote edit')

    def test_diverged_branches_stop(self):
        self.migrate();w.save(self.repo,'Migrate')
        other=w.prepare(str(self.remote),self.base/'other')
        w.set_identity(other,'Synthetic Student','student@example.test')
        (other/'docs/remote.txt').write_text('remote');w.save(other,'Remote')
        (self.repo/'docs/local.txt').write_text('local')
        w.git(self.repo,'add','.');w.git(self.repo,'commit','-m','Local')
        with self.assertRaisesRegex(ValueError,'diverged'):w.sync(self.repo)

    def test_artifact_import_preflight(self):
        self.migrate();w.save(self.repo,'Migrate')
        folder=self.base/'transfer';(folder/'docs').mkdir(parents=True)
        (folder/'docs/chart.svg').write_text('<svg/>')
        (folder/'bad.py').write_text('print(1)')
        with self.assertRaisesRegex(ValueError,'Transfer only'):w.import_artifacts(self.repo,folder)
        self.assertFalse((self.repo/'docs/chart.svg').exists())
        (folder/'bad.py').unlink()
        self.assertEqual(w.import_artifacts(self.repo,folder),['docs/chart.svg'])

    def test_credential_files_block_save(self):
        self.migrate();w.save(self.repo,'Migrate')
        (self.repo/'secret.key').write_text('synthetic secret')
        with self.assertRaisesRegex(ValueError,'credential'):w.save(self.repo,'Should fail')

    def test_ignored_external_data_does_not_block_save(self):
        self.migrate();w.save(self.repo,'Migrate')
        with (self.repo/'.gitignore').open('a') as f:f.write('\ndata/raw/external.bin\n')
        with (self.repo/'data/raw/external.bin').open('wb') as f:f.truncate(LIMIT+1)
        w.save(self.repo,'Document external data exclusion')
        self.assertNotIn('external.bin',w.git(self.repo,'ls-files'))

    def test_wrong_remote_refused(self):
        with self.assertRaisesRegex(ValueError,'different repository'):
            w.prepare(str(self.seed),self.repo)

    def test_url_validation(self):
        self.assertEqual(w.github_url('https://github.com/student/project'),'https://github.com/student/project.git')
        self.assertEqual(w.github_url('https://github.com/student/project.git'),'https://github.com/student/project.git')
        for bad in ['https://token@github.com/student/repo','https://evil.test/repo','https://github.com/student/repo/tree/main']:
            with self.assertRaises(ValueError):w.github_url(bad)


if __name__=='__main__':unittest.main()

# Capstone repository migration toolkit

Reorganize an existing student repository into a public-facing data science project on **`tidy_work`**, preserving its history and leaving `main` unchanged until instructor review. Students do not create a new repository or fork.

Start with the [instructor guide](migration/README.md). The [student Colab launcher](launcher/student_migration.ipynb) guides sign-in, branch preparation, preview, migration, saving, editing, and readiness checks. The [template](template/README.md) provides structure, not analysis.

## What is included

```text
template/                     Generic project scaffolding
launcher/student_migration.ipynb
migration/
  README.md                   Instructor setup and mapping reference
  migrate.py                  Build a new draft without changing the source
  validate.py                 Structure and readiness checks
  workflow.py                 Branch, save, resume and artifact helpers
  inspect_source.py           File fingerprints and indexed cell summaries
  mapping.schema.json         Machine-validated mapping format
  common.py                   Shared notebook and path helpers
  requirements-dev.txt        Tool dependency
  tests/                      Synthetic migration and local Git tests
```

No student-specific mappings, drafts, presets, or migrations are included. Create and test mappings yourself before sharing the launcher. Any original examples in the local workspace remain unchanged and are excluded from Git.

## Try a synthetic migration locally

Requires Python 3.10+ and Git. These commands write only to `generated/`; the fixture stays unchanged.

```bash
python -m pip install -r migration/requirements-dev.txt
python migration/migrate.py --source migration/tests/fixtures/source --mapping migration/tests/fixtures/synthetic.mapping.json --template template --output generated/synthetic --dry-run
python migration/migrate.py --source migration/tests/fixtures/source --mapping migration/tests/fixtures/synthetic.mapping.json --template template --output generated/synthetic
python migration/validate.py --repo generated/synthetic --mode structure
python migration/validate.py --repo generated/synthetic --mode readiness
```

Readiness is expected to fail for this unfinished synthetic draft. Choose a fresh output path for each migration; existing destinations are never overwritten.

## Tests

```bash
python -m unittest discover -s migration/tests -v
python migration/validate.py --repo template --artifact template
```

Tests use temporary local repositories and synthetic data, not student repositories or GitHub accounts. Live Colab authentication, notebook saving through its UI, Drive transfer, and actual GitHub pushes require the instructor's end-to-end pilot before distribution.

## Publish for your pilot

Publish this toolkit repository yourself, then open `launcher/student_migration.ipynb` in Colab using:

```text
https://colab.research.google.com/github/juanatga/dsb_cap_template/blob/main/launcher/student_migration.ipynb
```

Set the toolkit URL in the launcher (or tell testers to fill it in). Supply a reviewed mapping via a public raw GitHub URL. Students enter their **existing project** URL separately. Pin `TOOLKIT_REF` to a tested release tag for distribution. Do not commit authenticated launcher outputs or credentials.

Before publishing, explicitly decide whether to include the supplied `examples/`; the implementation does not need them. Do not accidentally publish student data as toolkit content. The student-facing launcher uses only the chosen mapping and repository.

## Specification clarifications

The later branch-based requirements supersede the original spec's new-repository/setup instructions: `tidy_work` starts from the student's existing `main`; no `git init` or new student repo is needed. The template includes `data/README.md`, referenced in the spec but absent from its initial tree. Paths use a documented repository root, with `PROCESSED` equivalent to `../data/processed` when starting in `notebooks/`. All twelve modelling sections remain, with guidance for pretrained models and detection methods.

Official references: [GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login), [Git credential setup](https://cli.github.com/manual/gh_auth_setup-git), and [Colab FAQ](https://research.google.com/colaboratory/faq.html).

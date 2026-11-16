# Instructor guide

The tools mechanically reorganize work according to **your reviewed mapping**. They do not infer scientific decisions, synthesize results, automatically split arbitrary notebooks, run student code, or claim a project is complete.

Students work in their existing repo on `tidy_work`. This toolkit does not open PRs: after student validation, you open the PR into `main`.

## 1. Prepare the source and mapping

Use a fresh clone of the student's existing `main`, outside this toolkit. Keep your mapping outside that clone. Every actual file, including dotfiles but excluding `.git`, must be classified. Caches, downloaded datasets and untracked files in a working copy count too; prefer a clean clone.

```bash
python -m pip install -r migration/requirements-dev.txt
git clone --branch main https://github.com/OWNER/EXISTING_PROJECT.git ../student-source
python migration/inspect_source.py --source ../student-source
```

The inspection command prints SHA-256 fingerprints and zero-based notebook cell summaries. Review the full code before assigning cells; summaries are not dependency analysis. Use `tests/fixtures/synthetic.mapping.json` as a small example. No mappings for real students ship with this toolkit.

Write a JSON mapping following `mapping.schema.json`:

```json
{
  "version": 1,
  "files": [
    {
      "source": "old_analysis.ipynb",
      "sha256": "REPLACE_WITH_64_CHARACTER_SHA256",
      "action": "notebook",
      "reason": "Separate exploration from modelling while preserving dependencies.",
      "blocks": [
        {
          "target": "notebooks/01_eda.ipynb",
          "section": 6,
          "cells": [{"index": 0}, {"index": 1}]
        }
      ],
      "omit": [{"index": 2, "reason": "Retired scratch cell; retained in source history."}]
    },
    {
      "source": "measurements.csv",
      "sha256": "REPLACE_WITH_64_CHARACTER_SHA256",
      "action": "copy",
      "target": "data/raw/measurements.csv",
      "reason": "Preserve untouched original input."
    }
  ],
  "documents": {},
  "dependencies": [],
  "notes": ["List missing inputs, unfinished work, and decisions requiring student review."]
}
```

This illustrative mapping is not runnable until you supply real hashes and account for **all files and all cells**. The synthetic fixture is runnable as supplied.

### File actions

| Action | Meaning |
|---|---|
| `keep` | Copy this file unchanged at its existing path. |
| `copy` | Copy unchanged to `target`; the original path disappears unless another declared output uses it. |
| `remove` | Leave the file out of the migrated layout, with a mandatory reason. Earlier Git commits preserve it. |
| `notebook` | Route individual cells into the two template notebooks; every index must be used once or explicitly omitted. |

Every entry requires `source`, `sha256`, `action`, and `reason`. A copy/keep that overwrites a template file also requires `replace_template: true`. No wildcards, implicit deletions, symlinks, or paths outside the root are supported. All source notebooks use `notebook`, even when all their cells are deliberately omitted.

Files over 25,000,000 bytes cannot be copied into the draft. Map them as `remove` and put acquisition instructions and their exact ignore paths into `documents`. Moving or deleting a large file does not purge earlier Git history; history cleanup is outside this toolkit.

An unrelated project must be classified explicitly. Do not silently discard it to make the checklist pass. Keeping a notebook outside `notebooks/` fails structure checks; discuss archival or a separate project with its owner when needed.

### Notebook blocks and adaptations

`target` is one of the two standard notebook paths; `section` is its one-based specification number. Blocks are concatenated in mapping order within each destination section. Used sections replace the template's instruction/code stubs; unused sections retain scaffolding. The opening writing guidance remains for students to remove. Markdown and code are preserved, saved outputs and execution counts are cleared, and missing pre-code explanations become tagged writing prompts.

Source-cell references can contain precise text replacements:

```json
{
  "index": 7,
  "replace": [{
    "old": "pd.read_csv('old.csv')",
    "new": "pd.read_csv(RAW / 'old.csv')",
    "reason": "Read the migrated local raw file."
  }]
}
```

Each `old` string must match exactly once at that point. Replacements occur in listed order. Arbitrary search/replace across the repo is deliberately unsupported.

Insert a new explanation, setup, export, or loading cell explicitly:

```json
{
  "type": "code",
  "text": "PROCESSED.mkdir(parents=True, exist_ok=True)\ncleaned.to_csv(PROCESSED / 'cleaned.csv', index=False)",
  "reason": "Create the explicit data handoff to modelling."
}
```

Provide a Markdown explanation before inserted code. Mark unfinished inserted guidance with `"instruction": true`. Preserve index identifiers, timestamp timezone, and other cross-notebook requirements in the export/load pair. Fit learned transformations only on training data. For waveform/model pipelines, do not accidentally export visualization-only filtering as model preprocessing.

Raw notebook cells must be explicitly omitted or converted manually before fingerprinting. Markdown attachments are preserved. Widget state and runtime-specific metadata are not transferred.

### Documentation and packages

`documents` maps relative filenames to their **complete replacement text**. Use it to reorganize an existing README, document data acquisition, fill credits, or extend `.gitignore`; read the template first and keep its required sections. It cannot overwrite `.migration/` or notebook files, or duplicate copy targets. Narrative prose is supplied by you/student, never synthesized by the script.

`dependencies` adds package names (optionally exact versions) to the starter requirements. Existing package names are not duplicated or automatically upgraded. Confirm imports against distribution names yourself and pin the actual working environment before submission. List missing external model weights, network requirements, and non-Python dependencies in notes/documentation.

## 2. Dry-run and inspect a draft locally

```bash
python migration/migrate.py --source ../student-source --mapping ../mapping.json --template template --output generated/pilot --dry-run
python migration/migrate.py --source ../student-source --mapping ../mapping.json --template template --output generated/pilot
python migration/validate.py --repo generated/pilot --mode structure
```

The source is never changed. JSON schema, hashes, full file classification and cell coverage are checked before generation. The mapping does not follow later student edits automatically: update it intentionally if a fingerprint changes.

The tool writes the report beside the output, e.g. `generated/pilot-report.json`, and keeps a durable provenance record in `.migration/state.json` inside the draft. The record includes exact declared adaptations, omitted cells and reasons. It has no credentials. Review it for private material before publishing. Reports include structural findings, but no claim of notebook execution.

Existing output directories are refused. Use a fresh path for another trial. Do not delete a draft containing student edits merely to rerun migration.

## 3. Pilot the Colab launcher

Publish the toolkit when ready, preferably under a tested tag. In `launcher/student_migration.ipynb`, set or supply `TOOLKIT_URL` and `TOOLKIT_REF`. Host each reviewed mapping at a public raw GitHub URL; do not put confidential source snippets in a public mapping. The current launcher supports public mapping URLs and GitHub.com HTTPS project URLs. Private mapping hosting and non-GitHub hosts are outside v1.

Test the launcher on a disposable pilot repository first, then with a student-authorized repository. Each launch uses one project. The launcher supports all students by accepting their mapping URL, not by guessing a mapping from their name.

Authentication uses `gh auth login --web --git-protocol https` and `gh auth setup-git`. The student signs in, confirms their own commit name/email, and needs push permission. The browser device code is displayed; tokens are never placed in cells. GitHub organization policies may require additional authorization. The toolkit is cloned publicly before authentication; publish the toolkit publicly for this workflow.

The launcher clones the student's existing repo into Colab, creates `tidy_work` from remote `main`, or resumes a remote/local `tidy_work`. It stops for dirty files and divergence; clean behind-only branches fast-forward. No resets, force pushes, or automatic PRs occur. Repeated Apply steps stop after the migration marker exists. If a save push is rejected after a concurrent remote change, the local commit remains available for reconciliation.

The initial preview lists the mapping and file changes. Apply rechecks the preview, builds in a separate folder, validates, and applies only declared changes. Subsequent saves require structural validity but allow unfinished writing. GitHub is the persistent store: Colab is temporary.

Use the launcher's Drive transfer instructions for small figures and processed data from separate analysis runtimes. Imports are limited to `docs/` and `data/processed/`, reject notebooks/code/Markdown, and require a later explicit save. They never import an entire arbitrary folder into the repository. Each notebook session still needs the explicit environment and data setup in SETUP.md.

### Required live pilot checks

- Sign in through the browser device flow and confirm the correct GitHub identity.
- Create `tidy_work`, preview/apply, push, and verify `main` is unchanged.
- Save a notebook from Colab to the same branch and exact notebook path; resume and fetch it.
- Transfer a figure and processed dataset from another runtime, save, and load them in notebook 02.
- Resume without regenerating; test a remote edit and verify it cannot be overwritten.
- Confirm sign-out and runtime deletion after work is saved.

Local automated tests cover helper behavior, not GitHub's permissions, Colab's UI, Drive access, or model execution.

## 4. Validate and review

```bash
python migration/validate.py --repo PATH --mode structure
python migration/validate.py --repo PATH --mode readiness --json
python migration/validate.py --repo template --artifact template
```

Both modes return exit code 1 for errors, 0 otherwise. Structure checks layout and notebook schemas; unfinished content is reported as warnings. Readiness treats unfinished content, unpinned requirements and unverified manual checks as errors. Template mode expects comment-only TODO cells and empty outputs. In a Git checkout, validation and review fingerprints cover tracked files plus nonignored untracked files, so explicitly ignored external datasets can remain on disk. A previously tracked file is still checked even if later added to .gitignore. In a plain draft folder, all files are checked.

Path checks are heuristic: they flag common machine-specific paths and raw-data reads but cannot prove arbitrary code reads only processed inputs. All notebooks must execute independently in the prescribed order with acquired data; a static pass is not proof.

After actual manual review, record evidence in `.migration/review.json`:

```json
{
  "content_sha256": "CURRENT_FINGERPRINT_PRINTED_BY_READINESS",
  "checks": {
    "fresh_local_run": {"passed": true, "evidence": "Reviewer/date, environment and run results"},
    "fresh_colab_run": {"passed": true, "evidence": "Reviewer/date and fresh-runtime results"},
    "data_provenance_and_permissions": {"passed": true, "evidence": "Sources and access terms checked"},
    "baseline_and_evaluation": {"passed": true, "evidence": "Baseline, metric and independent evaluation reviewed"},
    "chart_labels_and_captions": {"passed": true, "evidence": "Figures inspected"},
    "plain_language_and_decisions": {"passed": true, "evidence": "Narrative, dictionary, quality decisions and processed loading reviewed"},
    "limitations_and_ethics": {"passed": true, "evidence": "Substantive caveats reviewed"},
    "public_reader_test": {"passed": true, "evidence": "Non-expert reader and feedback"}
  }
}
```

Do not mark blocked checks as passed. This file records human assertions; the tool does not authenticate them. The content fingerprint excludes only this review file and Git metadata. Any other file change invalidates the review, including changing README links from `tidy_work` to `main`. Finalize files before recording evidence. Ask the student to commit review evidence so their branch remains student-authored; your PR review is the instructor record.

Before merging, review the student checklist and PR diff. After merging, verify `main` runs. No automatic CI or scientific acceptance is implied.

## Recovery

- **Stale mapping:** preserve the source, inspect its new fingerprint and cells, and update/review the mapping.
- **Unclassified file:** explicitly keep, copy, remove, or map it; do not delete it blindly.
- **Already migrated:** continue editing; do not rerun initial migration.
- **Unsaved local files:** save or preserve them before syncing. Do not reset the branch.
- **Remote divergence:** preserve local commits/files and reconcile through normal Git review with the instructor.
- **Generation error:** source and branch remain untouched until a valid draft is ready. Inspect the error and use a fresh output path.
- **Interrupted application:** source history and the temporary generated draft remain available; inspect `git diff` before retrying. Do not blindly rerun over edits.
- **Missing dataset/model weights:** document access and mark execution blocked; migration does not fabricate them.

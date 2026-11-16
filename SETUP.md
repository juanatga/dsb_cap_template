# Run and save your project

## Your repository and branch

Keep your existing GitHub repository. Work on `tidy_project`, created from your existing `main`, with the instructor's template files added. Follow the instructor repository's README for the one-time setup commands. Manually copy your existing analysis into the template sections.

Your instructor reviews and merges the branch when the project is ready.

## Prepare a fresh Colab session

Open your notebook from your own repository's `tidy_project` branch. Opening the notebook does not copy the other project files into Colab.

In a temporary setup cell, run the following after replacing the owner and repository name. This copies the project into **Colab's temporary computer**, not your laptop:

```python
!git clone --branch tidy_project https://github.com/{OWNER}/{REPO}.git project
%cd project
%pip install -r requirements.txt
```

Run this once per fresh runtime. If `project` already exists, use that checkout rather than cloning over it. Obtain datasets as documented in `data/README.md`. Change the branch to `main` when reproducing the reviewed final project.

Run `01_eda.ipynb` before `02_modelling.ipynb`. A separate runtime for notebook 02 must obtain the processed outputs through the documented acquisition steps; it does not share files or variables with notebook 01.

## One path convention

Document this pattern in each notebook's Setup section. It supports a kernel started at the repository root or inside `notebooks/`. In Colab, first enter the clone as shown above.

```python
from pathlib import Path
ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
if not (ROOT / "data").is_dir() or not (ROOT / "notebooks").is_dir():
    raise RuntimeError("Start in the repository root or its notebooks folder.")
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
```

Use `RAW` for untouched inputs and `PROCESSED` for EDA exports and model loading. From `notebooks/`, the latter corresponds to `../data/processed/`. Notebook 02 must explain "run 01_eda.ipynb first" if outputs are missing. Keep machine-specific paths and Drive mounts out of the analysis code.

Fit learned transformations on training data only; apply them to held-out data without refitting.

## Save notebooks and outputs

In Colab, use **File → Save a copy in GitHub**. Select your own repository, `tidy_project`, and the exact `notebooks/` filename. Verify the saved notebook on GitHub.

Notebook saves do not include figures or datasets. For small outputs, download the files from Colab's Files panel to your computer, then upload them through GitHub into `docs/` or `data/processed/` on `tidy_project`. Files larger than 25 MB stay in documented external storage and must be ignored by Git.

Save and verify your work before ending a Colab runtime; its local files are temporary.

## Local alternative

Clone the same branch onto your computer, install requirements, and start Jupyter from the repository root. VS Code can open the checkout directly.

```bash
git clone --branch tidy_project https://github.com/{OWNER}/{REPO}.git
cd {REPO}
python -m pip install -r requirements.txt
jupyter notebook
```

If you already have a local checkout, save any local edits and pull the latest branch before starting; do not clone over an existing folder.

## Record the environment

After a successful run, inspect installed versions with `pip freeze` and pin the packages your project actually uses in `requirements.txt`, including when working in Colab. Do not blindly copy unrelated Colab packages. Reinstall those requirements and verify a fresh run before submission.

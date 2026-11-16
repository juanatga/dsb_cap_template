# Run and save your existing project

## Where you work

Keep your existing GitHub repository. Do not create a new repo or fork. Your instructor supplies a Colab migration launcher and mapping. Migration copies files into Colab's temporary computer, not your laptop. Work on tidy_work; main changes only after instructor review and merge.

## Migration in Colab

1. Open the instructor's launcher and enter your existing repository URL and mapping.
2. Sign in to GitHub when prompted. Prepare tidy_work from main, or resume it.
3. Preview the explicit moves, changes, and removals. Ask the instructor to update a stale mapping.
4. Generate the draft and inspect the report. Files are still only in Colab.
5. Save the branch to GitHub and verify the displayed tidy_work link before closing Colab.
6. Open notebook 01, then 02 through the launcher's links. Fill the writing prompts and run from fresh kernels.
7. Save notebook edits with Colab's File > Save a copy in GitHub, selecting your repository, tidy_work, and the exact notebooks/ filename. Check the saved version on GitHub.
8. Generated figures and data are separate files: saving the notebook does not save them. The launcher includes instructions for transferring these from the analysis runtime through a temporary Drive folder, then reviewing and committing them. Keep oversized data outside Git.
9. Reload the latest branch in the launcher and run readiness checks. Send your existing repository and tidy_work link to your instructor, who opens the pull request. Do not merge yourself.

## Notebook environment: Colab

Opening a notebook from GitHub opens that notebook, not the entire repository. In a temporary setup cell before running the analysis, clone your existing repository into the runtime, select tidy_work, enter the clone, and install packages. Replace the values below. These setup commands copy into Colab, not your computer.

```python
!git clone --branch tidy_work https://github.com/{OWNER}/{REPO}.git project
%cd project
%pip install -r requirements.txt
```

Run this once per fresh runtime. If project already exists, use the existing checkout rather than cloning over it. Obtain data as documented in data/README.md. Do not bake Drive mounts or absolute paths into analysis cells. Change tidy_work to main when reproducing the reviewed final project.

## Local alternative

Clone the same branch, install requirements, and start Jupyter from the repository root. VS Code can open the checkout directly. No new Git repository is needed.

```bash
git clone --branch tidy_work https://github.com/{OWNER}/{REPO}.git
cd {REPO}
python -m pip install -r requirements.txt
jupyter notebook
```

## One path convention

Document this pattern in each notebook's Setup section. It supports a kernel started at the root or in notebooks/; a Colab runtime must first enter the clone as above.

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

Use PROCESSED for both export and model loading (equivalent to ../data/processed from notebooks/). Notebook 02 must explain "run 01_eda.ipynb first" when outputs are missing. Fit learned transformations on training data only; apply them to held-out data without refitting.

## Record the environment

After a successful run, use pip freeze to inspect installed versions and pin the packages your project actually uses in requirements.txt, including in Colab. Do not blindly copy unrelated Colab packages. Reinstall those requirements and verify a fresh run.

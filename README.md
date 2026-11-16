# Organize your capstone project

Use this template to organize your existing work into two notebooks: **exploration** and **modelling**. You will copy your analysis into the appropriate sections yourself.

**Keep your existing GitHub repository. Work on a branch named `tidy_project`.** Your `main` branch keeps the original project until your instructor reviews and merges your changes. You do not need a fork or a new repository.

## 1. [optional] Create your branch and add the template

Do this setup once in **Terminal on your computer** (on Windows, use **Git Bash**), not in a Colab code cell. You need Git installed and permission to push to your existing GitHub repository. After setup, you can edit the notebooks in Colab.

First save your latest work to your repository's `main` branch. Open Terminal in a folder where you keep projects. 

## 2. Understand the layout

Your completed project should have this structure:

```text
README.md                    Your project's story and main result
LICENSE                      Code license and completed attribution
requirements.txt             Packages and tested versions
.gitignore                   Files to keep out of Git
data/
  README.md                  How to obtain the datasets
  raw/README.md              Sources and untouched original data
  processed/README.md        Cleaned outputs produced by EDA
notebooks/
  01_eda.ipynb               Exploration, cleaning, and findings
  02_modelling.ipynb         Models, evaluation, and conclusions
docs/README.md               Figures, slides, and supporting material
```

The setup commands create these folders. If you need to add a missing folder on the **GitHub website**, select `tidy_project`, choose **Add file → Create new file**, and enter a path such as `data/raw/README.md`. GitHub creates the folders when you commit the file.

## 3. Move your notebook content manually

Keep your original notebooks until the new versions run correctly. Open the original and the destination notebook side by side in Colab.

1. Copy exploration, data checks, cleaning, and related explanations into `notebooks/01_eda.ipynb`.
2. Copy feature preparation, models, evaluation, and conclusions into `notebooks/02_modelling.ipynb`.
3. Place each block under the appropriate numbered section. Preserve the order needed for the code to run.
4. Add a plain-language Markdown explanation before each code cell. Explain what the code does and why.
5. Replace the template prompts with your own writing. Keep section headings and your explanations; remove unused instruction cells and TODO comments.

Use the [EDA template](notebooks/01_eda.ipynb) and [modelling template](notebooks/02_modelling.ipynb) as references. If you already had notebooks at those exact paths, the setup kept them unchanged: add the template's section headings to them and reorganize their content manually.

### Open and save your own notebooks in Colab

In Colab, choose **File → Open notebook → GitHub**, then paste the GitHub URL of the notebook on your **`tidy_project`** branch. You can copy that URL after opening the notebook on GitHub.

After editing, choose **File → Save a copy in GitHub** and select:

- **Repository:** your existing project repository.
- **Branch:** `tidy_project`.
- **File path:** `notebooks/01_eda.ipynb` or `notebooks/02_modelling.ipynb`.

Open the saved file on GitHub to verify it. Saving an ordinary Drive copy is not the same as saving to your repository.

## 4. Organize your data and fix paths

- Put untouched original files in `data/raw/` and document their sources and terms.
- Have `01_eda.ipynb` write cleaned data to `data/processed/`.
- Have `02_modelling.ipynb` load those processed files, rather than depending on variables left in the EDA notebook's memory.
- Store figures and slides in `docs/`.

Use **Add file → Upload files** inside the appropriate folder on GitHub, with `tidy_project` selected, to add small local files. Verify the uploaded file before removing an old copy.

Files larger than **25 MB** belong in external storage. Document their location and exact acquisition steps in `data/README.md`, and add their local paths to `.gitignore`.

Opening a notebook in Colab does not copy its data or the rest of the repository. In a fresh Colab session, replace the account and repository names below and run this setup cell once:

```python
!git clone --branch tidy_project https://github.com/YOUR_USERNAME/YOUR_EXISTING_REPO.git project
%cd project
%pip install -r requirements.txt
```

Run your analysis from this project folder, using paths such as `data/raw/your_file.csv`. Follow `data/README.md` to obtain any missing files. If `project` already exists, use that checkout rather than cloning again.

 Saving a notebook does not save generated files: download small figures or datasets from Colab's Files panel to your computer, then upload them to the correct folder on GitHub. Here, **download means to your computer**.

## 5. Complete the project README and supporting files

Use the [project README skeleton below](#project-readme-skeleton) to rewrite the README in **your own repository**. Replace these setup instructions with your project narrative once you have completed the move. Include the problem, one concrete result and figure, data sources, reproduction instructions, and credits. Write for someone without a data science background.

Also complete the data documentation, license attribution, and tested package versions in `requirements.txt`. Replace repository-link placeholders with your own account and repository; use `tidy_project` while working.

## 6. Check and submit

1. Run `01_eda.ipynb` from a fresh session and save its processed outputs.
2. Run `02_modelling.ipynb` from a separate fresh session, acquiring those outputs as documented. Do not rely on the first notebook's in-memory variables.
3. Confirm that the README, figures, and both notebooks are saved on GitHub's (optionally in the `tidy_project` branch).
4. Once the new versions work, remove superseded notebook copies from this branch. Earlier versions remain in Git history and on `main` until the merge.
5. Check that your explanations, data sources, baseline comparison, and limitations are complete. Remove leftover prompts and TODO comments.
6. [optional] Your instructor opens the pull request to review and merge your work into `main`. Before the final merge, update reproduction links to the final branch as directed by your instructor.


## Project README skeleton

Copy the Markdown below into your project README, then replace the prompts and placeholders with your own content. Keep this instructor repository open as your setup reference.

````markdown
# {PROJECT TITLE}

*Replace this with a one-sentence description a non-expert can understand.*

## The problem

*Replace this with 3–5 sentences explaining the problem and why people should care.*

## Key result

*Replace this with one concrete finding or number, what it means, and a supporting figure saved in docs/.*

![{Describe the finding}](docs/{FIGURE_FILENAME})

## The data

*Replace this with the source, size, collection period, license or terms, and one plain-language sentence per dataset. Link to data/README.md for acquisition instructions.*

## How to navigate this repo

*Replace this instruction with a short guide tailored to your project.*
Start here, then read [EDA](notebooks/01_eda.ipynb), followed by [modelling](notebooks/02_modelling.ipynb). Data instructions are in [data/](data/README.md); figures and slides are in [docs/](docs/README.md).

## How to reproduce

*Replace the repository and branch placeholders and explain any data access requirements. [optional] Use tidy_project while editing; update links to main before submission.*

```bash
git clone --branch {BRANCH} https://github.com/{OWNER}/{REPO}.git
cd {REPO}
python -m pip install -r requirements.txt
jupyter notebook
```

Run 01 then 02 from fresh sessions. In Colab, first clone this repository, enter its folder, and install requirements as shown above (use `!git clone`, `%cd`, and `%pip install` in a code cell). Obtain data as explained in [data/README.md](data/README.md). Opening a badge alone does not copy the repository or its data.

[![Open EDA in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{OWNER}/{REPO}/blob/{BRANCH}/notebooks/01_eda.ipynb)
[![Open modelling in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{OWNER}/{REPO}/blob/{BRANCH}/notebooks/02_modelling.ipynb)

## Repository structure

*Replace descriptions if your project needs additional documented files.*

```text
README.md                  Public project story
LICENSE                    Code license; data may have separate terms
requirements.txt           Packages and verified versions
.gitignore                 Files to keep out of Git
data/
  README.md                Acquisition and file-size policy
  raw/                     Untouched originals and provenance
  processed/               Outputs generated by EDA
notebooks/
  01_eda.ipynb              Explore, document decisions, export
  02_modelling.ipynb        Compare methods and explain results
docs/                      Figures, slides, extended explanations
```

## Author & credits

*Replace this with your name, program, acknowledgements, data providers, and any reused code or model credits.*

## License

*Replace this with the completed MIT license attribution and a separate statement of data and pretrained-model terms. A code license does not grant permission to redistribute data.*
````

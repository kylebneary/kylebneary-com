# kylebneary.com

Personal website — blog, digital resume, and (eventually) projects — built with
Flask and deployed to Google Cloud Run.

## Stack

- **Backend**: [Flask](https://flask.palletsprojects.com/) 3.x, organized as Blueprints
- **Templates**: Jinja2
- **Blog content**: Markdown files with metadata headers, rendered server-side
  via `python-markdown` + `beautifulsoup4`
- **Styling**: a single hand-written stylesheet (`static/css/styles.css`), no
  frontend build step
- **Runtime**: `gunicorn` in production, Flask's dev server locally
- **Hosting**: Docker container on Google Cloud Run

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit together.

## Local development

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt -r requirements-dev.txt

python main.py
# Site available at http://localhost:8080
```

### Running tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

Both run automatically in CI on every pull request (see below).

## Writing a blog post

1. Add a new Markdown file to `blog/posts/`, e.g. `blog/posts/my_new_post.md`.
2. Give it a metadata header (the [Python-Markdown `meta` extension](https://python-markdown.github.io/extensions/meta_data/) format):

   ```markdown
   title: My New Post
   summary: One sentence describing the post
   publication_date: 2026-08-08

   Post content starts here...
   ```
3. The post's URL slug is the filename with underscores replaced by hyphens
   and the extension dropped (`my_new_post.md` → `/blog/my-new-post`).
4. Posts with a `publication_date` in the future are excluded from listings
   automatically, so you can commit drafts ahead of time.
5. Reference images with a path starting `images/`; they're rewritten to
   `blog/static/images/...` automatically at render time.

## Deployment

The site runs on **Google Cloud Run**, built from the root `Dockerfile`.

**Deploys are automatic**: Cloud Run's built-in GitHub integration watches
`main` and redeploys on every push — there's no committed Cloud Build config
or GitHub Actions deploy step, it's configured directly on the Cloud Run
service in GCP. This means **merging a PR into `main` ships to production
immediately**, which is exactly why nothing gets pushed to `main` directly
(see below) and why CI (lint + tests) runs on every PR first.

To deploy manually (e.g. to debug the build), you can still run:

```bash
gcloud run deploy kylebneary-com \
  --source . \
  --region <region> \
  --project <gcp-project-id>
```

## Contributing / branching model

**Nothing is pushed directly to `main`.** All work happens on a branch and
lands via pull request:

```bash
git checkout main
git pull
git checkout -b your-branch-name
# make changes, commit
git push -u origin your-branch-name
# open a PR into main
```

CI (lint + tests, see [`.github/workflows/ci.yml`](.github/workflows/ci.yml))
runs on every PR automatically. `main` should have branch protection enabled
requiring CI to pass and requiring a PR before merge — see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#branch-protection-setup-manual-step)
for the one-time GitHub setting to turn on (it can't be set from the CLI in
this environment).

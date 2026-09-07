# kylebneary.com

Personal profile site — blog, digital resume, and projects — built with
Flask and deployed to Google Cloud Run.

## Stack

- **Backend**: [Flask](https://flask.palletsprojects.com/) 3.x, organized as Blueprints
- **Templates**: Jinja2, with a shared `templates/base.html` carrying the
  design system, nav, footer, and per-page SEO tags (meta description, Open
  Graph/Twitter cards, canonical URL, JSON-LD)
- **Blog & project content**: Markdown files with metadata headers, rendered
  server-side via `python-markdown` + `beautifulsoup4`
- **Styling**: a single hand-written, token-based stylesheet
  (`static/css/styles.css`), no frontend build step
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

`main.py` runs with Flask's debug reloader on, so editing a template, route,
or the stylesheet and refreshing the browser is enough to preview changes —
no separate build/watch step. This is also how to preview redesign/content
work before opening a PR into `main` (nothing under `/blog/` or `/projects/`
requires a rebuild; both re-read their content files on every request).

By default, SEO tags (canonical URLs, sitemap, Open Graph) point at
`https://www.kylebneary.com`. Override with the `SITE_URL` environment
variable if you need them to point elsewhere locally:

```bash
SITE_URL=http://localhost:8080 python main.py
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
4. Posts with a `publication_date` in the future are withheld — from
   listings, the RSS feed, the sitemap, and their own URL — until that moment
   passes. **The stamp accepts a time**, so publication can be scheduled to
   the minute:

   ```markdown
   publication_date: 2026-09-15          # midnight
   publication_date: 2026-09-15 09:30    # 9:30am, site timezone
   publication_date: 2026-09-15T09:30-05:00   # explicit offset
   ```

   Bare stamps are read as wall-clock time in `SITE_TZ` (default
   `America/Chicago`), not the server's timezone — Cloud Run runs in UTC,
   which is why this is set explicitly. Nothing has to run at publication
   time: content is re-read from disk on every request, so a scheduled item
   appears on its own with no deploy and no cron job.

   To preview scheduled content before its date, run with
   `SHOW_UNPUBLISHED=1`. Production leaves it unset.

   The same applies to a project's `date:` in `projects/data/*.md`, which
   gates its card, its write-up page, its code explorer, and its sitemap
   entry. An *undated* project has nothing to wait for and stays visible.
5. Reference images with a path starting `images/`; they're rewritten to
   `blog/static/images/...` automatically at render time. The first image in
   a post is also used as its Open Graph share image automatically.
6. Optionally add a `tags: python, flask, seo` metadata line — tags render
   as chips on the post and in the blog index.

Posts also get a per-post RSS entry (`/blog/feed.xml`), a sitemap entry, and
`BlogPosting` structured data automatically — no extra step needed.

## Adding a project

Projects follow the same pattern as blog posts: each is a Markdown file with
a metadata header in `projects/data/`.

```markdown
title: My Project
summary: One sentence describing what it does
tech: Python, Flask, GCP
repo_url: https://github.com/kylebneary/my-project
live_url: https://my-project.example.com
status: shipped
date: 2026-08-08

Longer description goes here (currently unused by the template, reserved
for a future per-project detail page).
```

`status` drives the badge on the card (`shipped`, `in-progress`, or
`coming-soon` all get their own styling — anything else falls back to a
neutral badge). `repo_url`/`live_url` are both optional; omit either to hide
that link. A `coming-soon` entry renders as a card but gets no detail page,
which is how to list something before it's written up. When no project is
published, `/projects/` falls back to an empty-state line rather than an
empty grid.

## SEO

Every page gets a meta description, canonical URL, Open Graph/Twitter card
tags, and JSON-LD structured data (`Person`/`WebSite` on the home page,
`BlogPosting` on posts, `CollectionPage` on `/projects/`) from
`templates/base.html` — override the `meta_description`, `og_image`,
`canonical`, `og_type`, or `structured_data` Jinja blocks in a page template
if it needs something more specific than the site-wide default.

There's also `/sitemap.xml` (home, blog index, about, projects, and every
blog post, generated dynamically) and `/robots.txt` (points crawlers at the
sitemap), and an RSS feed at `/blog/feed.xml`.

**Canonical domain**: all of the above is built from `SITE_URL`
(`main.py`, defaults to `https://www.kylebneary.com`, overridable via the
`SITE_URL` env var — see [Local development](#local-development)). Pick a
single canonical host (`kylebneary.com` vs `www.kylebneary.com`) in Cloud
Run's domain mapping / DNS and 301-redirect the other one to it — serving
the site on both without a redirect creates duplicate-content pages in
Google's eyes. That mapping lives in GCP/DNS, not in this repo, so it isn't
something a code change can fix — if it turns out the live canonical host is
different from `SITE_URL`'s default, update the one line in `main.py`.

Search Console/Analytics setup is a separate manual step (needs your own
Google account) — not something this repo can wire up.

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

# Architecture

## Overview

This is a small Flask app with no database — all content is either a Jinja2
template or a Markdown file on disk. It's structured as one Flask Blueprint
per site section, each owning its own routes, templates, and (for the blog)
static assets.

```
main.py                  # app entrypoint, registers all blueprints
├── home/                # "/" — landing page (templates only, no routes.py)
├── about_me/            # "/about-me" — resume page
│   └── about_me.py
├── blog/                 # "/blog" — post index + individual posts
│   └── blog.py
├── projects/             # "/projects" — placeholder, not yet linked in nav
│   └── projects.py
├── templates/             # shared base.html + home page template
└── static/                # shared CSS, favicon
```

Each module follows the same shape:

```python
some_bp = Blueprint('some_bp', __name__,
    template_folder='templates', url_prefix='/some-prefix')

@some_bp.route('/')
def index():
    return render_template('some_module/index.html')
```

Blueprints are registered in [`main.py`](../main.py). The blog blueprint also
declares its own `static_folder`/`static_url_path` (`/blog-static`) since it
serves post images independently of the site-wide `static/` folder.

## Request flow

- `GET /` → `home_bp.index` → pulls the 3 most recent blog posts via
  `blog.blog.get_blog_posts()` and renders `templates/index.html`.
- `GET /blog/` → `blog_bp.index` → lists all posts, sorted by
  `publication_date` descending.
- `GET /blog/<post_name>` → `blog_bp.post` → reads
  `blog/posts/<post_name with hyphens back to underscores>.md`, converts it
  to HTML, and rewrites any `images/...` src paths to the blog blueprint's
  static URL.
- `GET /about-me/` → renders the static resume template
  (`about_me/templates/about_me/resume.html`).
- `GET /projects/` → currently renders the site's root `index.html` (the
  homepage template) rather than a projects-specific page — this looks like
  scaffolding for a feature that isn't built yet. The nav link to it is
  commented out in `templates/base.html`. Worth revisiting before advertising
  the section.

## Blog post format

Posts live in `blog/posts/*.md` and are parsed with `python-markdown`'s
`meta` extension. Required front-matter keys: `title`, `summary`,
`publication_date` (format `YYYY-MM-DD`). Posts are:

- **filtered** to only those with a valid, parseable `publication_date` in
  the past (future-dated posts are silently excluded — this doubles as a
  simple "draft" mechanism)
- **sorted** newest-first
- **sliced** to the top 3 for "featured" placements on the home and blog
  index pages

`get_blog_posts()` re-reads and re-parses every Markdown file on every
request — there's no caching. Fine at current post volume; would need
revisiting if the post count grows substantially.

## Deployment

- `Dockerfile` builds a `python:3.12` image, installs `requirements.txt`,
  and runs `python main.py`.
- Cloud Run injects `PORT`; `main.py` reads it via
  `os.environ.get("PORT", 8080)`.
- **Deploys are automatic**, via Cloud Run's built-in GitHub integration:
  the Cloud Run service is configured (in the GCP console, not as anything
  checked into this repo) to watch `main` and build+deploy on every push.
  There's no `cloudbuild.yaml` or GitHub Actions deploy step — the trigger
  lives entirely in GCP. **Merging a PR into `main` ships to production
  within minutes.**

## Known gaps

Tracked here rather than fixed silently, since they change app behavior and
deserve a deliberate decision rather than a drive-by edit:

1. **`Dockerfile` runs the Flask dev server, not gunicorn.** `main.py` calls
   `app.run(debug=True, ...)`, so the container serves production traffic
   through Werkzeug's debug server — including its interactive debugger,
   which allows arbitrary code execution if it's ever reachable. `gunicorn`
   is already in `requirements.txt` but unused. Fix: change the Dockerfile's
   `CMD` to something like `gunicorn --bind 0.0.0.0:8080 main:app` and drop
   `debug=True` (or gate it behind an env var for local dev only).
2. **`/projects/` renders the homepage template**, not a projects-specific
   page (see above). Likely intentional scaffolding, but worth a decision:
   build it out or remove the blueprint until it's ready.
3. **CD isn't gated on CI.** Cloud Run's GitHub integration deploys on every
   push to `main` regardless of whether `.github/workflows/ci.yml` passed —
   the two systems don't talk to each other. The only thing standing between
   a bad push and production is branch protection on `main` (require a PR +
   passing status checks before merge — see below). Without that enabled,
   a direct push to `main` skips CI entirely and deploys anyway.
4. **No caching layer for blog posts** — acceptable today, noted above.

## Branch protection setup (manual step)

GitHub CLI (`gh`) isn't authenticated in the environment this documentation
was generated from, so branch protection on `main` couldn't be configured
programmatically. To require PRs and passing CI before merge, either run:

```bash
gh auth login
gh api repos/kylebneary/kylebneary-com/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint-and-test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":0}' \
  --field restrictions=null
```

or, via the GitHub UI: **Settings → Branches → Add branch protection rule**
for `main`, enabling "Require a pull request before merging" and "Require
status checks to pass before merging" (select the `lint-and-test` check once
it has run at least once).

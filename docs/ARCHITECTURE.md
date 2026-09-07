# Architecture

## Overview

This is a small Flask app with no database — all content is either a Jinja2
template or a Markdown file on disk. It's structured as one Flask Blueprint
per site section, each owning its own routes, templates, and (for the blog)
static assets.

```
main.py                  # app entrypoint, registers all blueprints,
                          # SITE_URL config, /sitemap.xml, /robots.txt
├── home/                 # unused legacy package (home_bp actually lives
│                         # inline in main.py) — see note below
├── about_me/             # "/about-me" — resume page
│   └── about_me.py
├── blog/                 # "/blog" — post index, individual posts, RSS feed
│   ├── blog.py
│   └── posts/            # blog content (Markdown + front-matter)
├── projects/              # "/projects" — project index
│   ├── projects.py
│   └── data/              # project content (Markdown + front-matter)
├── templates/             # shared base.html (design system + SEO tags) +
│                         # home page template + sitemap.xml
└── static/                # shared CSS, favicon, headshot
```

`home/` is vestigial — `home_bp` is defined directly in `main.py` using the
root `templates/` folder, and nothing imports from the `home` package. It's
left in place rather than deleted as part of this redesign to keep the diff
scoped to the pages themselves; safe to remove in a follow-up.

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
- `GET /projects/` → `projects_bp.index` → reads every Markdown file in
  `projects/data/` via `projects.projects.get_projects()` and renders a card
  grid (`projects/templates/projects/index.html`).
- `GET /projects/<slug>` → `projects_bp.detail` → renders one project's
  Markdown body as a full write-up, styled like a blog post, with an
  auto-generated table of contents. Slug is the filename with underscores
  swapped for hyphens, exactly like the blog. Placeholder entries (see below)
  have no body worth showing and 404 here.
- `GET /projects/<slug>/code` and `GET /projects/<slug>/code/<path>` →
  `projects_bp.code` → a browsable file tree over the project's vendored code
  mirror, with server-side Pygments highlighting and a line anchor (`#L-<n>`)
  on every line. See "Code mirrors" below.
- `GET /sitemap.xml`, `GET /robots.txt` → defined directly on `app` in
  `main.py`; the sitemap is generated from the blog/about/projects routes
  plus every blog post at request time (see `templates/sitemap.xml`).
- `GET /blog/feed.xml` → `blog_bp.feed` → RSS 2.0 feed built from the same
  `get_blog_posts()` list used by the blog index.
- `GET /blog/artificial` → `blog_bp.artificial_index` → same post list,
  filtered to posts tagged `artificial` (case-insensitive), rendered with
  its own intro copy (`blog/templates/blog/artificial.html`). This is the
  "Artificial" series landing page: a curated sub-view of the blog, not a
  separate content directory — posts still live in `blog/posts/` and only
  need `tags: artificial, ...` to join the series.
- `GET /blog/artificial/feed.xml` → `blog_bp.artificial_feed` → RSS feed
  scoped to the same filtered list, reusing `blog/templates/blog/feed.xml`
  with title/description/link overrides.

## Content formats

### Blog posts

Posts live in `blog/posts/*.md` and are parsed with `python-markdown`'s
`meta` extension. Required front-matter keys: `title`, `summary`,
`publication_date` (format `YYYY-MM-DD`). Optional: `tags` (comma-separated).
A post is considered part of the **Artificial** series (see above) if its
`tags` include `artificial` — that's the only thing that controls series
membership, computed by `blog._is_artificial()`.
Posts are:

- **filtered** to only those with a valid, parseable `publication_date` that
  has already passed (see "Scheduled publishing" below)
- **sorted** newest-first
- **sliced** to the top 3 for "featured" placements on the home and blog
  index pages
- enriched with a computed **reading time** (word count of the rendered
  HTML / 200wpm) and, if present, the **first post image** (used as the
  page's `og:image` and RSS thumbnail candidate)

`get_blog_posts()` re-reads and re-parses every Markdown file on every
request — there's no caching. Fine at current post volume; would need
revisiting if the post count grows substantially.

### Projects

`projects/data/*.md` follows the same Markdown + front-matter pattern as
blog posts (parsed by `projects.projects.get_projects()`, same
`markdown.Markdown(extensions=['meta'])` approach). Front-matter keys:
`title`, `summary`, `tech` (comma-separated), `repo_url`, `live_url`,
`status`, `date` (sort order and display), `post_url` (a related blog post),
and `code_dir` (see "Code mirrors"). A project earns a detail page when it has
a real Markdown body *and* a status other than `coming-soon`, so a
`coming-soon` entry stays card-only and its detail URL 404s. When nothing is
published — every project scheduled, or none present — the index renders an
empty-state line rather than a bare grid.

`projects/data/caliper.md` is **generated** — it is produced by
`scripts/gen-site-page.ts` in the (private) `x402-bazaar` repo, which extracts
every code block from the source that actually deploys, located by literal
anchor text rather than line numbers. Editing it here is pointless: the next
regeneration overwrites it. The prose lives in that repo's
`site-integration/caliper.md.tmpl`.

### Code mirrors

A project with a `code_dir` key gets a browsable copy of its source at
`/projects/<slug>/code`. The mirror is a **git submodule** under
`projects/code/`:

```
projects/code/x402-worker-template  ->  github.com/kylebneary/x402-worker-template
```

`get_code_files()` walks it, skipping VCS/build noise and lockfiles
(`CODE_SKIP`). File reads are whitelisted against that listing and the
resolved path is confirmed to sit inside the mirror root, so a `../..` in the
URL cannot escape the submodule. Files over `MAX_CODE_BYTES` (256KB) are not
served.

The write-up's code blocks caption themselves with the file and line they came
from, linking to `/projects/<slug>/code/<file>#L-<n>` — which is why the
formatter uses Pygments' `linespans` rather than `lineanchors`: `linespans`
wraps each line in a span carrying the id, so `:target` can highlight the whole
line. `tests/test_routes.py::test_write_up_deep_links_resolve` walks every
caption on the rendered page and asserts both the URL and the anchor exist, so
a snippet that drifts out of range fails CI rather than shipping a dead link.

**Submodules must be initialised or the mirror is empty.** CI does this
(`submodules: true` on `actions/checkout`). Cloud Run's GitHub integration is
outside this repo and may not — and `.dockerignore` excludes `.git`, so the
Dockerfile cannot initialise it either. When the mirror is missing,
`projects_bp.code` **redirects to the canonical GitHub URL** instead of 404ing,
so the write-up's deep links always land somewhere real. The visible symptom of
a build that skipped submodules is therefore `/projects/caliper/code` bouncing
to github.com rather than rendering in-site.

## Scheduled publishing

`content.py` holds the one parser both the blog and projects use.
`parse_publication()` accepts a bare date (`2026-09-15`, meaning midnight), a
date and time (`2026-09-15 09:30`), or either with an explicit offset
(`2026-09-15T09:30-05:00`). Anything without an offset is interpreted as
wall-clock time in `SITE_TZ` (default `America/Chicago`) — **not** the
server's local time, since Cloud Run runs in UTC and would otherwise publish
five or six hours early.

`is_published()` gates visibility. For posts that means listings, the home
page, both RSS feeds, the sitemap, *and* the post's own route — the URL is
derived from the filename and therefore guessable, so the route has to refuse
a future post rather than rely on nobody linking to it. For projects it gates
the card, the detail page, the code explorer, and the sitemap entry. An
undated project stays visible; an undated post does not, matching how each
behaved before times were supported.

Nothing runs at publication time. Content is re-read from disk on every
request with no caching, so a scheduled item becomes visible on its own the
moment its stamp passes — no deploy, no cron, and nothing that can fail at
the moment it matters. The practical consequence is that **merging to `main`
and publishing are separable**: ship the code whenever, and let the stamp
decide when readers see it.

`SHOW_UNPUBLISHED=1` reveals future-dated content, for previewing locally or
verifying a deploy before its content is due. Production leaves it unset.

`site_timezone()` falls back to UTC rather than raising if the tz database is
missing, since an exception there would take down every page that reads dated
content — which is all of them. `tzdata` is in `requirements.txt` so the
lookup works regardless of what the base image ships.

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

## Design system & SEO infrastructure

`static/css/styles.css` is organized around CSS custom properties (colors,
spacing, radius, type scale) defined once in `:root`, rather than repeated
magic values — still a single hand-written stylesheet, no build step. The
mobile nav collapses behind a hamburger using a checkbox-hack (`<input
type="checkbox">` + sibling selectors), so it works with JS disabled.

`templates/base.html` centralizes SEO tags — meta description, canonical
URL, Open Graph/Twitter cards, JSON-LD — as overridable Jinja blocks
(`meta_description`, `canonical`, `og_type`, `og_image`,
`structured_data`), all built from the `SITE_URL` app config value (see
[README#seo](../README.md#seo)). Page templates only need to override the
blocks where the default doesn't apply (e.g. blog posts override `og_type`
to `article` and supply their own `BlogPosting` JSON-LD).

## Known gaps

Tracked here rather than fixed silently, since they change app behavior and
deserve a deliberate decision rather than a drive-by edit:

1. **`Dockerfile` runs the Flask dev server, not gunicorn.** `main.py` calls
   `app.run(debug=True, ...)`, so the container serves production traffic
   through Werkzeug's debug server — including its interactive debugger,
   which allows arbitrary code execution if it's ever reachable. `gunicorn`
   is already in `requirements.txt` but unused. Fix: change the Dockerfile's
   `CMD` to something like `gunicorn --bind 0.0.0.0:8080 main:app` and drop
   `debug=True` (or gate it behind an env var for local dev only). Flagged
   previously and still deliberately out of scope of the site redesign.
2. **CD isn't gated on CI.** Cloud Run's GitHub integration deploys on every
   push to `main` regardless of whether `.github/workflows/ci.yml` passed —
   the two systems don't talk to each other. The only thing standing between
   a bad push and production is branch protection on `main` (require a PR +
   passing status checks before merge — see below). Without that enabled,
   a direct push to `main` skips CI entirely and deploys anyway.
3. **No caching layer for blog/project content** — every request re-reads
   and re-parses the relevant Markdown files from disk. Acceptable at
   current content volume; would need revisiting if either grows
   substantially.
4. **`www` vs apex domain isn't redirected at the DNS/Cloud Run level** —
   `SITE_URL` picks one canonical host for SEO purposes, but if both
   `kylebneary.com` and `www.kylebneary.com` currently resolve to the site
   without one redirecting to the other, that's a duplicate-content issue
   search engines will penalize. This is a Cloud Run domain mapping / DNS
   setting, not something fixable from this repo — see
   [README#seo](../README.md#seo).

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

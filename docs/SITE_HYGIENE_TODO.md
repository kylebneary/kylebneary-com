# Site hygiene checklist — status

Source: an Instagram post listing 20 pre-launch website checks. This file
tracks what was done, what doesn't apply to this site, and what's left for
Kyle to decide or do outside this repo.

## Done (this branch)

1. **Privacy policy** — `/legal/privacy`, honest version: no accounts, no
   forms, no cookies today; notes standard Cloud Run request logging.
2. **Terms and conditions** — `/legal/terms`, lightweight version covering
   content/code licensing, no-warranty, and external links. Not
   attorney-reviewed; fine for a personal blog, revisit if that ever matters
   for liability.
3. **Secrets off the frontend** — audited; no API keys, tokens, or secrets in
   any template, static file, or the app code. Nothing to fix.
4. **Force HTTPS** — added an app-level redirect (`main.py`) for any request
   that reaches the app without `X-Forwarded-Proto: https`, as a
   defense-in-depth backstop behind Cloud Run's TLS termination.
6. **Meta titles + descriptions** — already implemented site-wide via
   `templates/base.html`'s overridable blocks; confirmed all pages
   (home, blog index/post, projects index/detail, about, and now the new
   legal pages) render a title and description.
7. **Social preview image** — already wired: blog posts use their first
   inline image as `og:image`; everything else falls back to the headshot.
   No change needed.
8. **Favicon** — already present and linked in `base.html`.
9. **Sitemap + robots.txt** — already implemented (`main.py`); added the two
   new legal pages to `sitemap.xml`.
10. **Alt text on images** — the one real `<img>` tag already had alt text;
    fixed two blog-post images that had leftover placeholder alt text
    ("Insert Screenshot ... Here") with real descriptions.
13. **Color contrast** — audited every text/background color pair in
    `styles.css` against WCAG. All pass AA (most pass AAA, 6.4:1–17:1).
    No changes needed.
14. **Mobile friendly** — already responsive: viewport meta tag, fluid type
    scale, checkbox-hack hamburger nav, and grid breakpoints throughout.
    Verified, no changes needed.
15. **Custom 404 page** — added (`templates/404.html` + an errorhandler in
    `main.py`), on-brand and links back into the site.
16. **Broken links** — audited every `href` in the codebase. All internal
    links use Flask's `url_for` (so they can't silently rot), and the
    handful of hardcoded external links (GitHub, LinkedIn, mailto) resolve.
    Nothing broken.

## Doesn't apply right now

- **5. Cookie consent banner** — the site sets no cookies today, so there's
  nothing to get consent for. Revisit only if analytics (#19) or another
  cookie-setting tool gets added — see the analytics note below for how to
  avoid needing a banner at all.
- **17. Form validation** / **18. Spam protection** — there are no forms on
  the site (no contact form, no comments, no newsletter signup). Nothing to
  validate or protect. If a contact form gets added later, pair HTML5
  validation with either a honeypot field or Cloudflare Turnstile (there's a
  `turnstile-spin` skill available for that).

## Needs a decision or an external account

- **11. Compress images** — no image tooling (Pillow, pngquant, etc.) was
  reachable from this environment (no network access to install it). Worth
  doing by hand:
  - `static/images/favicon.ico` is **204 KB** — that's enormous for a
    favicon (typically <15 KB). Re-export as a small multi-resolution
    `.ico`, or switch to a 32×32/180×180 PNG set (favicon + apple-touch-icon).
  - `blog/static/images/building_a_site_initial_design.png` (197 KB) and
    `building_a_site_final_design.png` (197 KB) are full-page screenshots —
    run them through any PNG optimizer (tinypng.com, `pngquant`, `oxipng`)
    to knock them down, likely to well under 100 KB each with no visible
    quality loss.
- **12. Page load speed** — couldn't run Lighthouse/PageSpeed Insights from
  this environment (needs a headless browser). Once this branch is deployed,
  run https://pagespeed.web.dev against the live URL. One likely finding
  going in: **`Dockerfile` currently runs Flask's dev server
  (`app.run(debug=True)`), not gunicorn**, which is a real production
  bottleneck (and, worse, a security hole — the interactive debugger allows
  arbitrary code execution if it's ever reachable). This was already flagged
  in `docs/ARCHITECTURE.md` as a deliberately-deferred known gap. `gunicorn`
  is already in `requirements.txt` unused. Worth fixing regardless of the
  Instagram checklist — happy to do it, just didn't want to change the
  Dockerfile/prod startup command without confirmation first.
- **19. Set up analytics** — needs Kyle to create an account somewhere;
  can't be done from here. Recommend a **cookie-free** option (Plausible,
  Fathom, GoatCounter, or Cloudflare Web Analytics) specifically so #5 stays
  moot — no banner needed if nothing sets a cookie. Once there's a site ID,
  it's a small addition to `templates/base.html` (one script tag, gated by
  an env var so local/dev doesn't get counted).
- **20. One clear call to action** — the homepage hero already leads with a
  single primary CTA ("Read the blog →") plus two lighter secondary links,
  which is close to the spirit of this item already. Flagging as a judgment
  call rather than changing it unasked — say the word if you want it
  trimmed further (e.g. down to just the one primary link).

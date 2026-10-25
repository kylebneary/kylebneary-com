# Site hygiene checklist — status

Source: an Instagram post listing 20 pre-launch website checks. This file
tracks what was done, what doesn't apply to this site, and what's left for
Kyle to decide or do outside this repo.

## Done

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
11. **Compress images** — compressed all three oversized assets with no
    visible quality loss:
    - `static/images/favicon.ico`: 204 KB → **8 KB** (re-exported as a
      proper multi-resolution `.ico` at 16/32/48/64px, instead of one
      256×256 frame).
    - `blog/static/images/building_a_site_initial_design.png`: 271 KB →
      **95 KB** (256-color palette quantization — these are UI screenshots
      with mostly flat color, so palette reduction is lossless-looking).
    - `blog/static/images/building_a_site_final_design.png`: 254 KB →
      **87 KB**, same treatment.
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

- **12. Page load speed** — couldn't run Lighthouse/PageSpeed Insights from
  this environment (needs a headless browser). Once this is deployed, run
  https://pagespeed.web.dev against the live URL. Note: the Dockerfile
  previously ran Flask's dev server instead of gunicorn in production (a
  real perf bottleneck and a security hole); that's already fixed and
  merged (see `docs/ARCHITECTURE.md`), so a fresh Lighthouse run should
  reflect gunicorn + the now-compressed images above.
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

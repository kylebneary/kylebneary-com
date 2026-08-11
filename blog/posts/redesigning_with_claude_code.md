---
title: Redesigning This Site with Claude Code
author: Kyle Neary
summary: How an interactive session with Claude Code took this site from a rough MVP to a real personal profile site — SEO, a real projects page, a design overhaul — in about an hour of my attention.
publication_date: 2026-08-11
tags: claude-code, ai-tools, meta, flask
---

# Redesigning This Site with Claude Code

A [previous post](/blog/buildging-a-site) covered how this site got built in the first place — mostly by prompting an AI for chunks of HTML and CSS and wiring them together myself. That worked, but it left the site as a rough first draft: a `/projects` page that secretly rendered the homepage, five placeholder blog posts openly labeled as AI filler, no SEO to speak of, and a design that was fine but forgettable.

This time around I used Claude Code instead, and the process looked pretty different — less "generate me a snippet," more "here's what I want, go figure out how to get there, and check in with me at the decision points." I want to write up how that actually went, because the workflow itself is the more interesting part of this update.

## Starting with a plan, not code

Instead of describing individual pieces (nav bar, blog cards, footer), I gave a single higher-level prompt: redesign the site as a real personal profile for showcasing my blog and projects, make it work well on mobile and desktop, figure out what would help it rank on search engines once it has real content, and do all of it on a `develop` branch with a way to preview locally before anything touched `main`.

Claude Code read through the existing Flask app and templates first, then came back with clarifying questions before writing anything — visual direction, whether to add a CSS build step, what to do with `/projects`, whether to keep the placeholder posts. That back-and-forth took a few minutes and saved a lot of rework: it meant the first version of the code already matched what I wanted instead of needing a redesign of the redesign.

---

## Comparing designs before writing a line of production code

The part that actually changed how I'd approach this next time: when I said the first design pass "didn't work," instead of guessing again, Claude Code built three fully different homepage mockups — different palettes, type pairings, and layouts — and published them as a page I could open and click through side by side. I picked one, we talked about what specifically wasn't landing, and only then did the real templates and CSS get rewritten to match.

Same thing happened with color. I mentioned I wanted cooler tones and generally not red, and got back three concrete accent-color options applied to the actual site layout — a confident cobalt blue, a quieter slate teal, and an indigo — instead of a single guess. I picked cobalt, and it was a one-line change to the site's color tokens once the design system was properly parameterized.

That loop — propose a few real options, compare them visually, commit to one, then implement — turned what could have been several rounds of "no, try again" into two quick decisions.

---

## What actually changed

- **A real `/projects` page.** It was a stub before (it silently rendered the homepage). Now it reads project entries from Markdown files, the same pattern the blog already used, complete with tech tags and status badges — shipped with a couple of clearly-marked placeholder entries until I fill in real projects.
- **The AI-placeholder blog posts are gone.** Five filler posts got deleted since they were actively working against the "real content" goal.
- **SEO groundwork that didn't exist before**: meta descriptions, Open Graph and Twitter card tags, canonical URLs, JSON-LD structured data, a generated `sitemap.xml`, `robots.txt`, and an RSS feed at `/blog/feed.xml`.
- **A properly responsive mobile nav** — and yes, Claude Code introduced a bug here (a CSS selector broke when the header markup got restructured for an unrelated fix) and then found and fixed it after I reported the menu "didn't feel right" on mobile, in the same session.
- **The actual redesign**: a bold sans/serif type pairing, a hairline-rule grid instead of shadowed cards, and now a cobalt-blue accent instead of the original navy/teal.

---

## The speed of it

The part worth being specific about: this was maybe an hour of my actual attention, spread across a handful of short check-ins — approve a plan, react to three mockups, point out a broken menu, pick a color. The actual implementation, testing, and verification happened in the gaps between those messages. Compare that to the original build, which was "under a day" of fairly continuous work. This wasn't a bigger scope done faster so much as the same kind of scope with most of the mechanical work — writing the CSS, wiring up the Markdown parsing, running the linter and test suite, checking every route actually returns 200 — happening without me watching it happen.

The trade-off is that I was reviewing outcomes rather than typing code, which meant catching the mobile nav regression only after actually looking at it, not because I read the CSS and spotted the bug. Interactive-but-asynchronous is a different way of building than either "do it all myself" or "one long AI-generated blob I review at the end," and it's the one I'd reach for again.

---

## What's next

Same as last time, this is a step, not a finish line — real project write-ups need to go into `/projects`, and there's a couple of unpublished posts sitting on a branch waiting to be merged in. But for the first time, the plumbing underneath (SEO, content patterns, a design system with actual tokens instead of one-off values) is built to support that instead of getting in the way of it.

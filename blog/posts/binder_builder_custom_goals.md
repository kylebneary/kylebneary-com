---
title: Binder Builder Gets Custom Goals
author: Kyle Neary
summary: The latest phase of Binder Builder lets you build a collection goal out of exactly the cards you want, not just "a set" or "a master set" — plus a new card-search view and a Grand Master Set goal type for special printings.
publication_date: 2026-11-03 09:50
tags: binder-builder, pokemon-tcg, side-projects
---

[Binder Builder](/projects/binder-builder) is the local-first Pokémon TCG toolkit I've been
building — a tracker for what you own, an optimizer that Monte-Carlos the cheapest way to finish
a set, and a binder designer that auto-arranges your collection into themed spreads. The project
page has a live demo of the binder designer and the code behind the Monte Carlo engine and the
Michi auto-layout scorer, if you haven't seen those yet. This post is about what's new since: a
phase of work I'd been calling "custom goals."

## What a goal used to be

A goal in Binder Builder is the thing you're trying to complete — "finish this set," track
progress, see what's left and what it'd cost. Until now, a goal meant one of two shapes: a whole
set, or a whole master set (every variant of every card). Both are rule-built — the app figures
out what's in them and keeps them in sync as new cards get added to the catalogue.

That's fine if you actually want the whole set. It's the wrong shape if you don't — say you only
care about the Pikachu line in a given set, or you're chasing a dozen specific illustration
rares across several sets and don't want 180 commons cluttering the goal just to track them.

## Pick exactly the cards you want

A goal can now be **custom**: you hand-pick the cards, and that list *is* the goal — nothing
auto-added, nothing to keep in sync. The flip side is that a custom goal can't be edited like a
rule-built one; you convert a set/master-set goal to custom explicitly if you want to start
pruning it by hand, rather than the app silently guessing which edits you meant as permanent.

The new way to build one of these is a **card-search view**: filter across the whole catalogue —
by set, rarity, name, whatever — and save the results straight into a goal, either a new one or
an existing one. The same filtering logic also backs the binder designer's card pool now, so
what you see in search is what you can actually drag into a binder.

## Grand Master Set: the master set, for real this time

A master set already meant "every variant," but English Pokémon product has a long tail of
printings that don't show up as ordinary variants — 1st Edition and Unlimited stamps, Shadowless,
various promo stamps. A plain master set has always quietly ignored those. **Grand Master Set**
is a new goal type that counts them too, so "complete the master set" can actually mean
complete, special printings included.

Getting there also meant teaching the app to handle cards with no price feed data at all — some
of these printings just don't have a market price anywhere public — rather than letting an
unpriced card silently fall out of a goal or a binder. Not a visible feature on its own, but the
thing that kept custom goals and Grand Master Sets from breaking the moment they hit a card like
that.

## What's not in the live demo

The [project page's live demo](/projects/binder-builder) now goes beyond just the binder
designer — it's a read-only tour of sets, a few example goals, and the portfolio dashboard, all
against the same small seeded fixture, no backend, running entirely in your browser. You can open
a Grand Master Set goal and a hand-picked custom one there and see exactly what they look like.
What's still missing is *building* one: card search and goal creation/editing need their own
mocked endpoints, and faking those convincingly felt like a bigger lift than this update
warranted. They're live in the real app today, just not in the sandboxed version you can click
around without installing anything.

## What's next

Next up on the roadmap is some admin tooling for data correction — a way to fix a mis-tagged
card or a wrong price without going around the database by hand. Right now that's a design, not
code. I'll write it up once there's something to show.

title: Binder Builder
summary: A local-first Pokémon TCG toolkit — track a collection, Monte-Carlo the cheapest way to finish a set, and auto-design binder spreads with a taste-explicit scoring function. Try the binder designer live, no account or install required.
tech: Python, FastAPI, SQLAlchemy, NumPy, React, TypeScript, Vite, TanStack Query
repo_url: https://github.com/kylebneary/binder-builder
live_url: /static/binder-builder-demo/index.html
status: in-progress
date: 2026-09-07 12:00

Binder Builder is three tools sharing one local database: a **tracker** for what you actually
own, an **optimizer** that runs a Monte Carlo simulation to answer "singles, sealed, or both?",
and a **binder designer** that auto-arranges your collection into themed spreads and exports the
print-ready inserts. It's local-first on purpose — your collection and its value live in a SQLite
file on your machine, not in someone else's database.

## Try the binder designer, live

The [live demo](/static/binder-builder-demo/index.html) is the real frontend — same React
components, same drag-and-drop grid, same auto-layout and Michi scoring code — running entirely
in your browser against a seeded fixture of 39 cards. There's no backend behind it: dragging a
card, clicking **Auto-layout**, or running **Michi** all execute for real, in JavaScript, in the
tab. It opens as its own page rather than an iframe on this one, because a drag-and-drop pocket
grid wants real width, not a box squeezed into an article column.

Two things are honestly disabled rather than faked: PDF and PNG export, which need the real
backend's rendering pipeline, show an explanatory message instead of a download. Everything else
— the part that's actually interesting to try — works.

## The optimizer: a Monte Carlo engine, not a point estimate

Pull rates for English Pokémon product are unpublished; every figure the optimizer uses is a
community estimate. So instead of pretending to a single "expected cost," it draws thousands of
simulated box openings and reports a distribution — p10 through p95 — net of what duplicates
resell for.

```python
"""Vectorised Monte Carlo engine. The primary source of truth.

PERFORMANCE CONTRACT: 100,000 trials of a 36-pack box over a ~200-card set in under 2 seconds.
That is only reachable by drawing all trials at once against integer card indices. A per-pack
Python loop is roughly 100x too slow and will make the UI unusable -- design for NumPy from
the first line rather than optimising later.
"""
```

The whole engine ([`backend/app/sim/montecarlo.py`](https://github.com/kylebneary/binder-builder/blob/main/backend/app/sim/montecarlo.py))
is built around that contract. Every pack slot across every trial is drawn in one vectorized pass
against a `(n_trials, n_pool)` count matrix — no Python loop over packs — and scatter-added with
`np.bincount` on a flattened `trial * n_pool + card` index rather than `np.add.at`, which is
unbuffered and far slower at this scale:

```python
def simulate(
    strategy: Strategy,
    pool: CardPool,
    boxes: dict[int, BoxSpec],
    params: CostParams,
    n_trials: int = 20_000,
    seed: int = 0,
) -> SimResult:
    """NetCost = SealedCost + SinglesCost(remaining) - Liquidation(dupes)."""
    rng = np.random.default_rng(seed)
    ...
    singles = singles_cost(still_needed_mask, pool, params)
    liquidation = liquidation_value(dupes, pool, params)
    net_cost = sealed_cost + singles - liquidation

    return SimResult(
        mean=float(net_cost.mean()),
        sd=float(net_cost.std(ddof=1)) if n_trials > 1 else 0.0,
        p10=float(np.percentile(net_cost, 10)),
        p50=float(np.percentile(net_cost, 50)),
        p90=float(np.percentile(net_cost, 90)),
        p95=float(np.percentile(net_cost, 95)),
        ...
    )
```

`NetCost` is sealed spend plus what's still needed as singles, minus what duplicates recoup at
resale. Reporting p10/p50/p90/p95 instead of a mean is the point: two strategies with the same
average cost can have very different tail risk, and "buy a booster box" is a bet on variance as
much as it is on price.

## The binder designer: a scoring function that admits what it can't measure

The [Michi method](https://github.com/kylebneary/binder-builder/blob/feat/phase-3-binder-michi/backend/app/binder/michi.py)
auto-arranges a collection into themed two-page spreads — by species, artist, colour, or evolution
line — and scores every candidate layout on five weighted terms: symmetry, colour coherence, hero
centrality, fill balance, and an orphan penalty for a themed group split across non-adjacent pages.

The interesting design decision isn't the weights, it's what happens when a term can't be
measured:

```python
sym = sum(symmetry_score(p) for p in plans) / len(plans)
fill = sum(fill_balance(p) for p in plans) / len(plans)

colours = [v for v in (colour_coherence(p) for p in plans) if v is not None]
colour = sum(colours) / len(colours) if colours else None
heroes = [v for v in (hero_centrality(p) for p in plans) if v is not None]
hero = sum(heroes) / len(heroes) if heroes else None

terms = [("symmetry", w.symmetry, sym), ("fill", w.fill, fill),
         ("colour", w.colour, colour), ("hero", w.hero, hero)]
measured = [(n, wt, v) for n, wt, v in terms if v is not None]
unmeasured = tuple(n for n, _, v in terms if v is None)

weight_sum = sum(wt for _, wt, _ in measured)
base = sum(wt * v for _, wt, v in measured) / weight_sum if weight_sum else 0.0
```

Colour coherence needs a card's extracted CIELAB value, which doesn't exist until
`bb binder extract-colors` has run against your card images. Scoring a missing term as `0` would
punish a layout for a data gap that has nothing to do with the layout; scoring it as `1` would
flatter it. So an unmeasured term is dropped and the remaining weights are renormalised over just
what was actually measured, and the breakdown says which terms counted — the live demo's score
panel shows exactly this: colour comes back `null` and listed under "not measured," because the
seeded fixture never ran colour extraction either.

## How the live demo runs without a live backend

The real app is a FastAPI + SQLAlchemy backend behind the React frontend, with no hosted
deployment anywhere — it's local-first by design, run with `make api` / `make web` against your
own SQLite file. Standing up a real multi-tenant instance of that just to demo one feature felt
like the wrong trade, so the demo takes a narrower path: the same frontend, built with a
`VITE_DEMO_MODE` flag that swaps every network call for an in-browser mock.

```typescript
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  if (DEMO_MODE) return demoApi<T>(path, init);
  const res = await fetch(`${BASE}${path}`, { ... });
  ...
}
```

Every hook in `lib/queries.ts` already funneled through this one `api()` function, so the mock
only had to live in one place. `demoApi.ts` answers the handful of endpoints the binder designer
actually calls — set/card data, layout load, placement upserts, auto-layout, Michi — against a
39-card fixture shaped like the real `pokemontcg.io` wire format, entirely in memory for the
lifetime of the tab. Auto-layout and Michi run the same clustering and scoring logic client-side
in TypeScript, not a hardcoded response, so the score panel reflects a real (if smaller) instance
of the algorithm above.

That build gets `vite build --base=/static/binder-builder-demo/` and ships as static files
committed straight into this site's own `static/` folder — no separate host, no extra deploy
pipeline, no bill. It rides along on the same Cloud Run deploy as everything else on this page.

## Where it stands

Phase 3 of the roadmap: the tracker and optimizer are built, the binder designer's grid editor,
insert export, and Michi auto-layout landed in the last stretch of commits, and the Michi branch
showcased above hasn't merged to `main` yet. The honest caveat that applies to the whole project
also applies to every number the optimizer or this demo shows you: pull rates are community
estimates of unknown sample size, treated as a well-reasoned argument, never an oracle.

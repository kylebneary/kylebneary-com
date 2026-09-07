---
title: Getting Paid by Robots
author: Kyle Neary
summary: A walk through x402 — the protocol that lets one AI agent pay another for an API call — and an honest log of what it actually took to ship an endpoint on it, including the two days I lost to a wallet CLI that doesn't work on Windows.
publication_date: 2026-08-30
tags: x402, agentic-commerce, cloudflare, typescript
---

Most of the engineering on a project designed to make money autonomously turns out to be about how to make it stop.

That's the punchline, so I'll put it first. The rest of this is the story of building [Caliper](/projects/caliper) — a small paid API that other AI agents can buy from, one call at a time, without ever creating an account — and what I learned about the state of machine-to-machine commerce along the way.

There are two halves here. The first is an explainer: what x402 is, why anyone resurrected HTTP status code 402, and whether the market for it is real. The second is the build log, including the parts that went badly.

---

## The status code nobody ever used

If you've spent time in HTTP's error range you've probably seen `402 Payment Required` sitting between `401 Unauthorized` and `403 Forbidden`, marked in the spec as *reserved for future use*. It's been reserved since 1997. Nearly three decades of "future use" with no standard behind it, because nobody solved the underlying problem: there was never a way to attach an actual payment to an HTTP request that worked at web scale and web speed.

The card networks can't do it. A $0.05 API call costs more in interchange fees than it's worth. Every attempt to work around that — prepaid credits, monthly minimums, API keys tied to a billing account — pushes the problem up a layer into account management, which requires a human to sign up, enter a card, agree to terms, and remember a password.

That constraint was invisible as long as the buyer was a person. It becomes the whole problem the moment the buyer is software.

An AI agent doing a research task can't fill out a signup form for a data provider it discovered thirty seconds ago. It can't agree to terms of service on your behalf. It can't wait three business days for API access approval. The agent economy people keep predicting runs headfirst into the fact that every useful API on the internet is gated behind a human-shaped onboarding flow.

## What x402 actually does

x402, [introduced by Coinbase](https://www.coinbase.com/developer-platform/discover/launches/x402) and now developed as an open standard, finally gives 402 a defined behavior. The whole protocol fits in a paragraph:

A client requests your endpoint. It has no key, no account, no relationship with you at all. Your server returns **HTTP 402** with a `PAYMENT-REQUIRED` header specifying a price, an asset, and a destination address. The client's wallet signs a stablecoin transfer for exactly that amount. A facilitator service settles it on-chain. Your server sees the settled payment, runs the handler, and returns the response.

That's it. No account. No API key. No invoice, no subscription, no free tier to abuse. **The payment is the authentication.** A caller that paid is authorized, and a caller that didn't gets a 402 explaining exactly what it would cost to change that.

<figure class="diagram">
<svg viewBox="0 0 700 396" role="img" aria-labelledby="hs-title hs-desc" xmlns="http://www.w3.org/2000/svg">
  <title id="hs-title">The x402 payment handshake</title>
  <desc id="hs-desc">A buying agent requests a paid route and is refused with HTTP 402 and payment terms. It signs a USDC payment and retries. The Worker asks the facilitator to verify and settle on Base, and only then runs the handler and returns JSON.</desc>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11.5">

    <!-- lifeline headers -->
    <g fill="none" stroke="var(--ink, #15161b)" stroke-width="1.5">
      <rect x="14" y="10" width="150" height="30"/>
      <rect x="272" y="10" width="150" height="30"/>
      <rect x="530" y="10" width="156" height="30"/>
    </g>
    <g fill="var(--ink, #15161b)" font-weight="700" text-anchor="middle" font-size="11">
      <text x="89" y="30">BUYING AGENT</text>
      <text x="347" y="30">CALIPER WORKER</text>
      <text x="608" y="30">FACILITATOR</text>
    </g>

    <!-- lifelines -->
    <g stroke="var(--rule, #dedcd3)" stroke-width="1.5" stroke-dasharray="3 4">
      <line x1="89" y1="40" x2="89" y2="374"/>
      <line x1="347" y1="40" x2="347" y2="374"/>
      <line x1="608" y1="40" x2="608" y2="374"/>
    </g>

    <defs>
      <marker id="ah-ink" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--ink, #15161b)"/>
      </marker>
      <marker id="ah-acc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--accent, #2a52a0)"/>
      </marker>
    </defs>

    <!-- 1: unpaid request -->
    <line x1="89" y1="72" x2="341" y2="72" stroke="var(--ink, #15161b)" stroke-width="1.5" marker-end="url(#ah-ink)"/>
    <text x="215" y="66" fill="var(--ink, #15161b)" text-anchor="middle">GET /v1/... &#160;(no key, no account)</text>

    <!-- 2: 402 -->
    <line x1="347" y1="110" x2="95" y2="110" stroke="var(--accent, #2a52a0)" stroke-width="1.5" marker-end="url(#ah-acc)"/>
    <text x="221" y="104" fill="var(--accent, #2a52a0)" text-anchor="middle" font-weight="700">402 &#160;PAYMENT-REQUIRED</text>
    <text x="221" y="126" fill="var(--ink-muted, #5a5c66)" text-anchor="middle" font-size="10.5">price &#183; asset &#183; pay-to address</text>

    <!-- 3: sign (self) -->
    <path d="M89,152 h44 a8,8 0 0 1 8,8 v14 a8,8 0 0 1 -8,8 h-38" fill="none" stroke="var(--ink-muted, #5a5c66)" stroke-width="1.5" marker-end="url(#ah-ink)"/>
    <text x="153" y="169" fill="var(--ink-muted, #5a5c66)" font-size="10.5">wallet signs USDC transfer</text>

    <!-- 4: retry with payment -->
    <line x1="89" y1="216" x2="341" y2="216" stroke="var(--ink, #15161b)" stroke-width="1.5" marker-end="url(#ah-ink)"/>
    <text x="215" y="210" fill="var(--ink, #15161b)" text-anchor="middle">retry, with signed payment</text>

    <!-- 5: settle -->
    <line x1="347" y1="254" x2="602" y2="254" stroke="var(--ink, #15161b)" stroke-width="1.5" marker-end="url(#ah-ink)"/>
    <text x="474" y="248" fill="var(--ink, #15161b)" text-anchor="middle">verify + settle</text>
    <text x="474" y="269" fill="var(--ink-muted, #5a5c66)" text-anchor="middle" font-size="10.5">USDC on Base</text>

    <!-- 6: settled -->
    <line x1="608" y1="298" x2="353" y2="298" stroke="var(--ink-muted, #5a5c66)" stroke-width="1.5" marker-end="url(#ah-ink)"/>
    <text x="480" y="292" fill="var(--ink-muted, #5a5c66)" text-anchor="middle" font-size="10.5">settled &#8594; handler runs</text>

    <!-- 7: response -->
    <line x1="347" y1="342" x2="95" y2="342" stroke="var(--accent, #2a52a0)" stroke-width="1.5" marker-end="url(#ah-acc)"/>
    <text x="221" y="336" fill="var(--accent, #2a52a0)" text-anchor="middle" font-weight="700">200 &#160;application/json</text>

  </g>
</svg>
<figcaption>One paid call. The handler never sees step 1 &mdash; the middleware answers it.</figcaption>
</figure>

Two properties make this work where earlier micropayment attempts didn't. The money is a stablecoin — USDC — so a nickel is a nickel and neither side is holding a volatile asset for the ten seconds the transaction takes. And it settles on a layer-2 network (Base, in my case) where the fee to move that nickel is a fraction of a cent rather than several dollars of Ethereum mainnet gas. Both of those are recent enough that "1997's reserved status code" and "actually viable" only became compatible in about the last two years.

The discovery half is equally simple. You serve a free `/.well-known/x402.json` describing what you sell and what it costs. Once your endpoint processes its first paid call, it gets indexed into the **x402 Bazaar** — the registry agents query to find services — and shows up on marketplaces like Agentic.Market. You don't apply. You don't get approved. You take one payment and you're in the catalog.

That last part is either the most exciting or the most alarming thing about the protocol, depending on your temperament. It's both, is my read.

---

## The honest version of the market

Here's where I have to be careful, because this is a space with a lot of very confident numbers flying around.

Depending on which dashboard you look at, x402 either settled tens of millions of dollars across a hundred million-plus transactions, or it's a network doing a few tens of thousands of dollars a day of real economic activity. Both figures get cited. They're not actually in conflict — they're measuring different things, and the gap between them is the interesting part.

When I did my research pass in **May 2026**, the picture I put together looked like this:

| Metric | Value |
|---|---|
| Curated services on Agentic.Market | ~70 |
| Published daily transaction volume | ~$28,000 |
| Estimated share that's wash trading | ~50% |
| Average transaction size | ~$0.20 |
| Endpoints passing the 402audit reliability bar | 59 |
| Average quality score across audited services | 34 / 100 |
| Services missing MCP discovery files | 52 / 70 |
| Services not returning valid JSON at their root | 51 / 70 |

Some caveats on all of that: these are point-in-time figures from a fast-moving ecosystem, the wash-trade estimate is an estimate, and "real volume" depends entirely on what you're willing to count. [CoinDesk's assessment in March](https://www.coindesk.com/markets/2026/03/11/coinbase-backed-ai-payments-protocol-wants-to-fix-micropayment-but-demand-is-just-not-there-yet) was blunter than mine: the plumbing works, the demand isn't there yet.

But look at the bottom four rows, because they're the ones that changed what I built.

Three quarters of the services on this marketplace are misconfigured. The average quality score is one third. Most of them don't ship the discovery files that make them findable, and most of them return HTML — to a buyer that is definitionally a machine — where JSON belongs.

**The Bazaar isn't under-supplied with ideas. It's under-supplied with competence.** That's a genuinely unusual market condition, and it's a much better thing to find than an unmet demand, because competence is something you can decide to have.

It also rules out most of what a person's first instinct would be. General inference? Anthropic and OpenAI are already listed. Crypto prices? CoinGecko. Stock data? Bloomberg. Web search? Firecrawl and Tavily. On-chain RPC? Alchemy. If your endpoint idea is a commodity, you are competing on price against a company whose marginal cost is lower than yours and whose name the buying agent already recognizes.

What's left, and what I picked, is a narrow band: **meta-services for other x402 builders** — audit and validation tools that exist precisely because three quarters of the market is broken — and **synthesis endpoints** that fuse several free upstream calls into one structured answer, selling the orchestration rather than the data.

---

## The actual build

The server is a single Cloudflare Worker. TypeScript, [Hono](https://hono.dev/) for routing, the x402 payment middleware wrapped around exactly one route. It's about eighty-five lines and it runs on the free tier, which covers 100,000 requests a day.

The whole system is five files:

- **`src/index.ts`** — the server. Free routes, the paywall, the handlers.
- **`scripts/init-wallet.ts`** — derives the receiving address from Coinbase Developer Platform credentials. Deterministic, so re-running it returns the same address rather than creating a second wallet.
- **`scripts/smoke-test.ts`** — a *buying* client, used to pay my own endpoint. Proving the paywall works means actually buying something.
- **`wrangler.toml`** — five lines. No build step, no bundler config, no container.
- **`memory.json`** — the ledger and the kill-switches. More on that below.

There's no database. The Worker holds two secrets: the address to be paid at, and the URL of the facilitator that settles payments. Notably absent is any credential for *signing* — this thing receives money and never spends it, so it holds nothing that could move funds.

I wrote the whole system up component by component, with the real source, [on the project page](/projects/caliper). What follows here is the part that surprised me.

Three routes total. Two are free — a health check and the discovery document — and one is paid. The paid one currently returns a fortune cookie.

That is not a joke about the state of the market, though it works as one. The fortune cookie is a deliberate smoke test: an endpoint with zero external dependencies, no LLM call, no upstream API, nothing that can fail for a reason unrelated to payments. If a paid request clears end-to-end against a hardcoded array of aphorisms, then the wallet, the middleware, the facilitator, the settlement, the deploy pipeline, and the Bazaar listing all work. Then, and only then, is it worth swapping the fortune list for something anyone would actually buy.

The one piece of the wiring that isn't obvious from the docs:

```typescript
// The x402 resource server is stateful — it fetches facilitator
// capabilities on first use. Build it once per isolate, not per request.
let cachedMiddleware: ReturnType<typeof paymentMiddleware> | undefined
function paidRouteMiddleware(env: Env) {
  if (cachedMiddleware) return cachedMiddleware
  const facilitator = new HTTPFacilitatorClient({ url: env.CDP_FACILITATOR_URL })
  const server = new x402ResourceServer(facilitator)
    .register('eip155:8453', new ExactEvmScheme())
  cachedMiddleware = paymentMiddleware(/* … route config … */, server)
  return cachedMiddleware
}
```

Constructing that per request means a network round-trip to the facilitator on every single call, which will quietly wreck the P99 latency that the ecosystem's audit services measure you on. Build it once, cache it in the isolate.

Everything else is boring in the good way. The price, the network, and the destination address go in a route config. The middleware handles the 402, the header, and the settlement check. My handler never sees an unpaid request.

---

## Where the two days went

None of the difficulty was in the payment protocol. It was all in the six-month-old ecosystem around it.

### The wallet CLI that doesn't run on Windows

Coinbase's Agentic Wallet ships a CLI called `awal` that holds your key in a hardware-isolated enclave, which is a genuinely nice property — your own code can't exfiltrate the key even if it's compromised. The setup docs are clean. I'm on Windows.

I hit three independent portability bugs, each one hiding behind the last:

1. **`spawn EINVAL`.** The wallet launches an Electron companion process by spawning `electron.cmd` without `shell: true`. Node has refused to do that since the security release for [CVE-2024-27980](https://nodejs.org/en/blog/vulnerability/april-2024-security-releases) — spawning `.cmd` and `.bat` files without an explicit shell was a command-injection vector. The function right next to it in the same file gets this right. This one was missed.
2. **Hardcoded `/tmp/` paths.** Both halves of the tool expect a lock file and an IPC bridge directory under `/tmp/`, which on Windows resolves to `C:\tmp\` — a directory that does not exist. The write fails silently, the wallet concludes another instance owns the lock, and exits. Fixable with `mkdir C:\tmp`, which is a deeply unsatisfying thing to type.
3. **`fs.watch` misses events.** With the first two patched, the wallet launches and creates its bridge directory. The CLI writes request files into it. The wallet watches that directory with `fs.watch` and never sees them. Windows' `ReadDirectoryChangesW` has different semantics from Linux's `inotify` and reliably drops these short-lived create events. There's no fix for this one that doesn't involve rewriting a minified bundle's watcher as a polling loop.

Every one of these is patchable. None of the patches survive `npm install -g awal@latest`. None of them affect Mac or Linux users, which is exactly why they're still there.

I spent a while setting up WSL to escape the whole category, then stopped and asked a better question: *do I need this tool at all?* The answer was no. Coinbase's server-wallet SDK does the same job — custody the key, sign the payment — headlessly, cross-platform, in-process, with no Electron window and no IPC bridge. Twenty lines of TypeScript replaced the entire CLI, and it works in a Worker, which the CLI never could have.

The lesson I'd actually generalize: **when a tool fights you three times on the same axis, check whether it's on your critical path before you fix it a fourth time.** I fixed two bugs I didn't need to fix, on the way to discovering I didn't need the tool.

### Every tutorial online is written against the old SDK

The second sinkhole was subtler. The x402 client and server libraries were re-published under a new scoped namespace, and the API changed shape in the move. Meanwhile a parallel set of unscoped packages exists under the standards foundation's namespace, one major version behind, with names close enough to be confusing and types incompatible enough that mixing them won't build.

So: three plausible package names for the same job, two of them wrong, and a search engine full of tutorials written against a signature that no longer exists. The middleware went from taking three arguments to two. Route keys went from bare paths to `"GET /path"`. The per-route config restructured. The network identifier went from the string `"base"` to CAIP-2 form, `"eip155:8453"`.

There's no clever lesson here, just a tax you pay for building on something young. What I did about it was write down the migration — old signature, new signature, what moved where — in the repo, so the next person through (very likely me in three months) doesn't re-derive it from npm archaeology.

---

## Making it stop

Which brings me back to the opening line.

The thing I actually spent the most care on isn't the endpoint. It's the set of constraints around it, written down before deploying anything:

- **Hard kill-switches in a versioned state file** — a minimum wallet balance, a monthly compute ceiling, a consecutive-failure cap per endpoint. Any one trips and the thing stops.
- **A pricing floor.** Compute cost must stay under 25% of the price of a call, or the endpoint isn't viable and doesn't ship. This is a rule for me, not a runtime check — it kills ideas at the design stage.
- **Per-payer daily caps.** Not for abuse in the usual sense; the specific attack here is someone spamming your endpoint with *real payments* to inflate your apparent volume, then pointing at it as evidence of wash trading. In a market where reputation is the product, that's a cheap way to hurt you.
- **No autonomous outflows.** The wallet receives. It doesn't spend, doesn't trade, and doesn't move funds without me confirming each time. The enclave protects against key theft; it does not protect against *authorized* stupidity.

None of this is exotic. It's just that when a project's premise is "software that earns money without supervision," every one of these is load-bearing rather than nice-to-have, and the failure modes are all financial. It's a different feeling from shipping a web app, where the worst case is usually an apologetic status page.

## Where it stands

The Worker is deployed. Health check is green, the paywall returns a clean 402 with the right headers, and the discovery document is being served. The smoke-test payment — where I pay my own endpoint a nickel and watch it clear — hasn't run yet. That's the next thing, and it's the one that flips this from *deployed* to *live*, because the Bazaar only indexes an endpoint after it processes a real payment.

After that, the fortune cookie gets deleted and three real endpoints go in its place: a discovery-file auditor, a repo triage service, and a domain intelligence endpoint. All three are aimed at that "under-supplied with competence" gap rather than at competing with Bloomberg.

Will it make money? Probably a little, possibly nothing. I put the realistic ceiling for a careful solo operator somewhere between "lose thirty dollars on compute that didn't recoup" and "clear fifty," and I'd be lying if I said I had a strong prior on where in that band it lands. That's not the reason to do it.

The reason is that x402 is a well-designed protocol solving a coordination problem that is definitely coming, arriving a couple of years before the demand for it. The interesting time to learn a piece of infrastructure is while it's still small enough that you can read the whole thing and one person's competence is a real advantage. That window is open right now, and it won't be for long.

The scaffold is [on GitHub](https://github.com/kylebneary/x402-worker-template) as a template you can deploy — the Worker, the wallet script, and the buying client, with everything Caliper-specific taken out. The builder's guide I wrote while working through it — market analysis, the runbook, and an appendix documenting all three Windows bugs — is still in the private working repo.

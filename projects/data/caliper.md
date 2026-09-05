title: Caliper
summary: A paid API that AI agents buy from directly — one HTTP call, one stablecoin micropayment, no account or API key involved. Built on x402 and running on Cloudflare's edge.
tech: TypeScript, Cloudflare Workers, Hono, x402, USDC on Base
repo_url: https://github.com/kylebneary/x402-worker-template
code_dir: x402-worker-template
live_url:
post_url: /blog/getting-paid-by-robots-x402
status: in-progress
date: 2026-08-30

<!-- GENERATED FILE — do not edit. Produced by scripts/gen-site-page.ts in the
     x402-bazaar repo; the prose lives in site-integration/caliper.md.tmpl and
     every code block is extracted from the source that actually deploys. -->

Caliper is a machine-to-machine API. Its customers are not people — they're AI
agents, which find it in a public registry, pay for a single call in USDC, and
get structured JSON back. There is no signup, no API key, and no billing
relationship. **The payment is the authentication.**

It's built on [x402](https://www.coinbase.com/developer-platform/discover/launches/x402),
the open standard that finally gives HTTP's long-reserved `402 Payment
Required` status code a defined behavior. This page walks the whole system,
component by component, with the real source. If you want the story of *why*
rather than *how* — the market, the dead ends, the two days I lost to a wallet
CLI — that's in
[Getting Paid by Robots](/blog/getting-paid-by-robots-x402).

## The payment handshake

Everything else on this page is in service of one exchange:

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

Steps 1 and 2 are the whole trick. A caller arrives with no credentials, and
instead of a `401` that leaves it stuck, it gets a `402` carrying *machine-readable instructions for how to become
authorized* — a price, an asset, and a destination address. There's nothing to sign up for. The agent reads the terms,
decides whether a nickel is worth it, pays, and retries.

By step 7 the money has already settled on [Base](https://base.org). No
invoicing, no reconciliation, no chargebacks.

## What's in the repository

The deployable is one Cloudflare Worker. Everything else is either operational
scripting or documentation.

```text
src/index.ts              the entire server — free routes, paywall, handlers
scripts/init-wallet.ts    derives the receiving address from CDP credentials
scripts/smoke-test.ts     a buying client, used to pay my own endpoint
wrangler.toml             deploy target and runtime config
.env.example              every secret the Worker reads, documented by name
```

That's the published template, and it's the code quoted throughout this page.
The working repo it was extracted from carries two more files that aren't
public — an operating ledger (`memory.json`, discussed below) and a builder's
guide holding the market analysis and runbook. Where this page draws on those,
it quotes them inline rather than pointing you at a repository you can't open.

Runtime dependencies, in full:

| Package | Version |
|---|---|
| `@coinbase/cdp-sdk` | 1.29.0 |
| `@x402/core` | 2.13.0 |
| `@x402/evm` | 2.13.0 |
| `@x402/fetch` | 2.13.0 |
| `@x402/hono` | 2.13.0 |
| `hono` | 4.7.1 |
| `viem` | 2.21.26 |

`hono` is the HTTP framework — chosen for a small edge footprint. The `@x402/*`
family is the payment protocol implementation: `core` for the facilitator
client and resource server, `evm` for the EVM payment scheme, `hono` for the
middleware binding, `fetch` for the buyer side. `@coinbase/cdp-sdk` custodies
the wallet, and `viem` supplies the Ethereum primitives underneath.

## The Worker

The server is about eighty-five lines. Here's the top of it:

<p class="code-source"><a href="/projects/caliper/code/src/index.ts">src/index.ts</a></p>

```typescript
import { Hono } from 'hono'
import { paymentMiddleware, x402ResourceServer } from '@x402/hono'
import { HTTPFacilitatorClient } from '@x402/core/server'
import { ExactEvmScheme } from '@x402/evm/exact/server'

type Env = {
  SERVER_PAY_TO_ADDRESS: string
  CDP_FACILITATOR_URL: string
}
```

Two secrets, and that's the entire runtime configuration. `SERVER_PAY_TO_ADDRESS`
is where USDC accrues. `CDP_FACILITATOR_URL` points at the service that verifies
and settles payments. Notably absent: any credential for *signing*. This Worker
receives money and never spends it, so it holds nothing that could move funds.

### Free routes, and why they matter

<p class="code-source"><a href="/projects/caliper/code/src/index.ts#L-33">src/index.ts:33</a></p>

```typescript
app.get('/health', (c) => c.json({ ok: true, ts: Date.now() }))

app.get('/.well-known/x402.json', (c) =>
  c.json({
    x402Version: 2,
    lastUpdated: new Date().toISOString(),
    accepts: [{ scheme: 'exact', network: 'eip155:8453', price: '$0.05' }],
    metadata: {
      name: 'Caliper',
      description:
        'Caliper smoke-test endpoint: returns a single fortune string. Real measurement endpoints (discovery audit, repo triage, domain intel) ship after this clears.',
    },
  })
)
```

`/health` is what uptime monitors probe, and uptime is not a vanity metric here
— the ecosystem's audit services score endpoints on 7-day uptime and P99
latency, and those scores are how a buying agent decides whether to trust you.

`/.well-known/x402.json` is the more interesting one. It's the discovery
document: a free, unauthenticated description of what this service sells and
what it costs. This is what gets an endpoint indexed into the x402 Bazaar and
onto marketplaces, and it's the thing three quarters of the services already
listed either don't serve or serve incorrectly. It costs nothing to get right,
and getting it wrong makes you invisible.

Both routes are free and both live on the same Worker as the paid ones. There's
no reason to split them out, and splitting them out means two deploys to keep in
sync.

### Paywalling a route

This is the part that isn't obvious from the documentation:

<p class="code-source"><a href="/projects/caliper/code/src/index.ts#L-48">src/index.ts:48</a></p>

```typescript
// The x402 resource server is stateful (fetches facilitator capabilities on
// first use), so build it once per isolate, not per request.
let cachedMiddleware: ReturnType<typeof paymentMiddleware> | undefined
function paidRouteMiddleware(env: Env) {
  if (cachedMiddleware) return cachedMiddleware
  const facilitator = new HTTPFacilitatorClient({ url: env.CDP_FACILITATOR_URL })
  const server = new x402ResourceServer(facilitator).register(
    'eip155:8453',
    new ExactEvmScheme()
  )
  cachedMiddleware = paymentMiddleware(
    {
      'GET /v1/fortune': {
        accepts: {
          scheme: 'exact',
          network: 'eip155:8453',
          price: '$0.05',
          payTo: env.SERVER_PAY_TO_ADDRESS,
        },
        description: 'A single fortune-cookie aphorism.',
      },
    },
    server
  )
  return cachedMiddleware
}
```

Three things are happening.

`HTTPFacilitatorClient` is the connection to Coinbase's settlement service.
`x402ResourceServer` registers which payment schemes this server accepts —
here, exactly one: the `exact` scheme on `eip155:8453`, which is CAIP-2 notation
for Base mainnet. That pairing is what determines the asset; USDC and its six
decimals are derived from the scheme and network rather than configured
separately.

Then `paymentMiddleware` maps routes to prices. The route key is `"GET
/v1/fortune"` — verb and path, not a bare path — and the config declares what
payment it will accept and where it goes.

**The caching is the important bit.** `x402ResourceServer` is stateful: on first
use it fetches the facilitator's capabilities over the network. Build it inside
the request handler and you've added a facilitator round-trip to every single
call, which will quietly destroy the P99 latency you're being scored on. Build
it once per isolate and hold it. Cloudflare keeps an isolate warm across many
requests, so this amortizes to nothing.

### The handler

<p class="code-source"><a href="/projects/caliper/code/src/index.ts#L-75">src/index.ts:75</a></p>

```typescript
app.use('/v1/fortune', (c, next) => paidRouteMiddleware(c.env)(c, next))

app.get('/v1/fortune', (c) => {
  const idx = Math.floor(Math.random() * FORTUNES.length)
  return c.json({
    fortune: FORTUNES[idx],
    served_at: new Date().toISOString(),
  })
})

export default app
```

The `app.use` line is the paywall. Everything below it runs *only* after a
payment has settled — the handler has no idea payment exists, no branch on
whether the caller paid, no receipt to verify. That separation is the whole
appeal of doing this as middleware.

The handler itself returns a fortune cookie, which deserves an explanation.

It's a deliberate smoke test. It has zero external dependencies: no LLM call, no
upstream API, nothing that can fail for a reason unrelated to payments. If a
paid call clears end-to-end against a hardcoded array of aphorisms, then the
wallet, the middleware, the facilitator, settlement, the deploy pipeline, and
Bazaar indexing are all verified simultaneously. Debugging a payment protocol
and a product at the same time is how you end up unable to tell which one is
broken.

Once it clears, the fortunes get deleted and the real endpoints take the same
slot. Nothing else in the file changes.

### Errors are JSON, always

<p class="code-source"><a href="/projects/caliper/code/src/index.ts#L-26">src/index.ts:26</a></p>

```typescript
app.onError((err, c) => {
  console.error('unhandled', err)
  return c.json({ error: 'internal_error' }, 500)
})

app.notFound((c) => c.json({ error: 'not_found' }, 404))
```

Six lines, and they matter more than they look. The buyer here is a program.
An HTML error page — the default for most frameworks — is an unparseable
failure to it, indistinguishable from the service being down. An audit of the
services already on this marketplace found that a majority don't return valid
JSON at their root.

There's also a harder problem hiding in that `500`: x402 has no built-in refund
flow. If payment settles and then the handler throws, the caller has paid for
nothing. The rule I operate on is that an endpoint whose error rate crosses 10%
comes down immediately and gets refunded by hand from the ledger, rather than
being left up while I debug it.

## Wallet custody

The Worker needs an address to be paid at. That address comes from a Coinbase
Developer Platform server wallet, derived once:

<p class="code-source"><a href="/projects/caliper/code/scripts/init-wallet.ts#L-11">scripts/init-wallet.ts:11</a></p>

```typescript
const apiKey = JSON.parse(readFileSync('./cdp_api_key_receive.json', 'utf8'))
const walletSecret = readFileSync('./cdp_wallet_secret.txt', 'utf8').trim()

const cdp = new CdpClient({
  apiKeyId: apiKey.id ?? apiKey.name,
  apiKeySecret: apiKey.secret ?? apiKey.privateKey,
  walletSecret,
})

const account = await cdp.evm.getOrCreateAccount({ name: 'bazaar-server' })

console.log('address:', account.address)
```

The account is deterministic per `name`, so re-running this returns the same
address rather than creating a second wallet — safe to call repeatedly, which
matters when it's the first thing you reach for after any credential change.

The `??` fallbacks on the API key fields are real-world scar tissue: the field
names in CDP's key JSON changed across SDK versions, from `name`/`privateKey`
to `id`/`secret`, and files generated by the portal at different times have
different shapes.

Custody here is a deliberate reversal. The documented path uses Coinbase's
`awal` CLI, which holds the key in a hardware enclave — a genuinely better
security property, since your own code can't exfiltrate it. It also doesn't run
on Windows, for three independent reasons I documented at length in the repo.
Twenty lines of SDK replaced the entire CLI, work headlessly, and — unlike the
CLI — can run inside a Worker if the service ever needs to pay *other* x402
endpoints.

## The buyer's side

To prove the paywall works you have to actually buy something, which means
writing a client:

<p class="code-source"><a href="/projects/caliper/code/scripts/smoke-test.ts#L-46">scripts/smoke-test.ts:46</a></p>

```typescript
const paidFetch = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [
    {
      network: 'eip155:8453',
      client: new ExactEvmScheme(account as any),
    },
  ],
})

const url = new URL('/v1/fortune', baseUrl).toString()
const res = await paidFetch(url)
console.log('status:', res.status)
console.log(await res.json())
```

`wrapFetchWithPaymentFromConfig` returns a drop-in replacement for `fetch` that
handles the entire handshake: it makes the request, catches the `402`, reads the
terms, signs a payment with the registered scheme, and retries — all
transparently. The calling code is an ordinary `fetch` that happens to cost
money.

The signer is the same CDP account from the previous section, which is why the
smoke test costs essentially nothing: I'm paying myself, so the only real
expense is the facilitator fee and Base gas, both fractions of a cent.

Worth noticing how small this is. Any agent framework that can be handed a
custom `fetch` can buy from an x402 endpoint with no other integration work.
That's the property the whole protocol is betting on.

## Deploy configuration

<p class="code-source"><a href="/projects/caliper/code/wrangler.toml">wrangler.toml</a></p>

```toml
name = "caliper"
main = "src/index.ts"
compatibility_date = "2026-05-01"

# We're shipping the smoke test on the free *.workers.dev subdomain. Once a
# paid call clears end-to-end and we move past fortune-cookie, register a real
# domain (NameSilo, Step 2 of docs/x402-builders-guide.md) and uncomment:
#
# routes = [
#   { pattern = "api.YOUR-DOMAIN.com/*", zone_name = "YOUR-DOMAIN.com" }
# ]
```

That's the whole deploy config. No build step, no bundler configuration, no
container. `wrangler deploy` pushes `src/index.ts` to Cloudflare's edge and
returns a URL.

Secrets are set out-of-band with `wrangler secret put` and never live in the
repo. The custom-domain block stays commented out on purpose — a `workers.dev`
subdomain is free and works, and buying a domain before an endpoint has earned
a single real payment is spending money to look legitimate rather than to be
legitimate.

## Operating state and kill-switches

This one isn't in the template. It's an operational file from the working
repo, reproduced here because the reasoning behind it is the transferable
part — the shape matters more than the file:

```json
{
  "version": 1,
  "project_name": "Caliper",
  "started_at": "2026-05-08",
  "starting_balance_usdc": null,
  "endpoints": [
    {
      "path": "/v1/fortune",
      "price_usdc": 0.05,
      "compute_cost_estimate_usdc": 0.0001,
      "deployed_at": null,
      "status": "scaffolded"
    }
  ],
  "ledger": [],
  "kill_switches": {
    "max_monthly_compute_spend_usdc": 30.0,
    "min_wallet_balance_usdc": 20.0,
    "max_consecutive_failures_per_endpoint": 5
  },
  "incidents": []
}
```

This is the reason I'd call the project finished-in-shape even though it's
barely started. It's the ledger and the brake.

`endpoints` tracks what's deployed, at what price, against what the compute
actually costs. `ledger` accumulates paid calls. `kill_switches` are hard
limits, and they were written **before** the first deploy rather than after the
first surprise:

- **`min_wallet_balance_usdc`** — below $20, no new deploys. Prevents slowly
  spending the float on experiments.
- **`max_monthly_compute_spend_usdc`** — a $30 ceiling. When endpoints start
  making LLM calls, this is what stops a loop from running up a bill.
- **`max_consecutive_failures_per_endpoint`** — five in a row and the endpoint
  comes down. A route that fails repeatedly while still taking payment is worse
  than a route that's offline.

Alongside those, three rules that aren't runtime checks but design constraints:

- **Compute must stay under 25% of price.** If an endpoint can't clear that
  margin at a price the market bears, it doesn't get built. This kills ideas at
  the whiteboard instead of after they're live.
- **Per-payer daily caps.** The specific attack in this ecosystem isn't free
  abuse — it's flooding an endpoint with *real* payments to inflate its apparent
  volume, then pointing at the numbers as evidence of wash trading. In a market
  where reputation is the product, that's cheap to do and expensive to be hit by.
- **No autonomous outflows.** The wallet receives. It doesn't spend, trade, or
  move funds without explicit per-instance confirmation. An enclave protects
  against key theft; it does nothing about *authorized* mistakes.

## How it got built

The sequence was deliberate, and the ordering is the part I'd repeat.

**Research before code.** The first artifact wasn't the Worker, it was a
runbook and a market analysis — what the ecosystem actually looks like, with
sources and dates on every number. That analysis is what ruled out the obvious
ideas. General inference, crypto prices, stock data, web search, on-chain RPC:
all already occupied by Anthropic, CoinGecko, Bloomberg, Firecrawl, and
Alchemy. Building any of them means competing on price against a company with
lower marginal costs and a name the buying agent recognizes.

What the same analysis turned up was stranger and more useful. Across the ~70
services listed in May 2026, the average quality score was 34 out of 100, with
roughly three quarters missing discovery files or failing to return valid JSON.
**The marketplace isn't short on ideas. It's short on services that work.** So
Caliper's real endpoints aim there: a discovery-file auditor for other x402
builders, and synthesis endpoints that fuse several free upstream calls into one
structured answer.

**Scaffold, then wallet, then deploy — in that order.** The wallet script can't
run before `npm install` puts the SDK on disk, which sounds obvious and is a
trap the documentation walks you into by covering wallet setup first.

**A worthless endpoint first.** The fortune cookie, for the reasons above.

**Kill-switches before traffic.** `memory.json` existed before the first
deploy.

The two real detours are both documented in the repo rather than smoothed over.
One was `awal` on Windows: three separate portability bugs, each hidden behind
the last, all patchable and none of the patches surviving a reinstall. The
lesson I'd actually keep is that when a tool fights you three times on the same
axis, check whether it's on the critical path before fixing it a fourth time —
I fixed two bugs on the way to discovering I didn't need the tool.

The other was an SDK migration. The x402 libraries moved to a new namespace and
changed shape; a parallel set of similarly-named packages exists one major
version behind; and every tutorial online is written against a signature that no
longer exists. Middleware arguments, route key format, and the network
identifier all changed. The fix wasn't clever, it was writing the migration down
in the repo so the next person through — very likely me — doesn't re-derive it
from npm archaeology.

## Where it stands

Deployed and serving. The health check is green, the discovery document is live,
and the paid route returns a correct `402` with payment terms.

The end-to-end smoke test — paying my own endpoint and watching a nickel settle
— is the next step, and it's the one that flips this from *deployed* to *live*,
since the Bazaar only indexes an endpoint after it has processed a real payment.

After that the fortune cookie comes out and three endpoints go in: a discovery-file
auditor, repo triage, and domain intelligence. All three sit in that
"short on services that work" gap rather than competing with incumbents.

The scaffold is public as
[x402-worker-template](https://github.com/kylebneary/x402-worker-template) — the
Worker, both scripts, and the deploy config, stripped of anything specific to
Caliper. It's the fastest path I know from nothing to a working paid endpoint.
The builder's guide written alongside it — the runbook, the market analysis
with sources, and an appendix documenting all three Windows bugs — is still in
the private working repo.

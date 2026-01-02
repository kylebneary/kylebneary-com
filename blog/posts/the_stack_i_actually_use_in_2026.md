---
title: The Stack I Actually Use (and Why)
author: Kyle Neary
summary: A living snapshot of the tools I use today, why I use them, and when I wouldn't recommend them.
publication_date: 2026-01-01
---

# The Stack I Actually Use (and Why)

Over the last decade, I’ve built and led data science and analytics systems across manufacturing, retail, finance, and hospitality. Along the way, I’ve tried *a lot* of tools — some excellent, many forgettable.

This page is a living snapshot of the tools I **actually use today**, why I use them, and when I *wouldn’t* recommend them.

> **Disclosure:** Some links on this page are affiliate links. That means I may earn a commission at no additional cost to you. I only include tools I genuinely use or would confidently recommend to peers.

---

## How to read this page

- This is **not** a “best tools” list  
- These are tools that fit *my* workflows  
- I call out when a tool is *not* a good fit  
- I update this page periodically as my stack evolves  

---

## Data & Analytics Stack

### Data Warehouse

#### Snowflake

My default choice for modern analytics workloads.

**Why I use it**
- Separation of storage and compute
- Strong ecosystem (dbt, BI tools, governance)
- Scales cleanly from small teams to enterprise

**When I wouldn’t use it**
- Very small projects with tight budgets
- Simple applications that don’t need analytical workloads

👉 [Learn more about Snowflake](https://www.snowflake.com/)  

---

#### BigQuery

A close second, especially when already operating deeply in GCP.

**Why I like it**
- Virtually zero operational overhead
- Excellent performance for large scans
- Natural fit for event-heavy pipelines

**Tradeoffs**
- Cost predictability can surprise teams
- SQL dialect differences require adjustment

👉 [BigQuery tools and integrations I use](https://cloud.google.com/bigquery)

---

### Transformation & Modeling

#### dbt (Core / Cloud)

If I had to pick one “must-have” tool for analytics teams, this would be it.

**Why it’s foundational**
- Enforces analytics engineering best practices
- Version-controlled transformations
- Documentation becomes a first-class artifact

**Core vs Cloud**
- **dbt Core**: great for small teams and tight budgets  
- **dbt Cloud**: worth it when collaboration, scheduling, and lineage matter  

👉 [dbt Cloud details](https://www.getdbt.com/product/dbt-cloud)

---

### BI & Analytics

I gravitate toward SQL-first tools that emphasize reproducibility and clarity.

**What I look for**
- SQL-native workflows
- Versioning support
- Narrative + analysis in the same space

I intentionally avoid platforms that:
- Hide logic behind drag-and-drop abstractions
- Make it difficult to audit or reproduce results

👉 [Hex analytics platform](https://hex.tech/)

---

### Data Quality & Observability

Data issues are often silent, and trust is fragile.

For smaller teams:
- dbt tests
- Freshness checks
- Lightweight alerting go a long way

For more mature stacks:
- Dedicated observability tools become essential

👉 [Monte Carlo data observability](https://www.montecarlodata.com/)

---

## Python & Machine Learning Tooling

### Core Stack

- Python
- pandas
- numpy
- scikit-learn
- PyTorch (when the problem justifies it)
- xgboost / lightgbm

My bias is simple:

> Simple models in production beat complex models in notebooks.

---

### Experimentation

- JupyterLab for exploration
- VS Code for everything else
- GitHub for version control

I try to move deliberately from:
**notebook → script → pipeline**

---

### Productionization

- dbt for feature logic where possible
- Scheduled jobs for batch ML
- Explicit monitoring over “set and forget”

---

## IDEs & AI-Assisted Development

### My primary IDE

**Visual Studio Code**

This is where the majority of my coding happens.

**Why it works for me**
- Lightweight and fast
- Excellent Python, SQL, and Markdown support
- Strong extension ecosystem
- Easy to pair notebooks with production code

---

### AI-enabled development (how I actually use it)

AI is a meaningful part of my workflow — but not as an “auto-build my app” button.

I use AI as:
- A **thinking partner**
- A **rapid prototyping accelerator**
- A **translation layer** between intent and first-draft code

Not as:
- An autonomous engineer
- A replacement for system design
- A substitute for understanding tradeoffs

---

### AI tools I actively use

#### ChatGPT

This is my primary AI environment for development work.

**Where it’s most valuable**
- Architecture and system design discussions
- Tradeoff exploration
- Refactoring strategies
- Walking through unfamiliar codebases line by line

I often treat ChatGPT as a long-form design notebook — a place to reason *before* touching the IDE.

👉 [ChatGPT](https://chatgpt.com/)

---

#### Gemini

I use Gemini as a complementary model, especially when:
- Working closer to GCP tooling
- Seeking a second perspective
- Sanity-checking edge cases

Using multiple models helps avoid single-model blind spots.

👉 [Gemini](https://gemini.google.com/)

---

### IDE-native and agent-style tools (testing)

I’m actively experimenting with:
- **Cursor**
- **Antigravity**
- **Claude Code**

These tools blur the line between editor, assistant, and agent.

Early impressions:
- Promising for scaffolding and refactors
- Useful for rapid iteration
- Still require strong human oversight

I’m intentionally keeping these in *testing mode*. More detailed thoughts will come in a dedicated post once I’ve spent more time with them.

---

### Guardrails I keep

Regardless of the tool:
- I don’t accept code I couldn’t explain to a teammate
- I treat AI-generated code as **untrusted input**
- I review diffs, not suggestions
- I still write tests intentionally
- I optimize for clarity over cleverness

---

## Infrastructure & Deployment

### Hosting

These are my go-to platforms for side projects and lightweight production systems.

**DigitalOcean**
- Simple, predictable pricing
- Great for small teams and solo builders

👉 [DigitalOcean hosting](https://www.digitalocean.com/)

---

**Railway**
- Excellent developer experience
- Very fast iteration for app backends

👉 [Railway platform](https://railway.app/)

---

**Fly.io**
- Powerful, globally distributed apps
- Slightly steeper learning curve

👉 [Fly.io](https://fly.io/)

---

### CI/CD

- GitHub Actions
- Simple pipelines > clever pipelines

---

## Writing, Thinking, and Planning

### Notes & Documentation

**Obsidian / Notion**

What matters most to me:
- Fast capture
- Searchability
- Markdown support

Tool choice matters less than consistency.

👉 [Notion workspace](https://www.notion.so/)

---

### Project Management

**Linear / GitHub Issues**

I prefer:
- Clear ownership
- Fewer tickets
- Short feedback loops

---

## Personal Finance & Side Projects

This may seem orthogonal, but it’s not.

If you’re building side projects, freelancing, or experimenting, **financial clarity reduces cognitive load**.

---

### Budgeting & Tracking

#### Monarch Money

My current preference for personal finance tracking.

**Why**
- Clean interface
- Multi-account aggregation
- Flexible categorization
- Low friction

👉 [Monarch Money](https://www.monarchmoney.com/)

---

#### YNAB

A strong alternative with a more opinionated approach.

- Excellent for hands-on budgeting
- Higher effort, higher control

👉 [YNAB comparison](https://www.ynab.com/)

---

## What I deliberately don’t use

- “All-in-one AI tools” that do everything poorly
- Tools that hide logic behind GUIs
- Platforms that lock data into proprietary formats
- Anything that requires heroics to maintain

---

## How this stack evolves

This page changes as:
- Teams grow or shrink
- Cost sensitivity changes
- Tooling matures
- My own priorities shift

If you’re building something similar and want a second opinion, explore the deeper dives linked throughout this site — or reach out directly.

---

*Last updated: 2026*

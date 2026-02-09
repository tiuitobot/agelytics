# How We Built Agelytics: A Development Pattern for Human-AI Pairs

**A meta-template for building domain-specific tools through conversational development.**

*Documented on 2026-02-09, after completing the Agelytics project in a single day.*

---

## Context

Agelytics was built in one day (~10 hours of active work) by a human-AI pair: Bruno (domain expert, AoE2 player, economist) and Tiuito (AI agent running on OpenClaw with persistent memory). The result: a 1,600+ line Python framework, a 4-layer knowledge system, full documentation, and a published GitHub repo.

This document captures the **development pattern** that made this possible — not the technical architecture (see `ARCHITECTURE.md` and `DOMAIN_KNOWLEDGE_TEMPLATE.md` for that), but the **process** of how a human and an AI can build something together.

---

## The Pattern: 9 Steps

### Step 1: Start with a Real Itch

**What happened:** Bruno played 7 AoE2 matches and wanted to understand his performance beyond just "I won" or "I lost".

**Principle:** Don't start with "let's build a tool." Start with a problem the human actually has, right now, today. The motivation to test and iterate is built-in because the human cares about the result.

**Anti-pattern:** "Let's build a platform for X" without a concrete use case.

---

### Step 2: MVP in Hours, Not Days

**What happened:** Parser + DB + CLI report working in ~2 hours. First 144 replays ingested. Bruno could see match reports immediately.

**Principle:** Ship the smallest useful thing as fast as possible. "Useful" means the human gets value — even if it's ugly, incomplete, or hardcoded. The AI handles the boilerplate; the human validates the output.

**Key enabler:** AI generates 80% of the code. Human provides domain knowledge ("this field means X", "the duration is in milliseconds not seconds"). Neither could do it alone at this speed.

**Anti-pattern:** Spending 3 hours on architecture before writing a single parser line.

---

### Step 3: Real User, Real Feedback Loop

**What happened:** Bruno played matches → looked at reports → found bugs → reported them in conversation → AI fixed in minutes → new report generated.

Specific feedback that shaped the product:
- "TC idle time of 60% can't be right" → discovered multi-TC calculation bug
- "Age-up time 7:50 vs 10:02 — which is it?" → discovered Research click vs uptime arrival confusion
- "eAPM of 577 is obviously wrong" → discovered drop-game outlier inflation

**Principle:** The fastest feedback loop possible. No tickets, no PRs, no staging environment. Say what's wrong → it's fixed → test again. The conversation IS the issue tracker.

**Key enabler:** AI can fix, test, commit, and push in one conversational turn. The human never waits.

**Anti-pattern:** Building in isolation for weeks before showing anyone.

---

### Step 4: Features Emerge from Usage, Not Planning

**What happened:** 
- Bruno clicked "Análise IA" → realized it was too shallow → Deep Coach was born
- Bruno asked "can you find something I DON'T already know?" → forensic analysis with action log mining
- Bruno played 7 matches in a day → day menu and daily AI summary became necessary
- Eva (8-year-old daughter) wanted to interact → voice storytelling feature confirmed TTS pipeline value

**Principle:** Build what's needed when it's needed. The human's behavior reveals requirements better than any planning document. 

**How it works in practice:** Human uses the tool → hits a wall or has an idea → says it out loud → AI implements it → human tests it → repeat.

**Anti-pattern:** Writing a 50-page PRD before building anything.

---

### Step 5: Separation Emerges Organically

**What happened:** At some point Bruno said: "This is actually 2 projects in 1 — a deterministic framework anyone can use, and an AI layer specific to our setup."

This wasn't planned. It emerged from:
- Wanting to share the tool with Lucas (friend, AoE2 player)
- Realizing Lucas doesn't have OpenClaw
- Noticing personal data was mixed with generic code

**Principle:** Don't force architecture upfront. Let the structure emerge from real constraints ("I want to share this but can't because my data is mixed in"). The right separation reveals itself through usage.

**Key enabler:** AI can restructure a codebase in minutes (move files, update imports, fix references, update crontab, test, commit). Refactoring cost ≈ 0.

**Anti-pattern:** Over-engineering separation from day one, before knowing what needs to be separated.

---

### Step 6: Knowledge Base Emerges from Data

**What happened:** Pattern detection ran on 144 matches → auto-promotion found 23 updates needed → 13 civilizations were missing from the KB → 6 new matchups were discovered.

**Principle:** "Start with patterns, not the KB." The data tells you what knowledge is needed. Don't build a comprehensive knowledge base before having data to validate it against.

**Sequence that works:**
1. Collect data (matches, events, records)
2. Run aggregate queries (what patterns exist?)
3. Patterns reveal gaps (what knowledge is missing?)
4. Fill gaps with curated knowledge
5. Auto-promote new patterns to KB

**Sequence that doesn't work:**
1. Build comprehensive KB
2. Hope data eventually uses it
3. Discover KB was wrong/incomplete
4. Rebuild

**Anti-pattern:** "First, let's document every AoE2 civilization" before having a single match parsed.

---

### Step 7: Automate Incrementally

**What happened:**
- Day 1, morning: Manual CLI commands (`agelytics ingest`, `agelytics report`)
- Day 1, afternoon: Watcher script detecting new replays
- Day 1, evening: Linux cron running every 2 minutes, Telegram notifications with inline buttons
- Day 1, night: Full pipeline: new match → parse → DB → patterns → player profile → KB auto-promote → notification

**Principle:** Automate after you understand the workflow, not before. Each automation step was motivated by friction ("I don't want to run `ingest` manually every time").

**Key insight:** Bruno explicitly said "the watcher should be pure Linux cron, no AI." Deterministic operations should be deterministic. AI enters only where judgment is needed.

**Anti-pattern:** Building the automation framework before the thing you're automating works.

---

### Step 8: Document Together, Not After

**What happened:** Documentation evolved alongside code:
- `plans/v1-architecture.md` created BEFORE coding
- `documentation/agelytics.md` updated after each feature
- `README.md` rewritten when repo structure changed
- `ARCHITECTURE.md` and `CHANGELOG.md` added with Phase 2
- `DOMAIN_KNOWLEDGE_TEMPLATE.md` added as Phase 5

**Principle:** Documentation is part of the deliverable, not a chore after. The AI generates docs naturally as part of the development flow — it's zero extra effort for the human.

**Key enabler:** AI has full context of what was built and why. It writes accurate docs because it was there for every decision.

**Anti-pattern:** "We'll document it later" (spoiler: you won't).

---

### Step 9: Generalize at the End

**What happened:** After completing all features, we noticed the 4-layer pattern (Data → Patterns → KB → AI) was domain-agnostic. Created `DOMAIN_KNOWLEDGE_TEMPLATE.md` with examples for Cooking, Finance, Chess.

Then Bruno noticed the DEVELOPMENT PROCESS itself was a pattern worth capturing → this document.

**Principle:** Abstraction comes from experience, not speculation. You can only write a good template after building the concrete thing. The template captures decisions that were MADE, not decisions that were PLANNED.

**Anti-pattern:** Writing the framework before building the first application.

---

## Roles in the Pair

### Human Provides:
- **Domain expertise** ("Mangudai counters Knights", "TC idle of 60% is impossible")
- **Quality judgment** ("this analysis is too shallow", "that's not an insight I didn't know")
- **Strategic direction** ("this should be two projects", "make it a skill")
- **Real-world testing** (actually playing games, clicking buttons, breaking things)
- **Taste** ("the voice should sound like X", "the report needs TC idle time")

### AI Provides:
- **Implementation speed** (parser, DB, reports, patterns — all in hours)
- **Breadth of knowledge** (Python, SQLite, mgz library, Telegram API, TTS, PDF generation)
- **Refactoring at zero cost** (restructure entire repo in minutes)
- **Documentation as byproduct** (writing docs from full context)
- **Pattern recognition across domains** (noticing the 4-layer architecture is generalizable)
- **Memory continuity** (remembering every decision, every bug, every preference across the session)

### Neither Can Do Alone:
- Human without AI: Would take weeks, not hours. Would skip documentation. Would not refactor.
- AI without human: Would build something technically correct but useless. No domain expertise. No taste. No real-world testing.

---

## Metrics

### What we built in ~10 hours:
- **1,600+ lines of Python** (parser, DB, report, patterns, watcher, deep coach, CLI)
- **4-layer knowledge system** (data → patterns → KB → AI analysis)
- **Knowledge base** with 10 civs, 15 matchups, benchmarks by ELO, 16 coaching rules
- **Full automation** (Linux cron → parse → patterns → KB update → Telegram notification)
- **Professional documentation** (README, Architecture, Changelog, Template, this document)
- **Published GitHub repo** (public, MIT license)
- **Working Telegram integration** with inline buttons and 3 analysis tiers

### What made it possible:
- Real problem with real user
- Conversational development (no overhead)
- AI handles boilerplate, human handles judgment
- Zero-cost refactoring
- Persistent memory (no context loss between steps)

---

## When This Pattern Works

✅ **Domain-specific tools** — where one person is both developer and user
✅ **Data-driven projects** — where you have structured data to analyze
✅ **Rapid prototyping** — when speed-to-value matters more than perfection
✅ **Solo/small team** — where communication overhead is the bottleneck
✅ **Learning projects** — where the goal is understanding, not just output

## When It Doesn't Work

❌ **Large team coordination** — this pattern is optimized for 1 human + 1 AI
❌ **Safety-critical systems** — the speed comes at the cost of formal verification
❌ **No domain expert available** — the human's expertise is non-negotiable
❌ **No feedback loop** — if you can't test quickly, the speed advantage disappears

---

## Reproducing This Pattern

1. **Find your itch.** What problem do you actually have today?
2. **Start a conversation.** Tell the AI what you want, not how to build it.
3. **Get to "useful" in under 2 hours.** If it takes longer, you're over-engineering.
4. **Use it yourself.** The bugs will find you.
5. **Say what's wrong out loud.** The AI fixes it. Repeat.
6. **Notice when structure wants to emerge.** Don't force it; let it reveal itself.
7. **Automate the friction.** Whatever you do manually more than twice → automate.
8. **Document as you go.** The AI has full context — let it write the docs.
9. **Generalize only after you've built the concrete thing.**

---

*"The best architecture is the one that emerges from solving a real problem, not the one designed in advance."*

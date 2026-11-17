# Five-stage CTI workflow — source interpretation

Reference: Flare presentation at Antisyphon Training, “The CTI workflow, stage by stage” (user-provided screenshot).

| Stage | Description on slide | AI involvement shown |
|---|---|---|
| 1. Gathering sources | Forums, Telegram, leak sites, stealer logs, blogs | `01: PARTLY` |
| 2. Reading and triage | Help me figure out what to read | `02: YES` |
| 3. Enrichment | Pulling out IOCs, deduping | Human work after AI steps out |
| 4. Analysis and attribution | Stays with the analyst | Human work |
| 5. Writing it up | The report, the alert, the brief | Human work |

The slide says “AI TAKES A STEP OUT HERE” after Stage 2. **Do not infer that the slide endorses AI-generated enrichment, attribution, or final reports.** Conventional automation may assist later tasks, but analytical judgments and publication remain human-led unless explicitly reconsidered by the project owner.

## Proposed pipeline interpretation (design proposal, not a slide quote)
1. Schedule and fetch permitted sources with independent adapters; AI may help source discovery.
2. Normalize and rank items; optionally use an LLM for relevance summaries with source citations.
3. Offer deterministic IOC parsing, validation, deduplication, and enrichment tools for analyst verification.
4. Analyst examines evidence, campaign relationships, confidence, and Ghana-specific relevance.
5. Analyst prepares and approves report using a structured Markdown template; only approved TLP:CLEAR reports reach the public site.

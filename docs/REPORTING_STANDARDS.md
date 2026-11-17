# Reporting and publication standards

## Template reference
Lenny Zeltser, Cyber Threat Intelligence Report Template: https://zeltser.com/cyber-threat-intel-report-template

**Decision:** start from the downloadable Markdown template as a reference; consider the MCP offering later. Obtain the actual template and review its license/attribution requirements before copying or modifying it. This repository handover does **not** reproduce its contents.

## Intelligence levels
- Tactical: validated indicators, TTPs, detection/hunting guidance.
- Operational: campaign mechanics, observed targeting, timelines, relevant sectors.
- Strategic: evidence-based risks and decision implications; initially secondary.

## Minimum report checks
- Title, scope, executive summary, evidence sources and dates.
- Observed facts separated from analysis, inference, and unknowns.
- Ghana relevance: confirmed local targeting vs plausible exposure explicitly distinguished.
- IOCs with context, timestamps, validation and confidence; no blind blocklists.
- Recommended defensive/hunting actions; limits and caveats.
- TLP 2.0 classification, reviewer approval, publication timestamp and version.

## TLP handling
- `TLP:CLEAR`: publicly shareable, after analyst approval.
- `TLP:GREEN`: community-limited; not public.
- `TLP:AMBER`: limited to recipients' organizations and clients where appropriate; apply TLP 2.0 rules and any restrictions.
- `TLP:AMBER+STRICT`: recipients' organizations only.
- `TLP:RED`: named recipients only.

TLP is a sharing designation, not encryption or access control. Restricted material needs private infrastructure and permission checks. Review FIRST TLP 2.0 official guidance before implementing automated enforcement: https://www.first.org/tlp/

## Reference use case
Microsoft Threat Intelligence, November 16, 2026 report about high-volume phishing exploiting Microsoft 365 outage lures:
https://www.microsoft.com/en-us/security/blog/2026/11/16/high-volume-phishing-campaign-uses-microsoft-365-outage-lures-target-multiple-industry-sectors-2/

Use it to study source-to-intelligence transformation and evidence discipline. It is **not** the platform's domain focus and is **not** proof of Ghanaian targeting.

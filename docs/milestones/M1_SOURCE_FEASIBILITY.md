# M1 source feasibility — checked 2026-11-18

Recorded for M1 v1.0; retained as historical evidence for the
[current collection proposal](M1_COLLECTION.md). No source requests or updated
payload verification occurred in the v1.1/v1.2 reviews or the 2026-11-19 v1.3
revision. These are bounded historical research
observations, not implemented collectors or operational onboarding approval.
Only public documentation, schemas and catalog data were inspected; no article
crawler, scheduled ingestion, database or intelligence publication was created.
No source payload is committed. Recheck mutable endpoints and terms before use.

## Current scope versus historical findings

The current [v1.3 full-text design](M1_EVIDENCE.md) supersedes earlier metadata-first
planning, not the historical verification evidence below. All source tables and
“Proposed scope” rows below record the original research context; they do not
approve current access or describe current v1.3 scope. No endpoints, content or
terms were fetched to prepare v1.3.

**Owner-reported observations, not independent verification:** the owner reports
observing complete Microsoft articles in RSS `content:encoded` and complete Google
Threat Intelligence/Mandiant articles in RSS `description` on **2026-11-18**.
B1 must independently reconfirm namespace/fields, completeness, encoding, sizes,
item counts, status/redirects/cache behavior and applicable access restrictions.
Missing or truncated full-text fields block acceptance; no crawler or metadata-only
fallback is authorized.

**Owner-reported terms/risk position:** Microsoft restrictions on copying,
distribution/publication and possible use limits were reported; applicable Google
terms and robots require review. The owner accepts identified private-research
operational/legal risk, but this is not a legal conclusion, license or exception.
D023/[rights questions and routes](M1_EVIDENCE.md) keep access, full-text retention,
derivation, backups and later publication permissions unresolved. No activation
based solely on technical accessibility or risk acknowledgement.

## Verification method and limits

Official pages were inspected with the web tool; official CISA repository files
were read through the GitHub connector. One-off bounded GET attempts from the
execution environment used a descriptive feasibility user-agent, no source
credentials, a 20-second timeout and an 8 MiB read cap. Those requests failed at
the outbound proxy (CONNECT 403), so they do **not** establish origin failures,
payload sizes, anonymous accessibility or HTTP cache behavior. The CISA website
also returned 403 through the web tool. No restriction was bypassed.

The web tool reports unsupported RSS/XML media types for the vendor feed URLs.
That confirms a feed-shaped response was encountered by that tool, not that a
complete feed was parsed or its status/fields validated. Before activation, an
approved runtime must record status, final URL and redirects, Content-Type,
transferred/decompressed bytes, ETag/Last-Modified, item counts, date/GUID/summary
coverage, parsing results and robots/terms decisions. Do not attach raw vendor
payloads to this public repository; current v1.3 development uses synthetic fixtures only.

## CISA KEV

| Item | Finding |
| --- | --- |
| Authority / entry point | [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) |
| Canonical JSON | [cisa.gov JSON feed](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json); direct access unverified here (403 via web tool, proxy block via shell) |
| Official alternate | [cisagov/kev-data](https://github.com/cisagov/kev-data), default branch `develop`; repository describes a CISA-maintained mirror synchronized shortly after the canonical source |
| Proposed initial transport | [official mirror JSON](https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json); anonymous runtime GET remains to be verified. Do not substitute an unofficial mirror. |
| Machine-readable evidence | Connector blob `0b3a3af601783f1e13f7761358f4188929eeeb21` parsed as JSON: catalog version `2026.11.17`, declared and actual count 1,782; decoded string length 1,856,425 characters (not a wire-byte measurement) |
| Schema | [official JSON schema](https://github.com/cisagov/kev-data/blob/develop/known_exploited_vulnerabilities_schema.json), checked blob `ec422845b354f58250d2e99cdfcce17a18659423`; includes CVE, vendor/product, description, dateAdded, requiredAction and dueDate; optional fields include ransomware use, forensic triage, notes and CWEs |
| Rights | [CC0 license](https://github.com/cisagov/kev-data/blob/develop/LICENSE), checked blob `bd3f969029f08512e9a67348be9d744b2eb81a7a`: database use is permitted; third-party linked material, logos and endorsement are not covered |
| Credentials / limits | Public-file route proposed, no paid API needed. No numeric source request quota established; daily polling is a project cap, not a provider entitlement. Avoid the GitHub REST API as an unnecessary runtime dependency. |
| Readiness | Format and database license verified; runtime transport/robots/cache checks and owner activation approval remain pending |

Use CVE ID as the source-native identity, but keep source namespaces separate.
`dateAdded` is a catalog inclusion date, not vulnerability publication or first
exploitation time. `dateReleased` describes the catalog. Preserve those original
fields/precision; do not invent a publication timestamp or Ghana impact. Keep
federal remediation deadlines labeled as source data, not Ghanaian legal duties.

## Microsoft Security Blog

| Item | Finding |
| --- | --- |
| Authority | [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/) inspected; covers research, threat intelligence and other security topics |
| Candidate feed | [English-language blog RSS](https://www.microsoft.com/en-us/security/blog/feed/) returned an `application/rss+xml` response type to the web tool; body extraction unsupported |
| Proposed scope | Feed-supplied title, original link, GUID, publication date, publisher and permitted summary. No article-page crawl, downloads, comment feed or commercial intelligence API. Exact field coverage still needs verification. |
| Rights | Blog footer links [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use). They limit copying/use and reserve rights; no broad archival or republication grant was established. Owner must document an applicable permission/basis for planned organizational collection and retention before activation. |
| Robots | [robots.txt](https://www.microsoft.com/robots.txt) inspected. The listed `/blog/feed/` rule is a root-path rule, not a blanket match for every nested feed; nevertheless verify the exact endpoint, redirects and chosen user-agent on the target runtime. Robots is not a copyright license. |
| Credentials / limits | No credential prompt observed by web lookup, but anonymous runtime GET and any numerical rate limit remain unverified. No paid integration proposed. |
| Readiness | Candidate endpoint identified; payload parsing and collection/retention rights are unresolved; disabled until cleared |

The following **historical v1.0 normalization guidance is superseded** by the
full-text target and permission gates above; it is preserved only for traceability:

> Do not assume the feed is threat-intelligence-only, a complete archive, or a full
> article source. Retain supplied category metadata if present without treating it
> as a Ghana relevance score. If summaries are absent or their retention is not
> permitted, require an approved metadata-only contract or defer this adapter;
> do not fabricate the nonempty `SourceItem.excerpt` required by V1.

## Google Threat Intelligence / Mandiant

| Item | Finding |
| --- | --- |
| Authority | [Google Cloud Threat Intelligence](https://cloud.google.com/blog/topics/threat-intelligence) inspected; identifies Mandiant investigations and Google threat research |
| Official feed discovery | The page's RSS link resolves to [FeedBurner threat-intelligence feed](https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v), which returned a `text/xml` response type to the web tool; body extraction unsupported |
| Proposed scope | One source adapter for this public research feed, preserving the entry's publisher/byline where supplied. No paid Google Threat Intelligence API, VirusTotal API or authenticated Mandiant portal. |
| Rights | Footer links [Google Terms](https://policies.google.com/terms?hl=en-US): intellectual property and machine-readable access instructions remain applicable. No blanket license for blog archiving/republication was established; applicable regional/service-specific terms and collection/retention basis need review. |
| Robots / redirects | [cloud.google.com robots](https://cloud.google.com/robots.txt) inspected; FeedBurner's robots response was unavailable to the tool. Verify FeedBurner and every redirect host; a feed link is not permission for general crawling. |
| Credentials / limits | No credential prompt observed in web lookup; anonymous runtime GET, feed fields, cache validators and numeric quotas remain unverified. No paid API dependency. |
| Readiness | Publisher-endorsed RSS endpoint identified; payload/rights/runtime gates remain open |

Retain the configured feed URL, actual final transport URL and original article
URL separately. FeedBurner may expose tracking/original-link fields; their actual
presence is unverified. Treat links as references, never automatically fetch
them. Do not infer authorship or a new independent source merely from rebranding.

## Go/no-go summary

- **Technically strongest candidate:** CISA, because actual catalog/schema data
  and database licensing were inspected. Endpoint reachability still needs proof
  on the selected host.
- **Conditional candidates:** both vendor RSS feeds. Their official contexts and
  feed response types support feasibility, but payload and rights checks are open.
- Before live activation of each candidate: record the approved endpoint/host
  allowlist, rights/retention basis, robots result, field mapping, bounded fetch
  result, failure/retry policy and operator sign-off. Unknown quotas mean cautious
  polling and honoring provider responses, never unlimited access.
- If a candidate fails, pause it and request a scope revision. Do not silently
  substitute sources, scrape full articles, buy access or call the three-source
  milestone complete with only one working source.
- These global sources support Ghanaian defenders but provide no inherent proof
  of Ghana targeting. Ghana CSA/CERT-GH and sector coverage remain separate
  onboarding work in the [source register](../INTELLIGENCE_SOURCES.md).

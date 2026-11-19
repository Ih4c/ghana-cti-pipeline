# Candidate intelligence sources — research backlog

These are candidate sources, **none integrated or enabled**. Bounded checks of
the three M1 candidates are recorded in the dated [source feasibility document](milestones/M1_SOURCE_FEASIBILITY.md);
it distinguishes verified facts from unresolved access and rights. The remaining
backlog has not been individually verified. Prefer official feeds/APIs/RSS where
permitted; no source listing grants collection or redistribution permission.

## Ghana priority
- Ghana Cyber Security Authority / CERT-GH: https://www.csa.gov.gh/ — official advisories and Ghana relevance.
- Future sector-specific Ghanaian CERT/regulator publications: verify authority, access, and rights before onboarding.

## Primary research and government
- Microsoft Security Blog: https://www.microsoft.com/en-us/security/blog/
- Google Cloud / Mandiant Threat Intelligence: https://cloud.google.com/blog/topics/threat-intelligence
- CISA Known Exploited Vulnerabilities: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- Cisco Talos: https://blog.talosintelligence.com/
- Palo Alto Unit 42: https://unit42.paloaltonetworks.com/
- CrowdStrike: https://www.crowdstrike.com/en-us/blog/
- ESET Research: https://www.welivesecurity.com/
- UK NCSC: https://www.ncsc.gov.uk/

## Structured indicators / enrichment
- abuse.ch projects: https://abuse.ch/ (ThreatFox, URLhaus, MalwareBazaar)
- VirusTotal: https://www.virustotal.com/ (review API terms and quotas)

## Source onboarding checklist
1. Provenance and trustworthiness assessed.
2. Collection method and ToS/license checked.
3. Rate limits, auth, and budget documented.
4. Stable adapter contract and fixture tests.
5. Coverage, false-positive, and Ghana relevance evaluated.
6. Safe storage and TLP implications considered.

## Initial MVP candidates
The [current M1 proposal](milestones/M1_COLLECTION.md) names CISA KEV, Microsoft
Security Blog, and the official Google Threat Intelligence/Mandiant feed.
Candidate selection is not activation approval: runtime access, rights, retention
and source-specific checks remain gates. Final scope requires owner approval;
if a candidate fails, propose a revision instead of silently substituting it.
Keep Ghana CSA/CERT-GH and sector coverage in the backlog: global source coverage
must not be described as evidence of Ghana-specific targeting.

The owner has accepted full-text direction D022, superseding D018's metadata-first
vendor target: complete permitted CISA entries and full articles supplied in
Microsoft RSS content:encoded / Google RSS description. The vendor fields are
owner-reported observations dated 2026-11-18, pending independent B1 confirmation.
The [source policy/evidence design](milestones/M1_EVIDENCE.md) remains proposed.
Full-text access/retention/derivation/backup rights are unresolved; risk acceptance
and feed availability are not licenses. Block unresolved modes; no metadata-only
substitution, article-page crawler, embedded-link requests, backfill or paid API.
Existing endpoint candidates remain unchanged, with no network checks in this task.

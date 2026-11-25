# M1-06b offline HTML and text transformations

Implemented under M1 v1.3 / D024 for independent review. The
[owner comment on PR #20](https://github.com/Ih4c/ghana-cti-pipeline/pull/20#issuecomment-7149971631)
explicitly approves this pure offline increment, standard-library `html.parser`,
synthetic tests and related documentation. Author/scope were verified before
application changes. PR #20 merged at `64224f1`, verified 2026-11-25. D032 records
concrete choices below; source adapters, integration and operational gates are
not approved. The owner's subsequent task clarification permitted considering
other parsers for security; no dependency change was needed or made.

## Separate APIs and representations

- [html_sanitizer.py](../src/ghana_cti_pipeline/collectors/html_sanitizer.py):
  `sanitize_html(original, *, version="cti-inert-html-v1") -> str`.
- [text_extraction.py](../src/ghana_cti_pipeline/collectors/text_extraction.py):
  `extract_text(sanitized, *, version="cti-plain-text-v1") -> str`.
- [article_transforms.py](../src/ghana_cti_pipeline/collectors/article_transforms.py):
  `transform_articles(originals, *, sanitizer_version, extractor_version)` returns
  a tuple of frozen `TransformedArticle` values with `original`, `sanitized_html`,
  `plain_text`, both implementation versions and the parser profile.
- [html_fragment.py](../src/ghana_cti_pipeline/collectors/html_fragment.py) and
  [html_profile.py](../src/ghana_cti_pipeline/collectors/html_profile.py) provide
  shared strict syntax, bounded buffers, constants and finite safe errors.

Inputs are already-extracted article **strings**, such as M1-06a body values,
never XML responses, URLs, paths, byte streams or arbitrary iterators. No original
is mutated or overwritten. The batch result retains the exact original string,
including original Unicode/line endings. Results suppress payloads in repr.
These are transient helper outputs, not new wire contracts, stored artifacts,
retention assertions, source verification or permission grants.

Only the two exact version identifiers are accepted. The shared parser profile
is `cti-strict-html-fragment-v1`; it is distinct from the XML parser and evidence
schema versions. Future adapters must bind these versions/configuration to the
unchanged M1-02a transformation descriptors and M1-02b derivation identities.
This increment does not generate artifacts, identities or manifests. Existing
original/sanitized/plain-text digest domains remain distinct and unchanged.

## Security model and accepted syntax

`HTMLParser` is a tokenizer, not a browser, HTML5 tree builder or sanitizer by
itself. This implementation uses it with a conservative fragment grammar and
**rebuilds output** from fixed element tokens and escaped character data. It
never serializes source tags/attributes or repairs malformed fragments into output.
Regular expressions check token syntax only; they do not strip or sanitize HTML.

Require balanced, explicitly closed nonvoid tags, ASCII tag/attribute names,
whitespace-separated attributes, quoted or syntactically valid unquoted values,
unique case-insensitive attribute names and complete tokens. Standard void tags
may use a closing slash; nonvoid self-closing syntax, mismatched/omitted closing
tags, malformed comments, declarations, CDATA, processing instructions and
unfinished tokens fail. Literal `<` in ordinary text must be escaped. This is a
strict fragment syntax profile, not validation of every HTML5 content-model rule.
It intentionally rejects browser-recoverable input; source feasibility is not proven.

The raw-text modes are explicitly fixed to script/style across Python 3.11/3.14;
other dropped containers use balanced fragment syntax. `plaintext` rejects because
its end-of-document mode is incompatible with this profile. Dropped content still
faces input/depth/node/syntax limits. No browser, resource resolver or callback is
involved; all links, URLs and embedded instructions remain untrusted data.

Supported named references are semicolon-terminated standard-library HTML5 entity
names; numeric references must be complete decimal/hex Unicode scalars with at
most eight digits. Unknown/incomplete references, NUL, surrogates and disallowed
C0/C1 controls fail instead of silently replacing evidence. TAB/LF/CR are allowed.
Reference decoding happens once during parsing, followed by escaping into HTML.
There is no second unescape pass over sanitized HTML or extracted text.

## Sanitizer policy and deterministic serialization

Emit only these lowercase, attribute-free elements:

`p div br h1 h2 h3 h4 h5 h6 ul ol li blockquote pre code strong em table caption
thead tbody tfoot tr th td`.

The explicit `div` allowance preserves block separation. Unwrap `a` and `span`
while preserving their visible descendants. Drop every other element and its
entire subtree, including scripts/styles, forms/controls, foreign SVG/MathML,
templates, embeds/media and unknown wrappers. Remove nonapproved void elements
such as img/base/link/meta/input. Comments are removed. Declarations/processing
instructions reject rather than attempting recovery. No attribute survives,
including style, event handlers, IDs, namespaces, custom-element bindings or
resource-bearing references. Plain URL-looking text may remain inert text; no
reference is followed or resolved.

Emit canonical `<tag>` / `</tag>` tokens (`<br>` only for the allowed void tag).
Escape all data `&`, `<`, `>` as `&amp;`, `&lt;`, `&gt;`; text quotes do not need
attribute escaping because no attribute context exists. Preserve data whitespace,
line endings and Unicode without normalization. Thus even entity-encoded markup
remains text on reparsing. Output contains no executable or resource-bearing
markup regardless of how a browser might repair its inert structural elements.
Successful sanitization is idempotent under this profile.

Dropping subtrees can remove meaningful source material; it does not claim lossless
article equivalence. Preserve and compare the private original. A result with no
nonblank output fails; an empty structural shell may pass sanitization but fails
text extraction. Batch transformation rejects either failure without fallback.

## Plain-text rules

The extractor accepts only the sanitizer's vocabulary: lowercase exact tokens,
no attributes/comments, and only its canonical amp/lt/gt escapes. Arbitrary or
noncanonical HTML is rejected instead of implicitly sanitized. Parse the sanitized
representation once; output is text, not HTML-safe markup or a publication product.
A later viewer must use its own reviewed text escaping/isolation.

Normalize CRLF and CR to LF in this derivative only. Keep other Unicode and
intra-text whitespace. At block boundaries (`p`, `div`, headings, blockquote,
pre, table, caption, ul, ol), ensure at least two LFs when prior text exists.
List-item/row boundaries ensure one LF. Each br contributes one LF. Adjacent
cells in a row are separated by a TAB, including empty cells. Inline strong/em/code
add no separators. Trim outer LFs only after bounded construction; retain spaces,
TABs and internal newlines. These are deterministic separators, not prose rewriting,
analysis, date inference or a claim that every HTML presentation survives.

## Bounds and failure behavior

All sizes are measured in strict UTF-8 bytes, not Python character counts:

| Boundary | Maximum |
| --- | --- |
| Original, sanitized or plain-text article | 1 MiB each |
| Each representation aggregate in a batch | 6 MiB independently |
| Articles per batch | 500; empty tuple valid and not a retraction |
| Element nesting, including removed elements and void children | 64 |
| Nodes per batch, separately for sanitizer and extractor | 50,000 |
| Input attributes per element / decoded value length | 32 / 4,096 characters |

A node is an opening element, comment or contiguous text run (including adjacent
entity callbacks); closing tags are not nodes. Counts do not depend on character
callback splitting. Batch APIs share each stage's node budget across articles;
single-article helpers use a fresh bounded budget and cannot claim aggregate
validation. D024 node/attribute budgets are now explicit implementation bindings.
Escaping can expand output, so the output writer checks before appending. Any
violation rejects the entire result; no partial yield, truncation or fallback.
Limits apply to intermediate construction too, before final LF trimming.

Functions raise `TransformError` with only finite codes: invalid_input,
input_limit, output_limit, batch_limit, item_limit, invalid_character,
malformed_html, depth_limit, node_limit, attribute_limit, invalid_reference,
not_sanitized, empty_output, unsupported_version. No source snippets, raw exception
messages, payload logs or automatic retry. Caller input remains available after
failure. No filesystem, network, clock, randomness, transport or storage imports.
Future orchestration must own combined source/run deadlines; these pure helpers
claim byte/node/depth bounds, not operational timing or retention enforcement.

## Validation, compatibility and stopping point

[Synthetic regression tests](../tests/test_html_transforms.py) include fixed
HTML/text vectors, malformed/mutation-XSS-style fragments, all attribute removal,
foreign/active subtree removal, nested encoding, Unicode/line endings, empty cells,
exact/one-over byte/depth/node/attribute/batch bounds, immutable original separation,
M1-06a field interoperability, existing digest domains and blocked side effects.
Generated adversarial fragments must either reject or reparse as the inert
attribute-free vocabulary. CI tests Python 3.11 and 3.14; runtime changes must
revalidate the profile rather than silently changing accepted transformations.
This is offline verification, not browser/viewer or live-source certification.

No prior contract, schema, identity profile, public protocol, dependency, CI file
or report template changes. No source adapters, storage integration, CLI,
real publisher content, live requests, deployment, scheduling, publication,
full-text activation or paid services. Existing 2 GiB storage/$0 budget remains.
Lawful basis is still open and blocks real full-text activation. Issue #10 stays
open; B1/B2/C remain unapproved. Stop at independent review. M1-07 CISA adapter
implementation requires separate owner approval.

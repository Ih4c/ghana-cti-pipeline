"""Pure, all-or-nothing article transformations; no evidence/storage integration."""

from dataclasses import dataclass, field

from ghana_cti_pipeline.collectors.html_profile import (
    BATCH_LIMIT,
    EXTRACTOR_VERSION,
    HTML_PARSER_PROFILE,
    SANITIZER_VERSION,
    NodeBudget,
    TransformError,
    article,
)
from ghana_cti_pipeline.collectors.html_sanitizer import _sanitize
from ghana_cti_pipeline.collectors.text_extraction import _extract


@dataclass(frozen=True)
class TransformedArticle:
    original: str = field(repr=False)
    sanitized_html: str = field(repr=False)
    plain_text: str = field(repr=False)
    sanitizer_version: str = SANITIZER_VERSION
    extractor_version: str = EXTRACTOR_VERSION
    parser_profile: str = HTML_PARSER_PROFILE


def transform_articles(
    originals: tuple[str, ...],
    *,
    sanitizer_version: str = SANITIZER_VERSION,
    extractor_version: str = EXTRACTOR_VERSION,
) -> tuple[TransformedArticle, ...]:
    """At most 500 articles; independently bound all three representation aggregates."""
    if (
        type(sanitizer_version) is not str
        or type(extractor_version) is not str
        or sanitizer_version != SANITIZER_VERSION
        or extractor_version != EXTRACTOR_VERSION
    ):
        raise TransformError("unsupported_version")
    if type(originals) is not tuple:
        raise TransformError("invalid_input")
    if len(originals) > 500:
        raise TransformError("item_limit")
    size = 0
    for value in originals:
        size += article(value)
        if size > BATCH_LIMIT:
            raise TransformError("batch_limit")
    sanitized_nodes, plain_nodes = NodeBudget(), NodeBudget()
    sanitized_size, plain_size = 0, 0
    results = []
    for original in originals:
        sanitized = _sanitize(original, sanitized_nodes)
        sanitized_size += len(sanitized.encode("utf-8"))
        if sanitized_size > BATCH_LIMIT:
            raise TransformError("batch_limit")
        plain = _extract(sanitized, plain_nodes)
        plain_size += len(plain.encode("utf-8"))
        if plain_size > BATCH_LIMIT:
            raise TransformError("batch_limit")
        results.append(TransformedArticle(original, sanitized, plain))
    return tuple(results)

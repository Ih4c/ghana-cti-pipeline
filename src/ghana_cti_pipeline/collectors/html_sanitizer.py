"""Rebuild an inert fragment; original strings are never changed or rendered."""

from html import escape

from ghana_cti_pipeline.collectors.html_fragment import FragmentParser
from ghana_cti_pipeline.collectors.html_profile import (
    ALLOWED,
    SANITIZER_VERSION,
    UNWRAP,
    VOID,
    NodeBudget,
    Output,
    TransformError,
    article,
)


class _Sanitizer(FragmentParser):
    def __init__(self, source, nodes):
        super().__init__(source, nodes)
        self.output = Output()
        self.dropped_at: int | None = None

    def open_tag(self, tag):
        if self.dropped_at is not None:
            return
        if tag in ALLOWED:
            self.output.write(f"<{tag}>")
        elif tag not in UNWRAP and tag not in VOID:
            self.dropped_at = len(self.stack)

    def close_tag(self, tag):
        if self.dropped_at is not None:
            if len(self.stack) - 1 == self.dropped_at:
                self.dropped_at = None
        elif tag in ALLOWED:
            self.output.write(f"</{tag}>")

    def text(self, data):
        if self.dropped_at is None:
            self.output.write(escape(data, quote=False))


def _sanitize(original: str, nodes: NodeBudget) -> str:
    article(original)
    parser = _Sanitizer(original, nodes)
    parser.run()
    return parser.output.finish()


def sanitize_html(original: str, *, version: str = SANITIZER_VERSION) -> str:
    """Strict bounded single-article transformation, not a viewer or permission gate."""
    if type(version) is not str or version != SANITIZER_VERSION:
        raise TransformError("unsupported_version")
    return _sanitize(original, NodeBudget())

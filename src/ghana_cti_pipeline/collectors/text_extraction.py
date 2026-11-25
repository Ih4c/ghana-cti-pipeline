"""Extract text from the sanitizer's canonical vocabulary, with versioned separators."""

from ghana_cti_pipeline.collectors.html_fragment import FragmentParser
from ghana_cti_pipeline.collectors.html_profile import (
    BLOCK,
    EXTRACTOR_VERSION,
    NodeBudget,
    Output,
    TransformError,
    article,
)


class _Extractor(FragmentParser):
    def __init__(self, source, nodes):
        super().__init__(source, nodes, canonical=True)
        self.output = Output()
        self.rows: list[int] = []

    def open_tag(self, tag):
        if tag in BLOCK:
            self.output.boundary(2)
        elif tag in {"li", "tr"}:
            self.output.boundary(1)
            if tag == "tr":
                self.rows.append(0)
        elif tag == "br":
            self.output.write("\n")
        elif tag in {"th", "td"}:
            if self.rows:
                if self.rows[-1]:
                    self.output.write("\t")
                self.rows[-1] += 1
            elif self.output.size and not self.output.trailing_newlines:
                self.output.write("\t")

    def close_tag(self, tag):
        if tag == "tr":
            self.rows.pop()
        if tag in BLOCK:
            self.output.boundary(2)
        elif tag in {"li", "tr"}:
            self.output.boundary(1)

    def text(self, data):
        self.output.write(data)


def _extract(sanitized: str, nodes: NodeBudget) -> str:
    article(sanitized)
    # Only derived text normalizes line endings. No unescape of the parsed result.
    source = sanitized.replace("\r\n", "\n").replace("\r", "\n")
    parser = _Extractor(source, nodes)
    parser.run()
    return parser.output.finish(plain=True)


def extract_text(sanitized: str, *, version: str = EXTRACTOR_VERSION) -> str:
    """Reject attributes/noncanonical markup rather than laundering arbitrary HTML."""
    if type(version) is not str or version != EXTRACTOR_VERSION:
        raise TransformError("unsupported_version")
    return _extract(sanitized, NodeBudget())

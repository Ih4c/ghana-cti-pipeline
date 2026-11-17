"""Dependency direction and a fixture-only adapter prove the minimal boundary."""

import ast
import json
from pathlib import Path

import ghana_cti_pipeline
from ghana_cti_pipeline.collectors.interfaces import Collector, CollectorError, FetchedDocument
from ghana_cti_pipeline.core.models import Provenance, SourceItem


class FixtureCollector:
    source_id = "synthetic-advisories"

    def __init__(self, item):
        self.item = item

    def fetch(self) -> FetchedDocument:
        return FetchedDocument(
            provenance=Provenance.model_validate(self.item["provenance"]),
            body=json.dumps(self.item).encode("utf-8"),
            media_type="application/json",
        )

    def parse(self, document: FetchedDocument) -> tuple[SourceItem, ...]:
        return (SourceItem.model_validate_json(document.body),)


def test_fixture_adapter_uses_shared_contract(records):
    collector: Collector = FixtureCollector(records["source_item"])
    document = collector.fetch()
    (item,) = collector.parse(document)
    assert item.provenance == document.provenance
    assert item.provenance.source_id == collector.source_id


def test_collector_failure_has_safe_message():
    failure = CollectorError(source_id="synthetic", code="timeout", retryable=True)
    assert failure.retryable
    assert failure.code == "timeout"
    assert str(failure) == "collector operation failed"


def test_components_only_depend_on_core_or_themselves():
    root = Path(ghana_cti_pipeline.__file__).parent
    for path in root.rglob("*.py"):
        component = path.relative_to(root).parts[0]
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert not node.level, f"Use absolute imports to make boundaries explicit: {path}"
                modules = [node.module or ""]
            elif isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            else:
                continue
            for module in modules:
                if module.startswith("ghana_cti_pipeline."):
                    dependency = module.split(".")[1]
                    assert dependency in {component, "core"}, (path, module)

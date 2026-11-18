"""Dependency direction and a fixture-only adapter prove the minimal boundary."""

import ast
import json
from pathlib import Path

import pytest

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


def assert_dependency_direction(source: str, component: str) -> None:
    """Require static, absolute dependencies; importlib calls cannot hide computed targets."""
    nodes = list(ast.walk(ast.parse(source)))
    importlib_names = {"importlib"}
    dynamic_import_names = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            importlib_names.update(
                alias.asname or alias.name for alias in node.names if alias.name == "importlib"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            dynamic_import_names.update(
                alias.asname or alias.name for alias in node.names if alias.name == "import_module"
            )
            assert all(alias.name != "*" for alias in node.names), "No importlib wildcard imports"

    for node in nodes:
        if isinstance(node, ast.Call):
            function = node.func
            dynamic = (isinstance(function, ast.Name) and function.id in dynamic_import_names) or (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id in importlib_names
                and function.attr == "import_module"
            )
            assert not dynamic, "Use static imports instead of importlib.import_module"
        if isinstance(node, ast.ImportFrom):
            assert not node.level, "Use absolute imports to make boundaries explicit"
            modules = (
                [f"ghana_cti_pipeline.{alias.name}" for alias in node.names]
                if node.module == "ghana_cti_pipeline"
                else [node.module or ""]
            )
        elif isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        else:
            continue
        for module in modules:
            if module.startswith("ghana_cti_pipeline."):
                dependency = module.split(".")[1]
                assert dependency in {component, "core"}, f"Forbidden dependency: {module}"


@pytest.mark.parametrize(
    "source",
    [
        "import ghana_cti_pipeline.triage",
        "from ghana_cti_pipeline.triage import rank",
        "from ghana_cti_pipeline import triage",
        "from ghana_cti_pipeline import core, triage as ranking",
        "import importlib\nimportlib.import_module('ghana_cti_pipeline.triage')",
        "import importlib as loader\nloader.import_module(target)",
        "from importlib import import_module\nimport_module('ghana_cti_pipeline.triage')",
        "from importlib import import_module as load\nload(target)",
    ],
)
def test_dependency_checker_rejects_cross_component_and_dynamic_imports(source):
    with pytest.raises(AssertionError, match="Forbidden dependency|Use static imports"):
        assert_dependency_direction(source, "collectors")


@pytest.mark.parametrize(
    "source",
    [
        "from ghana_cti_pipeline import core, collectors as adapters",
        "from ghana_cti_pipeline.core.models import SourceItem",
        "import ghana_cti_pipeline.collectors.interfaces",
        "import json",
    ],
)
def test_dependency_checker_allows_core_own_component_and_external_imports(source):
    assert_dependency_direction(source, "collectors")


def test_components_only_depend_on_core_or_themselves():
    root = Path(ghana_cti_pipeline.__file__).parent
    for path in root.rglob("*.py"):
        component = path.relative_to(root).parts[0]
        try:
            assert_dependency_direction(path.read_text("utf-8"), component)
        except AssertionError as error:
            raise AssertionError(f"{path}: {error}") from error

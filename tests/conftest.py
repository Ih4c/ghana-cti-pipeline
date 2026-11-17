"""Synthetic data only; tests must never contact sources or paid services."""

import json
import socket
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Network access is forbidden in fixture tests")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture
def records():
    return json.loads((Path(__file__).parent / "fixtures" / "contracts.json").read_text("utf-8"))

from pathlib import Path

import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.domain.verification import verify


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parents[2]
    return load_repository(base / "examples" / "repo_example.json")


def test_verify_empty_state(repo):
    assert verify(repo, []) == []


def test_verify_unknown_version(repo):
    violations = verify(repo, [("app", "9.9")])
    assert violations


def test_verify_unknown_package(repo):
    violations = verify(repo, [("no-such-package", "1.0")])
    assert violations


def test_verify_two_versions_same_package(repo):
    violations = verify(repo, [("lib", "1.0"), ("lib", "2.0")])
    assert violations


def test_verify_missing_dependency(repo):
    violations = verify(repo, [("app", "2.0")])
    assert any("lib" in v for v in violations)


def test_verify_conflict(repo):
    violations = verify(repo, [("legacy", "1.0"), ("util", "2.0")])
    assert violations


def test_verify_valid_solution(repo):
    installed = [("app", "2.0"), ("lib", "2.0"), ("util", "2.0")]
    assert verify(repo, installed) == []


def test_verify_valid_tool_solution(repo):
    installed = [("tool", "1.1"), ("lib", "1.0"), ("json-slow", "1.0")]
    assert verify(repo, installed) == []


def test_verify_missing_request(repo):
    installed = [("lib", "2.0")]
    violations = verify(repo, installed, requests=["app"])
    assert violations


def test_verify_request_satisfied(repo):
    installed = [("app", "2.0"), ("lib", "2.0"), ("util", "2.0")]
    assert verify(repo, installed, requests=["app"]) == []

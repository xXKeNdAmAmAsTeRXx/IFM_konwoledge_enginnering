from pathlib import Path

import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.use_cases.install import install


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parents[2]
    return load_repository(base / "examples" / "repo_example.json")


def test_install_empty_requests(repo):
    assert install(repo, []) == []


def test_install_app(repo):
    result = install(repo, ["app"])
    assert set(result) == {
        ("app", "2.0"),
        ("lib", "2.0"),
        ("util", "2.0"),
    }


def test_install_tool(repo):
    result = install(repo, ["tool"])
    assert set(result) == {
        ("tool", "1.1"),
        ("lib", "1.0"),
        ("json-slow", "1.0"),
    }


def test_install_app_and_tool(repo):
    result = install(repo, ["app", "tool"])
    assert set(result) == {
        ("app", "1.0"),
        ("tool", "1.1"),
        ("lib", "1.0"),
        ("json-slow", "1.0"),
    }


def test_install_app_and_legacy(repo):
    result = install(repo, ["app", "legacy"])
    assert set(result) == {
        ("app", "1.0"),
        ("legacy", "1.0"),
        ("lib", "1.0"),
    }


def test_install_exact_version(repo):
    result = install(repo, ["app==2.0"])
    assert ("app", "2.0") in result


def test_install_no_solution(repo):
    with pytest.raises(Exception):
        install(repo, ["app==2.0", "tool"])


def test_install_unique_packages(repo):
    result = install(repo, ["app", "tool"])
    names = [name for name, _ in result]
    assert len(names) == len(set(names))

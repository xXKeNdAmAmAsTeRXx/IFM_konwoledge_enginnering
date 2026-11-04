from pathlib import Path

import pytest
from packaging.version import Version

from package_manager.domain.model import State
from package_manager.domain.verification import verify
from package_manager.infrastructure.parsing import load_repository
from package_manager.infrastructure.state import parse_state
from package_manager.use_cases.update import analyze_update, update


@pytest.fixture
def repo():
    root = Path(__file__).resolve().parents[2]
    return load_repository(root / "examples" / "repo_example.json")


@pytest.fixture
def example_state():
    root = Path(__file__).resolve().parents[2]
    return parse_state((root / "examples" / "state_example.txt").read_text(encoding="utf-8"))


@pytest.fixture
def ab_state():
    return State(packages={
        "a": (Version("1.0"), True),
        "b": (Version("1.0"), True),
    })


def versions(state):
    return {name: str(v) for name, (v, _) in state.packages.items()}


def test_update_all_from_example_state(repo, example_state):
    result = update(repo, example_state)
    assert versions(result) == {
        "tool": "1.1", "lib": "1.5", "json-slow": "1.0", "app": "1.0", "util": "2.0",
    }
    assert verify(repo, result.get_packages_list()) == []


def test_update_keeps_manual_flags(repo, example_state):
    result = update(repo, example_state)
    assert result.packages["app"][1] is True
    assert result.packages["util"][1] is False


def test_update_only_a_has_no_conflict(repo, ab_state):
    result = update(repo, ab_state, ["a"])
    assert versions(result) == {"a": "2.0", "b": "1.0"}
    assert analyze_update(repo, ab_state, ["a"])["core"] == []


def test_update_conflict_gives_pareto_front(repo, ab_state):
    report = analyze_update(repo, ab_state)
    assert report["best"] == {"a": "2.0", "b": "2.0"}
    assert report["core"]
    assert sorted(report["conflict"]) == ["a", "b"]
    assert len(report["front"]) == 2
    assert {"a": "2.0", "b": "1.0"} in report["front"]
    assert {"a": "1.1", "b": "2.0"} in report["front"]


def test_update_unknown_package_is_rejected(repo, example_state):
    with pytest.raises(Exception):
        update(repo, example_state, ["web"])
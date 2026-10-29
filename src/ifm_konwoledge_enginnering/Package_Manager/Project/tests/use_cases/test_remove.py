from pathlib import Path

import pytest
from packaging.version import Version

from package_manager.infrastructure.parsing import load_repository
from package_manager.infrastructure.state import parse_state
from package_manager.domain.verification import verify
from package_manager.use_cases.remove import remove


# pytestmark = pytest.mark.skip(reason="Task 6 removal behavior is not implemented yet")


@pytest.fixture
def inputs():
    project_root = Path(__file__).resolve().parents[2]
    repo = load_repository(project_root / "examples" / "repo_example.json")
    state = parse_state(
        (project_root / "examples" / "state_example.txt").read_text(encoding="utf-8")
    )
    return repo, state


def test_remove_tool_without_autoremove(inputs):
    repo, state = inputs

    result = remove(repo, state, ["tool"], autoremove=False)

    assert set(result.packages) == {"app", "lib", "json-slow"}
    assert "tool" not in result.packages
    assert result.packages["app"] == (Version("1.0"), True)
    assert result.packages["lib"] == (Version("1.0"), False)
    assert result.packages["json-slow"] == (Version("1.0"), False)
    assert verify(repo, result.get_packages_list()) == []


def test_remove_tool_with_autoremove(inputs):
    repo, state = inputs

    result = remove(repo, state, ["tool"], autoremove=True)

    assert set(result.packages) == {"app", "lib"}
    assert "tool" not in result.packages
    assert "json-slow" not in result.packages
    assert result.packages["app"] == (Version("1.0"), True)
    assert result.packages["lib"] == (Version("1.0"), False)
    assert verify(repo, result.get_packages_list()) == []


def test_remove_lib_removes_dependents(inputs):
    repo, state = inputs

    result = remove(repo, state, ["lib"], autoremove=False)

    assert set(result.packages) == {"json-slow"}
    assert "lib" not in result.packages
    assert "app" not in result.packages
    assert "tool" not in result.packages
    assert result.packages["json-slow"] == (Version("1.0"), False)
    assert verify(repo, result.get_packages_list()) == []

from pathlib import Path

import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.infrastructure.state import parse_state
from package_manager.use_cases.remove import remove


pytestmark = pytest.mark.skip(reason="Task 6 removal behavior is not implemented yet")


@pytest.fixture
def inputs():
    project_root = Path(__file__).resolve().parents[2]
    repo = load_repository(project_root / "examples" / "repo_example.json")
    state = parse_state(
        (project_root / "examples" / "state_example.txt").read_text(encoding="utf-8")
    )
    return repo, state


def test_remove_package_and_dependent_packages(inputs):
    repo, state = inputs

    result = remove(repo, state, ["lib"])

    assert set(result.packages) == {"json-slow"}


def test_remove_autoremove_is_supported(inputs):
    repo, state = inputs

    result = remove(repo, state, ["tool"], autoremove=True)

    assert "tool" not in result.packages
    assert "json-slow" not in result.packages

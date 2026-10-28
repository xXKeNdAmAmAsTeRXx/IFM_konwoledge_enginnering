from pathlib import Path

import z3
import pytest

from package_manager.install import _objectives_for_not_empty_state
from package_manager.parsing import load_repository
from package_manager.model import State
from package_manager.versioning import parse_version


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parent.parent.parent
    return load_repository(base / "examples" / "repo_example.json")


def test_objectives_state_returns_five(repo):
    state = State(packages={"lib": (parse_version("1.0"), False)})
    result = _objectives_for_not_empty_state(repo, state, ["app"])
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(x, z3.ExprRef) for x in result)

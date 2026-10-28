from pathlib import Path

import z3
import pytest

from package_manager.install import _objectives_for_empty_state
from package_manager.parsing import load_repository


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parent.parent.parent
    return load_repository(base / "examples" / "repo_example.json")


def test_objectives_empty_returns_three(repo):
    result = _objectives_for_empty_state(repo, ["app"])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, z3.ExprRef) for x in result)

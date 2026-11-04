from pathlib import Path

import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.use_cases.explain import explain


@pytest.fixture
def repo():
    project_root = Path(__file__).resolve().parents[2]
    return load_repository(project_root / "examples" / "repo_example.json")


def test_explain_unsatisfiable_requests(repo):
    result = explain(repo, ["app==2.0", "tool"])

    assert result
    assert all(isinstance(item, str) for item in result)
    assert any("app==2.0" in item for item in result)
    assert any("tool" in item for item in result)


def test_explain_satisfiable_requests(repo):
    assert explain(repo, ["app"]) == []

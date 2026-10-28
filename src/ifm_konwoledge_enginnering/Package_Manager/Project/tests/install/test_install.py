from pathlib import Path

import pytest

from package_manager.parsing import load_repository
from package_manager.install import install


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parent.parent.parent
    return load_repository(base / "examples" / "repo_example.json")


def test_install_empty(repo):
    assert install(repo, []) == []


def test_install_app(repo):
    result = install(repo, ["app"])
    assert set(result) == {("app", "2.0"), ("lib", "2.0"), ("util", "2.0")}


def test_install_no_solution(repo):
    with pytest.raises(Exception):
        install(repo, ["app==2.0", "tool"])

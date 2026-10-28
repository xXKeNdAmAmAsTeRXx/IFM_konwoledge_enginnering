from pathlib import Path

import pytest

from package_manager.install import _calculate_obsolesce_dict
from package_manager.parsing import load_repository


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parent.parent.parent
    return load_repository(base / "examples" / "repo_example.json")


def test_obsolescence_keys(repo):
    from package_manager.kb import build_variables
    variables = build_variables(repo)
    result = _calculate_obsolesce_dict(repo, variables)
    for key in result:
        assert isinstance(key, tuple)
        assert len(key) == 2


def test_obsolescence_newest_is_zero(repo):
    from package_manager.kb import build_variables
    variables = build_variables(repo)
    result = _calculate_obsolesce_dict(repo, variables)
    # lib newest version should have index 0
    lib_versions = repo.versions_of("lib")
    assert result[("lib", str(lib_versions[0]))] == 0

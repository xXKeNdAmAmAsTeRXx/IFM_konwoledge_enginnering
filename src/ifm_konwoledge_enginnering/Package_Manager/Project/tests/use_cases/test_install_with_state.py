from pathlib import Path

import pytest
from packaging.version import Version

from package_manager.infrastructure.parsing import load_repository
from package_manager.infrastructure.state import parse_state
from package_manager.use_cases.install import install


@pytest.fixture
def inputs():
    project_root = Path(__file__).resolve().parents[2]
    repo = load_repository(project_root / "examples" / "repo_example.json")
    state = parse_state(
        (project_root / "examples" / "state_example.txt").read_text(encoding="utf-8")
    )
    return repo, state


def test_install_updates_existing_state(inputs, capsys):
    repo, state = inputs

    result = install(repo, ["app==2.0"], initial_state=state)

    assert {name: str(version) for name, (version, _) in result.packages.items()} == {
        "app": "2.0",
        "lib": "2.0",
        "util": "2.0",
        "json-slow": "1.0",
    }
    assert result.packages["app"] == (Version("2.0"), True)
    assert result.packages["lib"] == (Version("2.0"), False)

    output = capsys.readouterr().out
    assert "Upgrade app 1.0 -> 2.0" in output
    assert "Upgrade lib 1.0 -> 2.0" in output
    assert "Install util 2.0" in output
    assert "Remove tool 1.1" in output

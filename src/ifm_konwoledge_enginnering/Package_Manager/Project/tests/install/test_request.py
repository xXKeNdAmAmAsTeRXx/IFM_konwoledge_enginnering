from pathlib import Path

from package_manager.install import Request
from package_manager.parsing import load_repository


def test_request_defaults():
    req = Request(repository=None, requested_packages=[])
    assert req.requested_packages == []


def test_request_holds_packages():
    base = Path(__file__).resolve().parent.parent.parent
    repo = load_repository(base / "examples" / "repo_example.json")
    req = Request(repository=repo, requested_packages=["app"])
    assert req.requested_packages == ["app"]
    assert req.repository is repo

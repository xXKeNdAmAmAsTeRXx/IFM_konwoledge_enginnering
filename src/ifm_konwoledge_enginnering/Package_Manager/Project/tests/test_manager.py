import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MANAGER = BASE / "manager.py"


def make_requests(tmp_path, content="app\n"):
    path = tmp_path / "requests.txt"
    path.write_text(content, encoding="utf-8")
    return path
REPO = BASE / "examples" / "repo_example.json"
REQUESTS = None  # created per test


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(MANAGER), *args],
        cwd=BASE,
        capture_output=True,
        text=True,
    )


def test_install_basic(tmp_path):
    req = make_requests(tmp_path, "app\n")
    result = run_cli("install", str(req), "--repo", str(REPO))
    assert result.returncode == 0
    assert "app" in result.stdout


def test_install_print_axioms(tmp_path):
    req = make_requests(tmp_path, "app\n")
    result = run_cli("install", str(req), "--repo", str(REPO), "--print-axioms")
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_install_missing_repo(tmp_path):
    req = make_requests(tmp_path, "app\n")
    result = run_cli("install", str(req))
    assert result.returncode != 0


def test_install_invalid_repo(tmp_path):
    bad_repo = tmp_path / "bad.json"
    bad_repo.write_text("{ invalid json", encoding="utf-8")
    req = make_requests(tmp_path, "app\n")
    result = run_cli("install", str(req), "--repo", str(bad_repo))
    assert result.returncode != 0

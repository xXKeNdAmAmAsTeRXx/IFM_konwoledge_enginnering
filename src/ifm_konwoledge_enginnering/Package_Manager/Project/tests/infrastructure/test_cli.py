from pathlib import Path

from package_manager.infrastructure.cli import (
    DEFAULT_REPOSITORY,
    DEFAULT_STATE,
    main,
)
from package_manager.infrastructure.state import parse_state


BASE = Path(__file__).resolve().parents[2]
REPO = BASE / "examples" / "repo_example.json"
EXAMPLE_STATE = BASE / "examples" / "state_example.txt"


def make_requests(tmp_path, content="app\n"):
    path = tmp_path / "requests.txt"
    path.write_text(content, encoding="utf-8")
    return path


def make_warning_repo(tmp_path):
    path = tmp_path / "repo-with-warning.json"
    path.write_text(
        '{"packages": {"app": {"versions": {"1.0": '
        '{"requires": ["missingpkg"]}}}}}',
        encoding="utf-8",
    )
    return path


def seed_example_state(path):
    content = EXAMPLE_STATE.read_text(encoding="utf-8")
    path.write_text(content, encoding="utf-8")


def run_cli(tmp_path, *args, repo_path=REPO):
    return main(
        list(args),
        repo_path=repo_path,
        state_path=tmp_path / "state.txt",
    )


def test_list_without_saved_state_reports_empty_environment(tmp_path, capsys):
    result = run_cli(tmp_path, "list")

    assert result == 0
    assert "No packages installed" in capsys.readouterr().out


def test_repository_warnings_are_silent_by_default(tmp_path, capsys):
    result = run_cli(
        tmp_path,
        "list",
        repo_path=make_warning_repo(tmp_path),
    )

    assert result == 0
    assert "WARNING" not in capsys.readouterr().err


def test_show_warnings_flag_prints_to_stderr(tmp_path, capsys):
    result = run_cli(
        tmp_path,
        "list",
        "--show-warnings",
        repo_path=make_warning_repo(tmp_path),
    )

    assert result == 0
    assert "WARNING Package app=1.0" in capsys.readouterr().err


def test_install_saves_state_and_list_displays_it(tmp_path, capsys):
    requests = make_requests(tmp_path, "app\n")

    install_result = run_cli(tmp_path, "install", str(requests))
    saved_state_text = (tmp_path / "state.txt").read_text(encoding="utf-8")
    saved_state = parse_state(saved_state_text)

    assert install_result == 0
    assert set(saved_state.packages) == {"app", "lib", "util"}
    assert saved_state.packages["app"][1] is True
    assert saved_state.packages["lib"][1] is False

    list_result = run_cli(tmp_path, "list")
    output = capsys.readouterr().out
    assert list_result == 0
    assert "app 2.0 manual" in output
    assert "lib 2.0" in output


def test_install_updates_persisted_state(tmp_path, capsys):
    state_path = tmp_path / "state.txt"
    seed_example_state(state_path)
    requests = make_requests(tmp_path, "app==2.0\n")

    result = run_cli(tmp_path, "install", str(requests))

    assert result == 0
    assert "Upgrade app 1.0 -> 2.0" in capsys.readouterr().out
    saved_state = parse_state(state_path.read_text(encoding="utf-8"))
    assert str(saved_state.packages["app"][0]) == "2.0"
    assert saved_state.packages["app"][1] is True


def test_failed_install_does_not_create_or_change_state(tmp_path, capsys):
    requests = make_requests(tmp_path, "app==2.0\ntool\n")

    result = run_cli(tmp_path, "install", str(requests))

    assert result != 0
    assert not (tmp_path / "state.txt").exists()
    output = capsys.readouterr().out
    assert "Minimal unsatisfiable core" in output
    assert "app==2.0" in output
    assert "tool" in output


def test_failed_update_preserves_saved_state(tmp_path):
    state_path = tmp_path / "state.txt"
    seed_example_state(state_path)
    original_state = state_path.read_text(encoding="utf-8")
    requests = make_requests(tmp_path, "app==2.0\ntool\n")

    result = run_cli(tmp_path, "install", str(requests))

    assert result != 0
    assert state_path.read_text(encoding="utf-8") == original_state


def test_remove_persists_result_with_autoremove(tmp_path, capsys):
    state_path = tmp_path / "state.txt"
    seed_example_state(state_path)

    result = run_cli(tmp_path, "remove", "tool", "--autoremove")

    assert result == 0
    saved_state_text = state_path.read_text(encoding="utf-8")
    saved_state = parse_state(saved_state_text)
    assert set(saved_state.packages) == {"app", "lib"}
    assert "tool" not in saved_state_text
    assert "json-slow" not in saved_state_text
    assert "app 1.0 manual" in capsys.readouterr().out


def test_remove_keeps_other_packages_without_autoremove(tmp_path):
    state_path = tmp_path / "state.txt"
    seed_example_state(state_path)

    result = run_cli(tmp_path, "remove", "tool")

    assert result == 0
    saved_state = parse_state(state_path.read_text(encoding="utf-8"))
    assert "tool" not in saved_state.packages
    assert "json-slow" in saved_state.packages


def test_remove_rejects_unknown_package(tmp_path, capsys):
    result = run_cli(tmp_path, "remove", "does-not-exist")

    assert result != 0
    assert "unknown package" in capsys.readouterr().err


def test_explain_command_reports_unsatisfiable_core(tmp_path, capsys):
    requests = make_requests(tmp_path, "app==2.0\ntool\n")

    result = run_cli(tmp_path, "explain", str(requests))

    assert result == 0
    output = capsys.readouterr().out
    assert "Minimal unsatisfiable core" in output
    assert "app==2.0" in output
    assert "tool" in output


def test_explain_command_reports_satisfiable_requests(tmp_path, capsys):
    requests = make_requests(tmp_path, "app\n")

    result = run_cli(tmp_path, "explain", str(requests))

    assert result == 0
    assert "satisfiable" in capsys.readouterr().out.lower()


def test_print_axioms_option_is_preserved(tmp_path, capsys):
    requests = make_requests(tmp_path, "app\n")

    result = run_cli(tmp_path, "install", str(requests), "--print-axioms")

    assert result == 0
    assert capsys.readouterr().out.strip()


def test_invalid_repository_is_reported(tmp_path, capsys):
    bad_repo = tmp_path / "bad.json"
    bad_repo.write_text("{ invalid json", encoding="utf-8")
    requests = make_requests(tmp_path, "app\n")

    result = run_cli(
        tmp_path,
        "install",
        str(requests),
        repo_path=bad_repo,
    )

    assert result != 0
    assert "JSON syntax error" in capsys.readouterr().err

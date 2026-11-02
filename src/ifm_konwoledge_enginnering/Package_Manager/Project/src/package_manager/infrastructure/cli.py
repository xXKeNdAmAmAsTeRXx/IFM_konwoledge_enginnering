"""Command-line interface for the package manager use cases."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from package_manager.domain.errors import (
    NoSolutionError,
    PackageError,
    RequestError,
)
from package_manager.domain.model import State
from package_manager.domain.verification import verify
from package_manager.domain.versioning import (
    normalize_package_name,
    parse_requirement,
    parse_version,
)
from package_manager.infrastructure.parsing import (
    load_repository,
    parse_requests_text,
)
from package_manager.infrastructure.state import parse_state, write_state
from package_manager.use_cases.explain import explain
from package_manager.use_cases.install import install
from package_manager.use_cases.remove import remove


PROJECT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_REPOSITORY = PROJECT_DIR / "data/repos/repos/k12/repo_100.json"
DEFAULT_STATE = PROJECT_DIR / "state.txt"


def _read_requests(path: str) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    return parse_requests_text(text, source=path)


def _collect_requests(args: argparse.Namespace) -> list[str]:
    request_strings = []
    if getattr(args, "requests", None):
        request_strings.extend(_read_requests(args.requests))
    request_strings.extend(getattr(args, "request", []))
    if not request_strings:
        raise RequestError("requests", "provide a request file or --request")
    return request_strings


def _read_state_if_present(path: Path) -> State | None:
    if not path.exists():
        return None
    return parse_state(path.read_text(encoding="utf-8"))


def _install_result_to_state(result, request_strings: list[str]) -> State:
    if isinstance(result, State):
        return result

    requested_names = {
        atom.package
        for raw_request in request_strings
        for atom in parse_requirement(raw_request).alternatives
    }
    return State(
        packages={
            name: (parse_version(version), name in requested_names)
            for name, version in result
        }
    )


def _print_state(state: State) -> None:
    state_text = write_state(state)
    if not state_text:
        print("No packages installed.")
        return
    print(state_text, end="")


def _save_state(path: Path, state: State) -> None:
    """Atomically persist a state so an interrupted write won't corrupt it."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(write_state(state))
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _validate_state(repo, state: State) -> None:
    errors = verify(repo, state.get_packages_list())
    if errors:
        raise RequestError("state", "; ".join(errors))


def _print_explanation(core: list[str]) -> None:
    if not core:
        print("The requests are satisfiable.")
        return

    print("The requests cannot be installed. Minimal unsatisfiable core:")
    for label in core:
        print(f"- {label}")


def _run_install(
    args: argparse.Namespace,
    repo_path: Path,
    state_path: Path,
) -> int:
    repo = load_repository(repo_path, show_warnings=args.show_warnings)
    request_strings = _collect_requests(args)
    initial_state = _read_state_if_present(state_path)
    if initial_state is not None:
        _validate_state(repo, initial_state)

    try:
        result = install(
            repo,
            request_strings,
            print_axioms=args.print_axioms,
            initial_state=initial_state,
        )
    except NoSolutionError as exc:
        print(str(exc), file=sys.stderr)
        _print_explanation(explain(repo, request_strings))
        return 1

    final_state = _install_result_to_state(result, request_strings)
    _save_state(state_path, final_state)
    _print_state(final_state)
    return 0


def _run_remove(
    args: argparse.Namespace,
    repo_path: Path,
    state_path: Path,
) -> int:
    repo = load_repository(repo_path, show_warnings=args.show_warnings)
    state = _read_state_if_present(state_path) or State()
    _validate_state(repo, state)

    package_names = [normalize_package_name(name) for name in args.packages]
    unknown_packages = sorted(set(package_names) - set(repo.packages))
    if unknown_packages:
        raise RequestError(
            "packages",
            f"unknown package(s): {', '.join(unknown_packages)}",
        )

    final_state = remove(
        repo,
        state,
        package_names,
        autoremove=args.autoremove,
    )
    _save_state(state_path, final_state)
    _print_state(final_state)
    return 0


def _run_list(
    args: argparse.Namespace,
    repo_path: Path,
    state_path: Path,
) -> int:
    repo = load_repository(repo_path, show_warnings=args.show_warnings)
    if not state_path.exists():
        print("No packages installed (state file has not been created).")
        return 0

    state = parse_state(state_path.read_text(encoding="utf-8"))
    _validate_state(repo, state)
    _print_state(state)
    return 0


def _run_explain(args: argparse.Namespace, repo_path: Path) -> int:
    repo = load_repository(repo_path, show_warnings=args.show_warnings)
    request_strings = _collect_requests(args)
    _print_explanation(explain(repo, request_strings))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage packages in the k12 repository"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", help="List packages in the saved state"
    )
    _add_warning_option(list_parser)

    install_parser = subparsers.add_parser(
        "install", help="Install requests and save the resulting state"
    )
    install_parser.add_argument(
        "requests",
        nargs="?",
        help="Optional path to a file containing package requests",
    )
    install_parser.add_argument(
        "-r",
        "--request",
        action="append",
        default=[],
        help="Request string, e.g. app==2.0; may be repeated",
    )
    install_parser.add_argument(
        "--print-axioms",
        action="store_true",
        help="Print example repository axioms",
    )
    _add_warning_option(install_parser)

    remove_parser = subparsers.add_parser(
        "remove", help="Remove packages from the saved state"
    )
    remove_parser.add_argument(
        "packages", nargs="+", help="Package names to remove"
    )
    remove_parser.add_argument(
        "--autoremove",
        action="store_true",
        help="Also remove automatically installed packages no longer needed",
    )
    _add_warning_option(remove_parser)

    explain_parser = subparsers.add_parser(
        "explain", help="Explain an unsatisfiable request set"
    )
    explain_parser.add_argument(
        "requests",
        nargs="?",
        help="Optional path to a file containing package requests",
    )
    explain_parser.add_argument(
        "-r",
        "--request",
        action="append",
        default=[],
        help="Request string, e.g. app==2.0; may be repeated",
    )
    _add_warning_option(explain_parser)

    return parser


def _add_warning_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--show-warnings",
        action="store_true",
        help="Show repository validation warnings",
    )


def main(
    argv: list[str] | None = None,
    *,
    repo_path: Path = DEFAULT_REPOSITORY,
    state_path: Path = DEFAULT_STATE,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "install":
            return _run_install(args, Path(repo_path), Path(state_path))
        if args.command == "remove":
            return _run_remove(args, Path(repo_path), Path(state_path))
        if args.command == "list":
            return _run_list(args, Path(repo_path), Path(state_path))
        if args.command == "explain":
            return _run_explain(args, Path(repo_path))
        parser.error(f"unknown command {args.command!r}")
    except PackageError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

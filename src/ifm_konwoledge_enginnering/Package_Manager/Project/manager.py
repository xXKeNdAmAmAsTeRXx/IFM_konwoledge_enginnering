import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from package_manager.errors import PackageError, RequestError
from package_manager.install import install
from package_manager.parsing import load_repository, parse_requests_text


def main():
    parser = argparse.ArgumentParser(description="Package manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install a request set")
    install_parser.add_argument("requests", help="Path to requests file")
    install_parser.add_argument("--repo", required=True, help="Path to repository JSON")
    install_parser.add_argument("--print-axioms", action="store_true", help="Print example axioms")
    install_parser.add_argument("--state-out", help="Path to write resulting state")

    args = parser.parse_args()

    if args.command == "install":
        try:
            repo = load_repository(args.repo)
            request_strings = parse_requests_text(Path(args.requests).read_text(encoding="utf-8"))
            installed = install(repo, request_strings, print_axioms=args.print_axioms)
        except (PackageError, RequestError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        for package, version in sorted(installed):
            print(f"{package} {version}")

        if args.state_out:
            lines = [f"{package} {version}" for package, version in sorted(installed)]
            Path(args.state_out).write_text("\n".join(lines) + "\n", encoding="utf-8")

        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

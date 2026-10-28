"""Public install use-case entry point."""

from typing import List, Tuple

from package_manager.domain.model import Repository, State
from package_manager.use_cases.empty_install import install_empty
from package_manager.use_cases.install_with_state import install_with_state


def install(
    repo: Repository,
    request_strings: List[str],
    print_axioms: bool = False,
    initial_state: State | None = None,
) -> List[Tuple[str, str]] | State:
    """Install requests, selecting the workflow by whether a state is supplied."""
    if initial_state is None:
        return install_empty(repo, request_strings, print_axioms=print_axioms)
    return install_with_state(
        repo,
        request_strings,
        initial_state,
        print_axioms=print_axioms,
    )


__all__ = ["install"]

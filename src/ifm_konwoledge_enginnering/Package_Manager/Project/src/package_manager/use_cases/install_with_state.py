"""Install requests into an existing environment (Task 6.1)."""

from typing import List

from package_manager.domain.model import Repository, State


def install_with_state(
    repo: Repository,
    request_strings: List[str],
    initial_state: State,
    print_axioms: bool = False,
) -> State:
    """Install requests while taking the existing environment into account.

    Task 6 installation and optimization behavior is not implemented yet.
    """
    raise NotImplementedError("Task 6 installation into a state is not implemented yet")

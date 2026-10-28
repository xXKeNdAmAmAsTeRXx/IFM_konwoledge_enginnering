"""Remove packages from an installed environment (Task 6.2)."""

from collections.abc import Iterable

from package_manager.domain.model import Repository, State


def remove(
    repo: Repository,
    state: State,
    package_names: Iterable[str],
    autoremove: bool = False,
) -> State:
    """Return a state with the requested packages removed.

    Task 6 removal and optimization behavior is not implemented yet.
    """
    raise NotImplementedError("Task 6 package removal is not implemented yet")

"""Explain unsatisfiable installation requests (Task 6.3)."""

from collections.abc import Sequence

from package_manager.domain.model import Repository


def explain(repo: Repository, request_strings: Sequence[str]) -> list[str]:
    """Return a human-readable unsatisfiable core for the requests.

    Task 6 explanation behavior is not implemented yet.
    """
    raise NotImplementedError("Task 6 explanations are not implemented yet")

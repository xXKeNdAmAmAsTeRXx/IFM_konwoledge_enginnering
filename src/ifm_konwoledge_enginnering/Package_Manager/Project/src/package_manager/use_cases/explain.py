"""Explain unsatisfiable installation requests (Task 6.3)."""

from collections.abc import Sequence

from package_manager.domain.model import Repository


def explain(repo: Repository, request_strings: Sequence[str]) -> list[str]:
    """Return a human-readable unsatisfiable core for the requests.

    TODO: Build a plain Z3 Solver from the generated repository axioms and add
    each parsed request as a separately tracked constraint.
    TODO: If the solver is unsatisfiable, shrink its unsat_core by checking
    each candidate removal, then return the associated human-readable labels.
    """
    raise NotImplementedError("Task 6 explanations are not implemented yet")

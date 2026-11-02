"""Explain unsatisfiable installation requests (Task 6.3)."""

from collections.abc import Sequence

import z3

from package_manager.domain.model import Repository
from package_manager.domain.versioning import parse_requirement
from package_manager.infrastructure.solver.knowledge_base import (
    build_axioms,
    build_variables,
    encode_requirement,
)


def explain(repo: Repository, request_strings: Sequence[str]) -> list[str]:
    """Return a human-readable, inclusion-minimal core for unsatisfiable input.

    Return an empty list when the requests are satisfiable.
    """
    variables = build_variables(repo)
    labeled_axioms = list(build_axioms(repo, variables))

    for idx, raw_request in enumerate(request_strings):
        request = parse_requirement(raw_request)
        formula = encode_requirement(request, repo, variables)
        label = f"Request #{idx+1}: {raw_request}"
        labeled_axioms.append((label, formula))

    solver = z3.Solver()
    records = []
    for idx, (label, formula) in enumerate(labeled_axioms):
        tracker = z3.FreshBool(f"core_{idx+1}")
        solver.assert_and_track(formula, tracker)
        records.append((tracker, label, formula))

    result = solver.check()

    if result == z3.sat:
        return []
    if result != z3.unsat:
        raise RuntimeError(
            f"Z3 could not determine satisfiability: {solver.reason_unknown()}"
        )

    core_trackers = {str(item) for item in solver.unsat_core()}
    core = [r for r in records if str(r[0]) in core_trackers]

    index = 0
    while index < len(core):
        trial = core[:index] + core[index + 1:]
        checker = z3.Solver()
        checker.add(*(formula for _, _, formula in trial))

        status = checker.check()
        if status == z3.unsat:
            core = trial
        elif status == z3.sat:
            index += 1
        else:
            raise RuntimeError(checker.reason_unknown())

    return [label for _, label, _ in core]

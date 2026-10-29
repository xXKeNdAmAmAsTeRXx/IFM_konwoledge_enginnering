"""Installation into an empty environment (Task 4.3)."""

from __future__ import annotations

from typing import List, Tuple

import z3

from package_manager.domain.errors import RequestError
from package_manager.domain.model import Repository
from package_manager.domain.versioning import parse_requirement
from package_manager.infrastructure.solver.knowledge_base import (
    build_knowledge_base,
    encode_requirement,
)
from package_manager.infrastructure.solver.objective_builders import obsolescence_cost


def install_empty(
    repo: Repository,
    request_strings: List[str],
    print_axioms: bool = False,
) -> List[Tuple[str, str]]:
    requests = [parse_requirement(req) for req in request_strings]

    variables, opt, axioms = build_knowledge_base(repo, print_axioms=print_axioms)

    for req in requests:
        opt.add(encode_requirement(req, repo, variables))

    obsolescence = [
        (package_name, str(version), rank)
        for package_name in repo.packages
        for rank, version in enumerate(repo.versions_of(package_name))
    ]

    requested_pkgs = {atom.package for req in requests for atom in req.alternatives}

    requested_obsolescence = [
        (package_name, version, rank)
        for package_name, version, rank in obsolescence
        if package_name in requested_pkgs
    ]
    expr_requested = obsolescence_cost(repo, variables, requested_obsolescence)

    count_terms = [z3.If(v, 1, 0) for v in variables.values()]
    expr_count = z3.Sum(count_terms) if count_terms else z3.IntVal(0)

    other_obsolescence = [
        (package_name, version, rank)
        for package_name, version, rank in obsolescence
        if package_name not in requested_pkgs
    ]
    expr_other = obsolescence_cost(repo, variables, other_obsolescence)

    opt.set(priority="lex")
    opt.minimize(expr_requested)
    opt.minimize(expr_count)
    opt.minimize(expr_other)

    if opt.check() != z3.sat:
        raise RequestError("", "no solution for the given requests")

    model = opt.model()
    installed = [
        (package, version)
        for (package, version), var in variables.items()
        if z3.is_true(model.eval(var))
    ]
    return installed

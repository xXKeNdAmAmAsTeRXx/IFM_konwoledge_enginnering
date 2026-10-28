"""Install requests into an existing environment (Task 6.1)."""
from typing import List

import z3

from package_manager.domain.errors import InvalidInitialStateError
from package_manager.domain.model import Repository, State
from package_manager.domain.verification import verify
from package_manager.domain.versioning import parse_requirement
from package_manager.infrastructure.solver.knowledge_base import build_knowledge_base


def install_with_state(
    repo: Repository,
    request_strings: List[str],
    initial_state: State,
    print_axioms: bool = False,
) -> State:
    """Install requests while taking the existing environment into account.

    Task 6 installation and optimization behavior is not implemented yet.
    """

    validation_errors = verify(repo, initial_state.get_packages_list())
    if validation_errors:
        raise InvalidInitialStateError("initial_state", "; ".join(validation_errors))

    # Keep the initial state as an optimization reference, not as fixed solver
    # assignments: Task 6.1 allows packages to change or be removed.
    variables, opt, axioms = build_knowledge_base(repo, print_axioms=print_axioms)
    installed_packages = initial_state.get_packages_list()
    installed_names = {package_name for package_name, _ in installed_packages}

    # 1. Minimize removed packages:
    removed_terms = []
    for package_name, _ in installed_packages:
        version_vars = [
            variables[(package_name, str(version))]
            for version in repo.versions_of(package_name)
        ]
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        removed_terms.append(z3.If(selected_any, 0, 1))

    expr_removed = z3.Sum(removed_terms) if removed_terms else z3.IntVal(0)

    # 2. Minimize version changes for packages that remain installed:
    changed_terms = []
    for package_name, old_version in installed_packages:
        version_vars = [
            variables[(package_name, str(version))]
            for version in repo.versions_of(package_name)
        ]
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        old_version_selected = variables[(package_name, old_version)]
        changed_and_retained = z3.And(selected_any, z3.Not(old_version_selected))
        changed_terms.append(z3.If(changed_and_retained, 1, 0))

    expr_changed = (z3.Sum(changed_terms) if changed_terms else z3.IntVal(0))

    # 3. Minimize obsolescence of requested packages not initially installed:
    requests = [parse_requirement(request) for request in request_strings]

    obsolescence = {}
    for requirement in requests:
        for atom in requirement.alternatives:
            if atom.package not in installed_names:
                for rank, version in enumerate(repo.versions_of(atom.package)):
                    obsolescence[(atom.package, str(version))] = rank

    obsolescence_terms = [
        rank * z3.If(variables[key], 1, 0)
        for key, rank in obsolescence.items()
    ]

    expr_obsolescence = (
        z3.Sum(obsolescence_terms) if obsolescence_terms else z3.IntVal(0)
    )

    # TODO 4: Minimize the number of new packages:
    #   sum(If(package was not initially installed and is selected, 1, 0)).

    added_terms = []
    for package_name in repo.packages:
        if package_name in installed_names:
            continue

        version_vars = [
            variables[(package_name, str(version))]
            for version in repo.versions_of(package_name)
        ]
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        added_terms.append(z3.If(selected_any, 1, 0))

    expr_added = (z3.Sum(added_terms) if added_terms else z3.IntVal(0))

    # TODO 5: Minimie obsolescence of other new packages:
    #   sum(obsolescence(package, version) * selected(package, version))
    #   for packages absent from initial_state and not requested.

    opt.set(priority="lex")
    opt.minimize(expr_removed)
    opt.minimize(expr_changed)
    opt.minimize(expr_obsolescence)
    opt.minimize(expr_added)

    #TODO: Changes plan

    raise NotImplementedError("Task 6 installation into a state is not implemented yet")

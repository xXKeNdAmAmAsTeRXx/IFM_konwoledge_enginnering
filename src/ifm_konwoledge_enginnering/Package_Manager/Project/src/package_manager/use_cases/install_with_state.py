"""Install requests into an existing environment (Task 6.1)."""
from typing import List

import z3

from package_manager.domain.errors import InvalidInitialStateError
from package_manager.domain.errors import RequestError
from package_manager.domain.model import Repository, State
from package_manager.domain.verification import verify
from package_manager.domain.versioning import parse_requirement, parse_version
from package_manager.infrastructure.solver.knowledge_base import (
    build_knowledge_base,
    encode_requirement,
    package_version_vars,
)


def build_change_plan(initial_state: State, final_state: State) -> list[str]:
    """Describe installs, removals, and version changes between two states."""
    initial_packages = initial_state.packages
    final_packages = final_state.packages
    changes = []

    for package_name in sorted(initial_packages.keys() | final_packages.keys()):
        old_package = initial_packages.get(package_name)
        new_package = final_packages.get(package_name)

        if old_package is None:
            new_version, _ = new_package
            changes.append(f"Install {package_name} {new_version}")
        elif new_package is None:
            old_version, _ = old_package
            changes.append(f"Remove {package_name} {old_version}")
        else:
            old_version, _ = old_package
            new_version, _ = new_package
            if old_version != new_version:
                action = "Upgrade" if new_version > old_version else "Downgrade"
                changes.append(
                    f"{action} {package_name} {old_version} -> {new_version}"
                )

    return changes


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
        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        removed_terms.append(z3.If(selected_any, 0, 1))

    expr_removed = z3.Sum(removed_terms) if removed_terms else z3.IntVal(0)

    # 2. Minimize version changes for packages that remain installed:
    changed_terms = []
    for package_name, old_version in installed_packages:
        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        old_version_selected = variables[(package_name, old_version)]
        changed_and_retained = z3.And(selected_any, z3.Not(old_version_selected))
        changed_terms.append(z3.If(changed_and_retained, 1, 0))

    expr_changed = (z3.Sum(changed_terms) if changed_terms else z3.IntVal(0))

    # 3. Minimize obsolescence of requested packages not initially installed:
    requests = [parse_requirement(request) for request in request_strings]
    for request in requests:
        opt.add(encode_requirement(request, repo, variables))

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

    # Minimize the number of new packages:
    added_terms = []
    for package_name in repo.packages:
        if package_name in installed_names:
            continue

        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        added_terms.append(z3.If(selected_any, 1, 0))

    expr_added = (z3.Sum(added_terms) if added_terms else z3.IntVal(0))

    # Minimie obsolescence of other new packages:
    requested_names = {
        atom.package
        for requirement in requests
        for atom in requirement.alternatives
    }

    obsolescence = {}
    for package_name in repo.packages:
        if package_name in requested_names:
            continue

        if package_name in installed_names:
            continue

        for rank, version in enumerate(repo.versions_of(package_name)):
            obsolescence[(package_name, str(version))] = rank

    obsolescence_terms = [
        rank * z3.If(variables[key], 1, 0)
        for key, rank in obsolescence.items()
    ]

    expr_obsolescence_new = (
        z3.Sum(obsolescence_terms) if obsolescence_terms else z3.IntVal(0)
    )


    opt.set(priority="lex")
    opt.minimize(expr_removed)
    opt.minimize(expr_changed)
    opt.minimize(expr_obsolescence)
    opt.minimize(expr_added)
    opt.minimize(expr_obsolescence_new)

    if opt.check() != z3.sat:
        raise RequestError("", "no solution for the given requests")

    model = opt.model()
    installed = [
        (package, version)
        for (package, version), var in variables.items()
        if z3.is_true(model.eval(var))
    ]

    initial_manual_flags = {
        name: manual for name, (_, manual) in initial_state.packages.items()
    }
    state_dict = {}
    for name, version in installed:
        is_manual = name in requested_names or initial_manual_flags.get(name, False)
        state_dict[name] = (parse_version(version), is_manual)

    final_state = State(packages=state_dict)
    changes = build_change_plan(initial_state, final_state)
    if changes:
        print("Change plan:")
        for change in changes:
            print(f"- {change}")
    else:
        print("No changes required.")

    return final_state

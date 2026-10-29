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
)
from package_manager.infrastructure.solver.objective_builders import (
    count_selected_packages,
    count_unselected_packages,
    count_version_changes,
    obsolescence_cost,
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
    expr_removed = count_unselected_packages(repo, variables, installed_names)

    # 2. Minimize version changes for packages that remain installed:
    expr_changed = count_version_changes(repo, variables, installed_packages)

    # 3. Minimize obsolescence of requested packages not initially installed:
    requests = [parse_requirement(request) for request in request_strings]
    for request in requests:
        opt.add(encode_requirement(request, repo, variables))

    requested_obsolescence = [
        (atom.package, str(version), rank)
        for requirement in requests
        for atom in requirement.alternatives
        if atom.package not in installed_names
        for rank, version in enumerate(repo.versions_of(atom.package))
    ]
    expr_obsolescence = obsolescence_cost(
        repo,
        variables,
        requested_obsolescence,
    )

    # Minimize the number of new packages:
    new_package_names = [
        package_name for package_name in repo.packages if package_name not in installed_names
    ]
    expr_added = count_selected_packages(repo, variables, new_package_names)

    # Minimie obsolescence of other new packages:
    requested_names = {
        atom.package
        for requirement in requests
        for atom in requirement.alternatives
    }
    other_obsolescence = [
        (package_name, str(version), rank)
        for package_name in repo.packages
        if package_name not in requested_names and package_name not in installed_names
        for rank, version in enumerate(repo.versions_of(package_name))
    ]
    expr_obsolescence_new = obsolescence_cost(repo, variables, other_obsolescence)


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

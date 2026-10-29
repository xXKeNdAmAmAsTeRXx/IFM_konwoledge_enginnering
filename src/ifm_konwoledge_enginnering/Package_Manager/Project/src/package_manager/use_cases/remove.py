"""Remove packages from an installed environment (Task 6.2)."""

from collections.abc import Iterable

import z3

from package_manager.domain.versioning import parse_version
from package_manager.domain.errors import InvalidInitialStateError, RequestError
from package_manager.domain.verification import verify
from package_manager.infrastructure.solver.knowledge_base import (
    build_knowledge_base,
    package_version_vars,
)
from package_manager.infrastructure.solver.objective_builders import (
    count_selected_packages,
    count_unselected_packages,
    count_version_changes,
)
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
    validation_errors = verify(repo, state.get_packages_list())
    if validation_errors:
        raise InvalidInitialStateError("initial_state", "; ".join(validation_errors))

    variables, opt, axioms = build_knowledge_base(repo)
    installed_packages = state.get_packages_list()

    # Mark Remove Packages - Hard Constraints
    for package_name in package_names:
        version_vars = package_version_vars(repo, variables, package_name)

        if version_vars:
            opt.add(z3.Not(z3.Or(*version_vars)))

    # 1. Minimal Amount of Removed Manual Packages outside packages_name
    manually_installed_packages = [p for p, (v, m) in state.packages.items() if m]
    manual_packages_outside_removals = [
        package_name
        for package_name in manually_installed_packages
        if package_name not in package_names
    ]
    expr_installed_removed = count_unselected_packages(
        repo,
        variables,
        manual_packages_outside_removals,
    )

    # 2. Minimal Amount of Version Changes
    expr_changed = count_version_changes(repo, variables, installed_packages)

    # 3. Minimal Amount of new package
    installed_names = {package_name for package_name, _ in installed_packages}
    new_package_names = [
        package_name for package_name in repo.packages if package_name not in installed_names
    ]
    expr_added = count_selected_packages(repo, variables, new_package_names)

    # 4. Minimal Amount of Delete Packages
    if autoremove:
        expr_removed = count_selected_packages(repo, variables, repo.packages)
    else:
        expr_removed = count_unselected_packages(repo, variables, installed_names)

    opt.set(priority="lex")
    opt.minimize(expr_installed_removed)
    opt.minimize(expr_changed)
    opt.minimize(expr_added)
    opt.minimize(expr_removed)

    if opt.check() != z3.sat:
        raise RequestError("", "no solution for the given requests")

    model = opt.model()
    installed = [
        (package, version)
        for (package, version), var in variables.items()
        if z3.is_true(model.eval(var))
    ]

    initial_manual_flags = {
        name: manual for name, (_, manual) in state.packages.items()
    }
    state_dict = {}
    for name, version in installed:
        is_manual = initial_manual_flags.get(name, False)
        state_dict[name] = (parse_version(version), is_manual)

    final_state = State(packages=state_dict)

    return final_state
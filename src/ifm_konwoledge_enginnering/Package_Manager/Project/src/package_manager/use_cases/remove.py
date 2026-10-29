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
    removed_installed_terms = []
    for package_name in manually_installed_packages:

        if package_name in package_names:
            continue

        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        removed_installed_terms.append(z3.If(selected_any, 0, 1))

    expr_installed_removed = z3.Sum(removed_installed_terms) if removed_installed_terms else z3.IntVal(0)

    # 2. Minimal Amount of Version Changes
    changed_terms = []
    for package_name, old_version in installed_packages:
        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        old_version_selected = variables[(package_name, old_version)]
        changed_and_retained = z3.And(selected_any, z3.Not(z3.Or(old_version_selected)))
        changed_terms.append(z3.If(changed_and_retained, 1, 0))

    expr_changed = z3.Sum(changed_terms) if changed_terms else z3.IntVal(0)

    # 3. Minimal Amount of new package
    added_terms = []
    for package_name, _ in repo.packages.items():
        if package_name in [p for (p, _) in installed_packages]:
            continue

        version_vars = package_version_vars(repo, variables, package_name)
        selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
        added_terms.append(z3.If(selected_any, 1, 0))

    expr_added = z3.Sum(added_terms) if added_terms else z3.IntVal(0)

    # 4. Minimal Amount of Delete Packages
    if autoremove:
        removed_terms = []
        for package_name, _ in repo.packages.items():
            version_vars = package_version_vars(repo, variables, package_name)
            selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
            removed_terms.append(z3.If(selected_any, 1, 0))
        expr_removed = z3.Sum(removed_terms) if removed_terms else z3.IntVal(0)
    else:
        removed_terms = []
        for package_name, _ in installed_packages:
            version_vars = package_version_vars(repo, variables, package_name)
            selected_any = z3.Or(*version_vars) if version_vars else z3.BoolVal(False)
            removed_terms.append(z3.If(selected_any, 0, 1))
        expr_removed = z3.Sum(removed_terms) if removed_terms else z3.IntVal(0)

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
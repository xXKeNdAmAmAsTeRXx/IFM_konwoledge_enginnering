"""Reusable Z3 objective-expression builders for package-manager use cases."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import z3

from package_manager.domain.model import Repository
from package_manager.infrastructure.solver.knowledge_base import package_version_vars


def package_selected(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    package_name: str,
) -> z3.ExprRef:
    """Return an expression that is true when any version of a package is selected."""
    version_vars = package_version_vars(repo, variables, package_name)
    return z3.Or(*version_vars) if version_vars else z3.BoolVal(False)


def count_selected_packages(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    package_names: Iterable[str],
) -> z3.ExprRef:
    """Count how many of the supplied packages are selected in a result."""
    terms = [
        z3.If(package_selected(repo, variables, package_name), 1, 0)
        for package_name in package_names
    ]
    return z3.Sum(terms) if terms else z3.IntVal(0)


def count_unselected_packages(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    package_names: Iterable[str],
) -> z3.ExprRef:
    """Count how many of the supplied packages are not selected in a result."""
    terms = [
        z3.If(package_selected(repo, variables, package_name), 0, 1)
        for package_name in package_names
    ]
    return z3.Sum(terms) if terms else z3.IntVal(0)


def count_version_changes(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    initial_versions: Iterable[Tuple[str, str]],
) -> z3.ExprRef:
    """Count initially installed packages that remain installed with a changed version."""
    terms = []
    for package_name, old_version in initial_versions:
        selected_any = package_selected(repo, variables, package_name)
        old_version_selected = variables[(package_name, old_version)]
        changed_and_retained = z3.And(selected_any, z3.Not(old_version_selected))
        terms.append(z3.If(changed_and_retained, 1, 0))
    return z3.Sum(terms) if terms else z3.IntVal(0)


def obsolescence_cost(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    package_versions: Iterable[Tuple[str, str, int]],
) -> z3.ExprRef:
    """Sum version ranks for selected packages."""
    terms = [
        rank * z3.If(variables[(package_name, version)], 1, 0)
        for package_name, version, rank in package_versions
    ]
    return z3.Sum(terms) if terms else z3.IntVal(0)
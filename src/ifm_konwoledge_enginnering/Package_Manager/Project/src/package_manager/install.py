"""Installation into an empty environment (Task 4.3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Any, Dict

import z3
from z3 import BoolRef

from .errors import RequestError, InvalidInitialStateError
from .kb import build_knowledge_base, encode_requirement
from .model import Repository, State, Requirement
from .versioning import parse_requirement, parse_version


@dataclass
class InstallRequest:
    repo: Repository
    requests: list[Requirement]
    state: State | None
    requested_packages: set[str]
    obsolescence: dict[tuple[str, str], int]
def parse_install_request(repo, request_strings, state=None) -> InstallRequest:
    pass

def build_objectives_empty(request) -> list[z3.ExprRef]:
    pass

def build_objectives_state(request) -> list[z3.ExprRef]:
    pass

def solve_install(request) -> list[tuple[str, str]]:
    pass

from dataclasses import dataclass
from typing import Any

@dataclass
class Request:
    repository: Any = None
    requested_packages: list[str] = None

    def __post_init__(self):
        if self.requested_packages is None:
            self.requested_packages = []


def _calculate_obsolesce_dict(repo, variables):
    # TODO: implement
    raise NotImplementedError


def _objectives_for_empty_state(repo, request_strings):
    # TODO: implement
    raise NotImplementedError


def _objectives_for_not_empty_state(repo, initial_state, request_strings):
    # TODO: implement
    raise NotImplementedError


def install(
    repo: Repository,
    request_strings: List[str],
    initialState: State | None = None,
    print_axioms: bool = False,
) -> State:

    # Validate State
    if initialState is not None:
        if verify(repo, initialState.get_packages_list()):
            raise InvalidInitialStateError()

    requests = [parse_requirement(req) for req in request_strings]
    variables, opt, axioms = build_knowledge_base(repo, print_axioms=print_axioms)

    #Add state to optimizer
    apply_state(opt, repo, variables, initialState)


    for req in requests:
        opt.add(encode_requirement(req, repo, variables))

    # Optimization Objectives

    if initialState is None:
        # 4.3 Objectives
        obsolescence = {}
        for package_name in repo.packages:
            for index, version in enumerate(repo.versions_of(package_name)):
                obsolescence[(package_name, str(version))] = index

        requested_pkgs = {atom.package for req in requests for atom in req.alternatives}

        requested_terms = [
            obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
            for (p, v) in variables
            if p in requested_pkgs
        ]
        expr_requested = z3.Sum(requested_terms) if requested_terms else z3.IntVal(0)

        count_terms = [z3.If(v, 1, 0) for v in variables.values()]
        expr_count = z3.Sum(count_terms) if count_terms else z3.IntVal(0)

        other_terms = [
            obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
            for (p, v) in variables
            if p not in requested_pkgs
        ]
        expr_other = z3.Sum(other_terms) if other_terms else z3.IntVal(0)

        opt.set(priority="lex")
        opt.minimize(expr_requested)
        opt.minimize(expr_count)
        opt.minimize(expr_other)

    else:
        old_installed = initialState.get_packages_list()
        old_versions = {name: version for name, version in old_installed}
        requested_pkgs = {atom.package for req in requests for atom in req.alternatives}

        obsolescence = {}
        for package_name in repo.packages:
            for index, version in enumerate(repo.versions_of(package_name)):
                obsolescence[(package_name, str(version))] = index

        # Removed Packages
        removed_terms = []
        for name, version in old_installed:
            versions = parse_version(version)
            if versions:
                removed_terms.append(z3.If(z3.Or(versions), 0, 1))
        expr_removed = z3.Sum(removed_terms) if removed_terms else z3.IntVal(0)

        # Changed version
        changed_terms = []
        for name, version in old_installed:
            old_var = variables[(name, version)]
            versions = [variables[(name, str(v))] for v in repo.versions_of(name)]
            if versions:
                changed_terms.append(
                    z3.If(z3.And(z3.Or(versions), z3.Not(old_var)), 1, 0)
                )
        expr_changed = z3.Sum(changed_terms) if changed_terms else z3.IntVal(0)

        # new packages obsolesce
        requested_new_terms = []
        for (p, v) in variables:
            if p in requested_pkgs and p not in old_versions:
                requested_new_terms.append(
                    obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
                )
        expr_requested = (
            z3.Sum(requested_new_terms) if requested_new_terms else z3.IntVal(0)
        )

        # New Requested Obsolesce
        requested_new_terms = []
        for (p, v) in variables:
            if p in requested_pkgs and p not in old_versions:
                requested_new_terms.append(
                    obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
                )
        expr_requested_new = (
            z3.Sum(requested_new_terms) if requested_new_terms else z3.IntVal(0)
        )


        # New Packages count
        new_count_terms = []
        for name in repo.packages:
            if name not in old_versions:
                versions = [variables[(name, str(v))] for v in repo.versions_of(name)]
                if versions:
                    new_count_terms.append(z3.If(z3.Or(versions), 1, 0))
        expr_new_count = z3.Sum(new_count_terms) if new_count_terms else z3.IntVal(0)

        # New Packages Obsolence
        other_new_terms = []
        for (p, v) in variables:
            if p not in old_versions and p not in requested_pkgs:
                other_new_terms.append(
                    obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
                )
        expr_other_new = z3.Sum(other_new_terms) if other_new_terms else z3.IntVal(0)

        opt.set(priority="lex")
        opt.minimize(expr_removed)
        opt.minimize(expr_changed)
        opt.minimize(expr_requested_new)
        opt.minimize(expr_new_count)
        opt.minimize(expr_other_new)


    if opt.check() != z3.sat:
        raise RequestError("", "no solution for the given requests")

    model = opt.model()
    installed = [
        (package, version)
        for (package, version), var in variables.items()
        if z3.is_true(model.eval(var))
    ]

    raise NotImplementedError

"""Z3 knowledge base construction (Task 4.2)."""

from __future__ import annotations

from typing import Dict, Tuple

import z3
from .model import Repository, Atom, Requirement


def build_variables(repo: Repository) -> Dict[Tuple[str, str], z3.BoolRef]:
    """Build a dictionary mapping packages names and versions to boolean values."""
    package_bools = {}
    for package in repo.packages.values():
        name = package.name
        for version in package.versions:
            package_bools[(name, str(version))] = z3.Bool(f"{name}=={version}")

    return package_bools

def encode_constraint(
    atom: Atom,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> z3.ExprRef:

    versions = repo.versions_of(atom.package)
    matching = []
    for version in versions:
        if atom.matches_version(version):
            matching.append(variables[(atom.package, str(version))])

    return z3.Or(*matching) if matching else z3.BoolVal(False)

def encode_requirement(
    req: Requirement,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> z3.ExprRef:

    alternatives = [encode_constraint(alt, repo, variables) for alt in req.alternatives]
    return z3.Or(*alternatives) if alternatives else z3.BoolVal(False)


def add_axioms(
    opt: z3.Optimize,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> None:
    """
    Returns None as it motives opt
    """
    # TODO: A1 at most one version per package
    # TODO: A2 dependencies via Implies
    # TODO: A3 conflicts via Implies(..., Not(...))
    # TODO: attach readable labels with assert_and_track

    #A1: one version per package
    for package in repo.packages.values():
        versions = [variables[(package.name, str(version))] for version in package.versions]

        if versions:
            label = z3.Bool(f"at most one package of {package.name}")
            opt.assert_and_track(z3.AtMost(*versions, 1), label)

    #A2: Dependencies (Imply)
    for package in repo.packages.values():
        for version, info in package.versions.items():
            var = variables[(package.name, str(version))]
            for requirement in info.requirements:
                requirement_encoded = encode_requirement(requirement, repo, variables)
                label = z3.Bool(f"Package {package.name} requires {requirement}")
                opt.assert_and_track(z3.Implies(var, requirement_encoded), label)

    #A3: Conflicts (Imply)



    raise NotImplementedError


def build_knowledge_base(repo: Repository):
    # TODO: build variables
    # TODO: create z3.Optimize()
    # TODO: set priority="lex"
    # TODO: add axioms
    # TODO: return variables, opt
    raise NotImplementedError

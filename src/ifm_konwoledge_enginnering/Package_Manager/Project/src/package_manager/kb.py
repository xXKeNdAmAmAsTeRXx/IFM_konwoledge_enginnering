"""Z3 knowledge base construction (Task 4.2)."""

from __future__ import annotations

from typing import Dict, Tuple

import z3
from .model import Repository, Atom, Requirement, Package


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
    """
    Create a list (logical or statement) of packages that match given atom constraints.
    """

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
    """
    Create a list of packages that match requirements including all alternatives.
    """

    alternatives = [encode_constraint(alt, repo, variables) for alt in req.alternatives]
    return z3.Or(*alternatives) if alternatives else z3.BoolVal(False)


def add_axioms(
    opt: z3.Optimize,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> list:
    """
    Mapping dependencies between packages by using three axioms (A1, A2, A3).
    Returns a list of (label, formula) pairs.
    """
    axioms = []

    #A1: one version per package
    for package in repo.packages.values():
        versions = [variables[(package.name, str(version))] for version in package.versions]

        if versions:
            label = z3.Bool(f"at most one package of {package.name}")
            formula = z3.AtMost(*versions, 1)
            opt.assert_and_track(formula, label)
            axioms.append((str(label), formula))

    #A2: Dependencies (Imply)
    for package in repo.packages.values():
        for version, info in package.versions.items():
            var = variables[(package.name, str(version))]
            for requirement in info.requires:
                requirement_encoded = encode_requirement(requirement, repo, variables)
                label = z3.Bool(f"Package {package.name} requires {requirement}")
                formula = z3.Implies(var, requirement_encoded)
                opt.assert_and_track(formula, label)
                axioms.append((str(label), formula))

    #A3: Conflicts (Imply)
    for package in repo.packages.values():
        for version, info in package.versions.items():
            var = variables[(package.name, str(version))]
            for req in info.conflicts:
                for atom in req.alternatives:
                    matching = [
                        variables[(atom.package, str(v))]
                        for v in repo.versions_of(atom.package)
                        if atom.matches_version(v)
                    ]
                    if matching:
                        label = z3.Bool(
                            f"{package.name}=={version} conflicts with {atom.package}"
                        )
                        formula = z3.Implies(var, z3.Not(z3.Or(matching)))
                        opt.assert_and_track(formula, label)
                        axioms.append((str(label), formula))

    return axioms


def build_knowledge_base(repo: Repository, print_axioms: bool = False):
    """
    Build packages knowledge base,which means map all dependencies between packages into logical condictions.
    """
    variables = build_variables(repo)
    opt = z3.Optimize()
    opt.set(priority="lex")

    axioms = add_axioms(opt, repo, variables)

    if print_axioms:
        print_example_axioms(axioms)

    return variables, opt, axioms




def print_example_axioms(axioms, limit=25):
    for label, formula in axioms[:limit]:
        print(f"{label}: {formula}")

"""Z3 knowledge base construction (Task 4.2)."""

from __future__ import annotations

from typing import Dict, Tuple

import z3
from package_manager.domain.model import Repository, Atom, Requirement


def package_version_vars(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
    package_name: str,
) -> list[z3.BoolRef]:
    """Return Z3 variables for every version of a package in the repository."""
    return [
        variables[(package_name, str(version))]
        for version in repo.versions_of(package_name)
    ]


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


def _format_atom(atom: Atom) -> str:
    """Format a requirement atom without exposing its dataclass representation."""
    constraints = " ".join(
        f"{constraint.op}{constraint.version}" for constraint in atom.constraints
    )
    return f"{atom.package} {constraints}".rstrip()


def _format_requirement(req: Requirement) -> str:
    """Format an OR requirement in the syntax accepted by the request parser."""
    return " | ".join(_format_atom(atom) for atom in req.alternatives)


def build_axioms(
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> list[tuple[str, z3.ExprRef]]:
    """
    Generate repository axioms (A1, A2, A3) without asserting them to a solver.

    Each result is a (human-readable label, formula) pair.
    """
    axioms = []

    # A1: one version per package.
    for package in repo.packages.values():
        versions = [variables[(package.name, str(version))] for version in package.versions]

        if versions:
            label = f"at most one package of {package.name}"
            formula = z3.AtMost(*versions, 1)
            axioms.append((label, formula))

    # A2: dependencies.
    for package in repo.packages.values():
        for version, info in package.versions.items():
            var = variables[(package.name, str(version))]
            for requirement in info.requires:
                requirement_encoded = encode_requirement(requirement, repo, variables)
                label = (
                    f"Package {package.name}=={version} requires "
                    f"{_format_requirement(requirement)}"
                )
                formula = z3.Implies(var, requirement_encoded)
                axioms.append((label, formula))

    # A3: conflicts.
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
                        label = (
                            f"{package.name}=={version} conflicts with "
                            f"{_format_atom(atom)}"
                        )
                        formula = z3.Implies(var, z3.Not(z3.Or(matching)))
                        axioms.append((label, formula))

    return axioms


def add_axioms(
    opt: z3.Optimize,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> list[tuple[str, z3.ExprRef]]:
    """Generate and assert repository axioms, tracking each one uniquely."""
    axioms = build_axioms(repo, variables)
    for _, formula in axioms:
        opt.assert_and_track(formula, z3.FreshBool("axiom_track"))
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

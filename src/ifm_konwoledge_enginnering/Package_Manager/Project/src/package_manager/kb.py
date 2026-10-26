"""Z3 knowledge base construction (Task 4.2)."""

from __future__ import annotations

from typing import Dict, Tuple

import z3

from .model import Repository, Atom, Requirement


def build_variables(repo: Repository) -> Dict[Tuple[str, str], z3.BoolRef]:
    # TODO: create one Bool per (package, version)
    # TODO: label it f"{package}=={version}"
    raise NotImplementedError


def encode_constraint(atom: Atom, repo: Repository) -> z3.ExprRef:
    # TODO: OR of all versions matching atom.constraints
    # TODO: return z3.Or() when no matching versions
    raise NotImplementedError


def encode_requirement(req: Requirement, repo: Repository) -> z3.ExprRef:
    # TODO: OR of encode_constraint for each alternative
    # TODO: return z3.Or() when no alternatives
    raise NotImplementedError


def add_axioms(
    opt: z3.Optimize,
    repo: Repository,
    variables: Dict[Tuple[str, str], z3.BoolRef],
) -> None:
    # TODO: A1 at most one version per package
    # TODO: A2 dependencies via Implies
    # TODO: A3 conflicts via Implies(..., Not(...))
    # TODO: attach readable labels with assert_and_track
    raise NotImplementedError


def build_knowledge_base(repo: Repository):
    # TODO: build variables
    # TODO: create z3.Optimize()
    # TODO: set priority="lex"
    # TODO: add axioms
    # TODO: return variables, opt
    raise NotImplementedError

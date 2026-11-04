from pathlib import Path

import z3
import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.infrastructure.solver.knowledge_base import build_knowledge_base
from package_manager.infrastructure.state import parse_state, apply_state
from package_manager.domain.versioning import parse_version
from package_manager.domain.model import State


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parents[2]
    return load_repository(base / "examples" / "repo_example.json")


def test_apply_state_empty(repo):
    variables, opt, _ = build_knowledge_base(repo)
    apply_state(opt, repo, variables, State())
    for var in variables.values():
        opt.push()
        opt.add(var)
        assert opt.check() == z3.unsat
        opt.pop()


def test_apply_state_single(repo):
    variables, opt, _ = build_knowledge_base(repo)
    state = State(packages={"lib": (parse_version("1.0"), False)})
    apply_state(opt, repo, variables, state)
    assert opt.check() == z3.sat
    model = opt.model()
    assert z3.is_true(model.eval(variables[("lib", "1.0")]))


def test_apply_state_conflict(repo):
    variables, opt, _ = build_knowledge_base(repo)
    state = State(packages={"legacy": (parse_version("1.0"), False)})
    apply_state(opt, repo, variables, state)
    opt.add(variables[("util", "2.0")])
    assert opt.check() == z3.unsat

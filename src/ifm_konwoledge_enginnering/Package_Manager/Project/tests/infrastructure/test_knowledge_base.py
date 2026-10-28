from pathlib import Path

import z3
import pytest

from package_manager.infrastructure.parsing import load_repository
from package_manager.domain.versioning import parse_requirement
from package_manager.infrastructure.solver.knowledge_base import (
    build_variables,
    encode_constraint,
    encode_requirement,
    add_axioms,
    build_knowledge_base,
    print_example_axioms,
)


@pytest.fixture
def repo():
    base = Path(__file__).resolve().parents[2]
    return load_repository(base / "examples" / "repo_example.json")


def test_build_variables_count(repo):
    variables = build_variables(repo)
    expected = sum(len(package.versions) for package in repo.packages.values())
    assert len(variables) == expected


def test_build_variables_keys(repo):
    variables = build_variables(repo)
    for key in variables:
        assert isinstance(key, tuple)
        assert len(key) == 2
        assert all(isinstance(part, str) for part in key)


def test_build_variables_values(repo):
    variables = build_variables(repo)
    for var in variables.values():
        assert isinstance(var, z3.BoolRef)


def test_build_variables_names(repo):
    variables = build_variables(repo)
    for (package, version), var in variables.items():
        assert str(var) == f"{package}=={version}"


def test_encode_constraint_empty(repo):
    variables = build_variables(repo)
    atom = parse_requirement("lib").alternatives[0]
    formula = encode_constraint(atom, repo, variables)
    solver = z3.Solver()
    solver.add(formula)
    assert solver.check() == z3.sat


def test_encode_constraint_single(repo):
    variables = build_variables(repo)
    atom = parse_requirement("lib >=2.0").alternatives[0]
    formula = encode_constraint(atom, repo, variables)

    solver = z3.Solver()
    solver.add(variables[("lib", "2.0")])
    solver.add(formula)
    assert solver.check() == z3.sat

    solver2 = z3.Solver()
    solver2.add(variables[("lib", "1.0")])
    solver2.add(z3.Not(variables[("lib", "2.0")]))
    solver2.add(formula)
    assert solver2.check() == z3.unsat


def test_encode_constraint_no_match(repo):
    variables = build_variables(repo)
    atom = parse_requirement("lib >=999").alternatives[0]
    formula = encode_constraint(atom, repo, variables)
    solver = z3.Solver()
    solver.add(formula)
    assert solver.check() == z3.unsat


def test_encode_requirement_single(repo):
    variables = build_variables(repo)
    req = parse_requirement("lib >=2.0")
    formula = encode_requirement(req, repo, variables)
    variables = build_variables(repo)

    solver = z3.Solver()
    solver.add(variables[("lib", "2.0")])
    solver.add(formula)
    assert solver.check() == z3.sat


def test_encode_requirement_alternatives(repo):
    variables = build_variables(repo)
    req = parse_requirement("json-fast | json-slow >=1.0")
    formula = encode_requirement(req, repo, variables)
    solver = z3.Solver()
    solver.add(formula)
    assert solver.check() == z3.sat


def test_add_axioms_at_most_one(repo):
    variables, opt, axioms = build_knowledge_base(repo)
    lib_versions = [variables[("lib", str(v))] for v in repo.packages["lib"].versions]

    opt.push()
    opt.add(lib_versions[0])
    opt.add(lib_versions[1])
    assert opt.check() == z3.unsat
    opt.pop()


def test_add_axioms_dependency(repo):
    variables, opt, axioms = build_knowledge_base(repo)

    opt.push()
    opt.add(variables[("app", "2.0")])
    opt.add(variables[("lib", "1.0")])
    assert opt.check() == z3.unsat
    opt.pop()


def test_add_axioms_conflict(repo):
    variables, opt, axioms = build_knowledge_base(repo)

    opt.push()
    opt.add(variables[("legacy", "1.0")])
    opt.add(variables[("util", "2.0")])
    assert opt.check() == z3.unsat
    opt.pop()


def test_build_knowledge_base_returns(repo):
    result = build_knowledge_base(repo)
    assert isinstance(result, tuple)
    assert len(result) == 3
    variables, opt, axioms = result
    assert isinstance(variables, dict)
    assert isinstance(opt, z3.Optimize)


def test_build_knowledge_base_sat(repo):
    variables, opt, axioms = build_knowledge_base(repo)
    assert opt.check() == z3.sat


def test_print_example_axioms(capsys):
    repo = load_repository(str(Path(__file__).resolve().parents[2] / "examples" / "repo_example.json"))
    variables, opt, axioms = build_knowledge_base(repo)
    print_example_axioms(axioms, limit=2)
    captured = capsys.readouterr()
    assert "at most one package of" in captured.out
    assert ":" in captured.out


def test_build_knowledge_base_print_flag(capsys):
    repo = load_repository(str(Path(__file__).resolve().parents[2] / "examples" / "repo_example.json"))
    variables, opt, axioms = build_knowledge_base(repo, print_axioms=True)
    captured = capsys.readouterr()
    assert len(captured.out.strip().splitlines()) > 0

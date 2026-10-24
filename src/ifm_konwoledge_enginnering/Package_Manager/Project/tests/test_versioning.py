import pytest

from package_manager.versioning import (
    normalize_package_name,
    parse_version,
    parse_requirement,
)
from package_manager.model import Constraint


def test_normalize_package_name_equivalence():
    assert normalize_package_name("Foo_Bar") == "foo-bar"
    assert normalize_package_name("foo-bar") == "foo-bar"
    assert normalize_package_name("foo.bar") == "foo-bar"
    assert normalize_package_name("Foo.Bar_Baz") == "foo-bar-baz"


def test_normalize_package_name_invalid():
    with pytest.raises(ValueError):
        normalize_package_name("")
    with pytest.raises(ValueError):
        normalize_package_name("123bad?name")


def test_parse_version_ordering():
    v10 = parse_version("1.10")
    v9 = parse_version("1.9")
    assert v10 > v9
    assert parse_version("1.0") == parse_version("1.0.0")


def test_parse_version_invalid():
    with pytest.raises(ValueError):
        parse_version("not-a-version")
    with pytest.raises(ValueError):
        parse_version("")


def test_constraint_matches():
    c = Constraint(">=", parse_version("2.0"))
    assert c.matches(parse_version("2.0"))
    assert c.matches(parse_version("2.5"))
    assert not c.matches(parse_version("1.9"))

    c2 = Constraint("!=", parse_version("1.0"))
    assert c2.matches(parse_version("2.0"))
    assert not c2.matches(parse_version("1.0"))


def test_parse_requirement_simple():
    req = parse_requirement("lib >=2.0 <3.0")
    assert len(req.alternatives) == 1
    atom = req.alternatives[0]
    assert atom.package == "lib"
    assert len(atom.constraints) == 2
    assert atom.constraints[0].op == ">="
    assert atom.constraints[1].op == "<"


def test_parse_requirement_no_constraints():
    req = parse_requirement("util")
    assert len(req.alternatives) == 1
    assert req.alternatives[0].package == "util"
    assert req.alternatives[0].constraints == []


def test_parse_requirement_alternatives():
    req = parse_requirement("json-fast | json-slow >=1.0")
    assert len(req.alternatives) == 2
    assert req.alternatives[0].package == "json-fast"
    assert req.alternatives[0].constraints == []
    assert req.alternatives[1].package == "json-slow"
    assert req.alternatives[1].constraints[0].op == ">="


def test_parse_requirement_commas():
    req = parse_requirement("lib >=1.0, <2.0")
    atom = req.alternatives[0]
    assert len(atom.constraints) == 2


def test_parse_requirement_no_spaces():
    req = parse_requirement("lib>=2.0")
    atom = req.alternatives[0]
    assert atom.constraints[0].op == ">="
    assert str(atom.constraints[0].version) == "2.0"


def test_parse_requirement_invalid_operator():
    from package_manager.errors import RepoError

    with pytest.raises(RepoError):
        parse_requirement("lib ~= 2.0")


def test_parse_requirement_invalid_version():
    from package_manager.errors import RepoError

    with pytest.raises(RepoError):
        parse_requirement("lib >= not-a-version")


def test_parse_requirement_empty_alternative():
    from package_manager.errors import RepoError

    with pytest.raises(RepoError):
        parse_requirement("lib | ")


def test_parse_requirement_invalid_name():
    from package_manager.errors import RepoError

    with pytest.raises(RepoError):
        parse_requirement("bad?name")

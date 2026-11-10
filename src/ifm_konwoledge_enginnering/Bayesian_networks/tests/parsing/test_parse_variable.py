import copy

import pytest

from models.variable import Variable
from parsing.parse_variable import parse_variable, parse_variables_dict


def test_parse_variable_valid():
    var_dict = {
        "state": "present",
        "description": "A test variable",
        "states": ["active", "inactive"],
    }

    variable = parse_variable("var1", var_dict)

    assert isinstance(variable, Variable)
    assert variable.name == "var1"
    assert variable.description == "A test variable"
    assert variable.states == ["active", "inactive"]


def test_parse_variable_default_description():
    var_dict = {"state": "present", "states": ["yes", "no"]}

    variable = parse_variable("var1", var_dict)

    assert variable.description == "not description provided"


def test_parse_variable_accepts_real_fixture_shape_without_state_field():
    var_dict = {"description": "course difficulty", "states": ["Easy", "Hard"]}

    variable = parse_variable("D", var_dict)

    assert variable.name == "D"
    assert variable.description == "course difficulty"
    assert variable.states == ["Easy", "Hard"]


def test_parse_variable_preserves_state_order():
    states = ["third", "first", "second"]

    variable = parse_variable("ordered", {"state": "present", "states": states})

    assert variable.states == states


def test_parse_variable_missing_states_key():
    with pytest.raises(ValueError, match="var1"):
        parse_variable("var1", {"state": "present", "description": "missing states"})


@pytest.mark.parametrize("states", ["not_a_list", None, 42])
def test_parse_variable_states_not_list(states):
    var_dict = {"state": "present", "states": states}

    with pytest.raises(ValueError, match="Invalid states"):
        parse_variable("var1", var_dict)


@pytest.mark.parametrize("state", [123, None, ["nested"]])
def test_parse_variable_invalid_state_element(state):
    var_dict = {"state": "present", "states": ["valid", state]}

    with pytest.raises(ValueError, match="Invalid state"):
        parse_variable("var1", var_dict)


@pytest.mark.parametrize("states", [[], ["only_one"]])
def test_parse_variable_too_few_states(states):
    var_dict = {"state": "present", "states": states}

    with pytest.raises(ValueError, match="at least two states"):
        parse_variable("var1", var_dict)


def test_parse_variable_rejects_duplicate_states():
    var_dict = {"state": "present", "states": ["same", "same"]}

    with pytest.raises(ValueError):
        parse_variable("var1", var_dict)


def test_parse_variable_does_not_mutate_input():
    var_dict = {"state": "present", "description": "desc", "states": ["a", "b"]}
    original = copy.deepcopy(var_dict)

    parse_variable("var1", var_dict)

    assert var_dict == original


def test_parse_variables_dict_empty():
    assert parse_variables_dict({}) == {}


def test_parse_variables_dict_parses_all_variables():
    not_parsed = {
        "A": {"state": "present", "description": "variable A", "states": ["a0", "a1"]},
        "B": {"state": "present", "description": "variable B", "states": ["b0", "b1"]},
        "C": {"state": "present", "description": "variable C", "states": ["c0", "c1"]},
    }

    parsed = parse_variables_dict(not_parsed)

    assert list(parsed.keys()) == ["A", "B", "C"]
    assert all(isinstance(variable, Variable) for variable in parsed.values())
    assert parsed["A"].name == "A"
    assert parsed["A"].states == ["a0", "a1"]
    assert parsed["B"].name == "B"
    assert parsed["C"].name == "C"


def test_parse_variables_dict_preserves_order():
    not_parsed = {
        "Z": {"state": "present", "states": ["z0", "z1"]},
        "A": {"state": "present", "states": ["a0", "a1"]},
        "M": {"state": "present", "states": ["m0", "m1"]},
    }

    parsed = parse_variables_dict(not_parsed)

    assert list(parsed.keys()) == ["Z", "A", "M"]


def test_parse_variables_dict_does_not_mutate_input():
    not_parsed = {
        "A": {"state": "present", "description": "variable A", "states": ["a0", "a1"]},
        "B": {"state": "present", "description": "variable B", "states": ["b0", "b1"]},
    }
    original = copy.deepcopy(not_parsed)

    parse_variables_dict(not_parsed)

    assert not_parsed == original


def test_parse_variables_dict_propagates_error_with_variable_name():
    not_parsed = {
        "GOOD": {"state": "present", "states": ["g0", "g1"]},
        "BROKEN": {"state": "present", "description": "missing states"},
    }

    with pytest.raises(ValueError, match="BROKEN"):
        parse_variables_dict(not_parsed)


def test_parse_variables_dict_accepts_variables_without_state_field():
    not_parsed = {
        "D": {"description": "course difficulty", "states": ["Easy", "Hard"]},
        "I": {"description": "student intelligence", "states": ["Dumb", "Intelligent"]},
    }

    parsed = parse_variables_dict(not_parsed)

    assert parsed["D"].name == "D"
    assert parsed["I"].name == "I"

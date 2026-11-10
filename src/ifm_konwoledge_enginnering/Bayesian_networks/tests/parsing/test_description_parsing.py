import json
from unittest.mock import mock_open, patch
import pytest

from models.variable import Variable
from parsing.description_parsing import parse_edge, parse_tiers, description_parser
from parsing.parse_variable import parse_variable

def test_parse_variable_valid():
    var_dict = {"state": "present", "states": ["active", "inactive"], "description": "A test variable"}
    var = parse_variable("var1", var_dict)
    assert var.name == "var1"
    assert var.description == "A test variable"
    assert var.states == ["active", "inactive"]


def test_parse_variable_default_description():
    var_dict = {"state": "present", "states": ["yes", "no"]}
    var = parse_variable("var1", var_dict)
    assert var.description == "not description provided"


def test_parse_variable_missing_state():
    # Note: Code checks `variable_dict.get('state') is None`
    var_dict = {"states": ["yes", "no"]}  # 'state' key is missing
    with pytest.raises(ValueError, match="Missing required field: var1"):
        parse_variable("var1", var_dict)


def test_parse_variable_states_not_list():
    var_dict = {"state": "present", "states": "not_a_list"}
    with pytest.raises(ValueError, match="Invalid states:"):
        parse_variable("var1", var_dict)


def test_parse_variable_invalid_state_element():
    var_dict = {"state": "present", "states": ["valid", 123]}
    with pytest.raises(ValueError, match="Invalid state: 123"):
        parse_variable("var1", var_dict)


def test_parse_variable_too_few_states():
    var_dict = {"state": "present", "states": ["only_one"]}
    with pytest.raises(ValueError, match="Variables should contain at least two states"):
        parse_variable("var1", var_dict)


def test_parse_edge_valid():
    vars_dict = {
        "A": Variable(name="A", description="", states=["0", "1"]),
        "B": Variable(name="B", description="", states=["0", "1"]),
    }
    v1, v2 = parse_edge(["A", "B"], vars_dict)
    assert v1.name == "A"
    assert v2.name == "B"


def test_parse_edge_invalid_length():
    vars_dict = {}
    with pytest.raises(ValueError, match="Invalid edge:"):
        parse_edge(["A"], vars_dict)
    with pytest.raises(ValueError, match="Invalid edge:"):
        parse_edge(["A", "B", "C"], vars_dict)


def test_parse_tiers_valid():
    v1 = Variable(name="A", description="", states=["0", "1"])
    v2 = Variable(name="B", description="", states=["0", "1"])
    vars_dict = {"A": v1, "B": v2}

    tiers = parse_tiers([["A"], ["B"]], vars_dict)
    assert tiers == [[v1], [v2]]


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
    "variables": {
        "A": {"state": "present", "states": ["0", "1"]},
        "B": {"state": "present", "states": ["0", "1"]}
    },
    "expert_edges": [["A", "B"]],
    "required_edges": [],
    "forbidden_edges": [],
    "tiers": [["A", "B"]]
}))
def test_description_parser_valid(mock_file):
    graph_data = description_parser("dummy_path.json")
    assert len(graph_data.exper_edges) == 1
    assert graph_data.exper_edges[0][0].name == "A"
    assert graph_data.exper_edges[0][1].name == "B"
    assert len(graph_data.tiers) == 1
    assert len(graph_data.tiers[0]) == 2


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
    "variables": {
        "A": {"state": "present", "states": ["0", "1"]}
    },
    "expert_edges": [],
    "required_edges": [],
    "forbidden_edges": []
    # Missing "tiers" required field
}))
def test_description_parser_missing_required_field(mock_file):
    with pytest.raises(ValueError, match="Missing required field: tiers"):
        description_parser("dummy_path.json")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
    "variables": {},
    "expert_edges": [],
    "required_edges": [],
    "forbidden_edges": [],
    "tiers": [],
    "unknown_extra_field": []
}))
def test_description_parser_invalid_field(mock_file):
    with pytest.raises(ValueError, match="Field unknown_extra_field is invalid"):
        description_parser("dummy_path.json")

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
    "variables": {
        "A": {"state": "present", "states": ["0", "1"]},
        "B": {"state": "present", "states": ["0", "1"]},
        "C": {"state": "present", "states": ["0", "1"]}
    },
    "expert_edges": [
        ["A", "B"],
        ["B", "C"],
        ["C", "A"]  # Creates a cycle: A -> B -> C -> A
    ],
    "required_edges": [],
    "forbidden_edges": [],
    "tiers": [["A", "B", "C"]]
}))
def test_description_parser_cycle_in_expert_edges(mock_file):
    with pytest.raises(ValueError, match="Cycle detected in expert_edges"):
        description_parser("dummy_path.json")
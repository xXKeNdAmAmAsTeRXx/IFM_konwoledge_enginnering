import copy
import json
from pathlib import Path

import pytest

from models.graph import GraphData
from models.variable import Variable
from parsing.description_parsing import (
    description_parser,
    parse_edge,
    parse_edges_list,
    parse_tiers,
)


def _write_json(path: Path, payload) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _write_text(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return str(path)


def _edge_names(edges):
    return [(left.name, right.name) for left, right in edges]


# parse_edge


def test_parse_edge_valid(variables_dict):
    left, right = parse_edge(["A", "B"], variables_dict)

    assert left is variables_dict["A"]
    assert right is variables_dict["B"]


@pytest.mark.parametrize("edge", [[], ["A"], ["A", "B", "C"]])
def test_parse_edge_invalid_length(edge, variables_dict):
    with pytest.raises(ValueError, match="Invalid edge"):
        parse_edge(edge, variables_dict)


@pytest.mark.parametrize(
    "edge, missing_name",
    [
        (["A", "Z"], "Z"),
        (["Z", "A"], "Z"),
        (["Z", "Y"], "Z"),
    ],
)
def test_parse_edge_unknown_variable(edge, missing_name, variables_dict):
    with pytest.raises(ValueError, match=missing_name):
        parse_edge(edge, variables_dict)


@pytest.mark.parametrize("edge", [None, "AB", 42])
def test_parse_edge_non_list_input(edge, variables_dict):
    with pytest.raises(ValueError):
        parse_edge(edge, variables_dict)


def test_parse_edge_accepts_self_edge(variables_dict):
    left, right = parse_edge(["A", "A"], variables_dict)

    assert left is right is variables_dict["A"]


def test_parse_edge_does_not_mutate_edge(variables_dict):
    edge = ["A", "B"]

    parse_edge(edge, variables_dict)

    assert edge == ["A", "B"]


# parse_edges_list


def test_parse_edges_list_empty(variables_dict):
    assert parse_edges_list([], variables_dict) == []


def test_parse_edges_list_valid(variables_dict):
    edge_list = [["A", "B"], ["B", "C"]]

    parsed = parse_edges_list(edge_list, variables_dict)

    assert _edge_names(parsed) == [("A", "B"), ("B", "C")]
    assert parsed[0][0] is variables_dict["A"]
    assert parsed[1][0] is variables_dict["B"]


def test_parse_edges_list_returns_new_list(variables_dict):
    edge_list = [["A", "B"]]

    parsed = parse_edges_list(edge_list, variables_dict)

    assert parsed is not edge_list
    assert parsed[0] is not edge_list[0]


def test_parse_edges_list_does_not_mutate_input(variables_dict):
    edge_list = [["A", "B"], ["B", "C"]]
    original = copy.deepcopy(edge_list)

    parse_edges_list(edge_list, variables_dict)

    assert edge_list == original


def test_parse_edges_list_propagates_invalid_edge(variables_dict):
    with pytest.raises(ValueError, match="Invalid edge"):
        parse_edges_list([["A"]], variables_dict)


def test_parse_edges_list_propagates_unknown_variable(variables_dict):
    with pytest.raises(ValueError, match="Z"):
        parse_edges_list([["A", "Z"]], variables_dict)


# parse_tiers


def test_parse_tiers_empty(variables_dict):
    assert parse_tiers([], variables_dict) == []


def test_parse_tiers_valid(variables_dict):
    tiers = parse_tiers([["A"], ["B", "C"]], variables_dict)

    assert tiers == [[variables_dict["A"]], [variables_dict["B"], variables_dict["C"]]]
    assert tiers[0][0] is variables_dict["A"]
    assert tiers[1][1] is variables_dict["C"]


def test_parse_tiers_accepts_empty_tier(variables_dict):
    assert parse_tiers([[]], variables_dict) == [[]]


def test_parse_tiers_unknown_variable(variables_dict):
    with pytest.raises(ValueError, match="Z"):
        parse_tiers([["A", "Z"]], variables_dict)


def test_parse_tiers_does_not_mutate_input(variables_dict):
    tiers_list = [["A"], ["B", "C"]]
    original = copy.deepcopy(tiers_list)

    parse_tiers(tiers_list, variables_dict)

    assert tiers_list == original


# description_parser: file and JSON handling


def test_description_parser_valid(tmp_path, valid_description_payload):
    path = _write_json(tmp_path / "opis.json", valid_description_payload)

    graph = description_parser(path)

    assert isinstance(graph, GraphData)
    assert _edge_names(graph.exper_edges) == [("A", "B"), ("B", "C")]
    assert _edge_names(graph.required_edges) == [("A", "B")]
    assert _edge_names(graph.forbidden_edges) == [("C", "A")]
    assert [[variable.name for variable in tier] for tier in graph.tiers] == [["A"], ["B"], ["C"]]


def test_description_parser_meta_is_allowed_and_ignored(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["meta"] = {"anything": "goes here", "nested": {"value": 42}}
    path = _write_json(tmp_path / "opis.json", payload)

    graph = description_parser(path)

    assert isinstance(graph, GraphData)


@pytest.mark.parametrize(
    "field",
    ["variables", "expert_edges", "required_edges", "forbidden_edges", "tiers"],
)
def test_description_parser_missing_required_field(field, tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload.pop(field)
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match=field):
        description_parser(path)


def test_description_parser_unknown_top_level_field(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["unknown_extra_field"] = []
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="unknown_extra_field"):
        description_parser(path)


def test_description_parser_error_mentions_source_path(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["unknown_extra_field"] = []
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError) as error:
        description_parser(path)

    assert path in str(error.value)


def test_description_parser_malformed_json(tmp_path):
    path = _write_text(tmp_path / "opis.json", '{ "variables": ')

    with pytest.raises(ValueError):
        description_parser(path)


def test_description_parser_empty_file(tmp_path):
    path = _write_text(tmp_path / "opis.json", "")

    with pytest.raises(ValueError):
        description_parser(path)


def test_description_parser_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        description_parser(str(tmp_path / "does_not_exist.json"))


@pytest.mark.parametrize("payload", [[], 42, None, [{"variables": {}}]])
def test_description_parser_top_level_must_be_object(payload, tmp_path):
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError):
        description_parser(path)


def test_description_parser_accepts_json_string_containing_object(tmp_path, valid_description_payload):
    path = _write_text(
        tmp_path / "opis.json",
        json.dumps(json.dumps(valid_description_payload)),
    )

    graph = description_parser(path)

    assert isinstance(graph, GraphData)


def test_description_parser_rejects_json_string_containing_invalid_json(tmp_path):
    path = _write_text(tmp_path / "opis.json", json.dumps("not a json object"))

    with pytest.raises(ValueError, match="Invalid JSON"):
        description_parser(path)


# description_parser: schema shapes


@pytest.mark.parametrize(
    "field",
    ["variables", "expert_edges", "required_edges", "forbidden_edges", "tiers"],
)
def test_description_parser_field_has_wrong_shape(field, tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload[field] = 42
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError):
        description_parser(path)


# description_parser: variables


@pytest.mark.parametrize(
    "variable_payload",
    [
        {"description": "one state", "states": ["only"]},
        {"description": "duplicate states", "states": ["same", "same"]},
        {"description": "states not list", "states": "a,b"},
        {"description": "non-string state", "states": ["ok", 1]},
        {"description": "missing states"},
    ],
    ids=["one-state", "duplicate-state", "states-not-list", "non-string-state", "missing-states"],
)
def test_description_parser_rejects_invalid_variable(
    variable_payload, tmp_path, valid_description_payload
):
    payload = copy.deepcopy(valid_description_payload)
    payload["variables"]["BROKEN"] = variable_payload
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="BROKEN"):
        description_parser(path)


# description_parser: edges and tiers


def test_description_parser_rejects_cycle_in_expert_edges(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["expert_edges"] = [["A", "B"], ["B", "C"], ["C", "A"]]
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="Cycle detected in expert_edges"):
        description_parser(path)


@pytest.mark.parametrize("field", ["expert_edges", "required_edges", "forbidden_edges"])
def test_description_parser_rejects_invalid_edge_length(field, tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload[field] = [["A"]]
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="Invalid edge"):
        description_parser(path)


@pytest.mark.parametrize("field", ["expert_edges", "required_edges", "forbidden_edges"])
def test_description_parser_rejects_unknown_edge_variable(field, tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload[field] = [["A", "Z"]]
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="Z"):
        description_parser(path)


def test_description_parser_rejects_unknown_tier_variable(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["tiers"] = [["A", "Z"]]
    path = _write_json(tmp_path / "opis.json", payload)

    with pytest.raises(ValueError, match="Z"):
        description_parser(path)


def test_description_parser_accepts_empty_edge_lists_and_tiers(tmp_path, valid_description_payload):
    payload = copy.deepcopy(valid_description_payload)
    payload["expert_edges"] = []
    payload["required_edges"] = []
    payload["forbidden_edges"] = []
    payload["tiers"] = []
    path = _write_json(tmp_path / "opis.json", payload)

    graph = description_parser(path)

    assert graph.exper_edges == []
    assert graph.required_edges == []
    assert graph.forbidden_edges == []
    assert graph.tiers == []


# description_parser: output contract


def test_description_parser_reuses_variable_objects(tmp_path, valid_description_payload):
    path = _write_json(tmp_path / "opis.json", valid_description_payload)

    graph = description_parser(path)

    variable_from_edge = graph.exper_edges[0][0]
    variable_from_tier = graph.tiers[0][0]
    variable_from_required = graph.required_edges[0][0]

    assert variable_from_edge is variable_from_tier
    assert variable_from_edge is variable_from_required
    assert isinstance(variable_from_edge, Variable)

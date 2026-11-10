import json
import os
from typing import Any, List

from models.graph import GraphData
from models.variable import Variable
from parsing.parse_variable import parse_variables_dict
from parsing.util.check_for_cycles import check_for_cycles


def _validate_variable_name(name: Any, context: str, variables_dict: dict[str, Variable]) -> None:
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid variable name in {context}: {name!r}")

    if name not in variables_dict:
        raise ValueError(f"{context} references unknown variable: {name}")


def parse_edge(edge: List[str], variables_dict: dict[str, Variable]) -> tuple[str, str]:
    if not isinstance(edge, list):
        raise ValueError(f"Invalid edge format: {edge}")

    if len(edge) != 2:
        raise ValueError(f"Invalid edge: {edge}")

    for name in edge:
        _validate_variable_name(name, f"edge {edge}", variables_dict)

    return (edge[0], edge[1])


def parse_edges_list(
    edges_list: List[List[str]], variables_dict: dict[str, Variable]
) -> list[tuple[str, str]]:
    if not isinstance(edges_list, list):
        raise ValueError(f"Invalid edges format: {edges_list}")

    return [parse_edge(edge, variables_dict) for edge in edges_list]


def parse_tiers(
    tiers_list: List[List[str]], variables_dict: dict[str, Variable]
) -> list[List[str]]:
    if not isinstance(tiers_list, list):
        raise ValueError(f"Invalid tiers format: {tiers_list}")

    tiers = []
    for names in tiers_list:
        if not isinstance(names, list):
            raise ValueError(f"Invalid tier format: {names}")

        tier = []
        for name in names:
            _validate_variable_name(name, f"tier {names}", variables_dict)
            tier.append(name)

        tiers.append(tier)

    return tiers


def _validate_graph_references(graph: GraphData) -> None:
    referenced = [
        name
        for edge in (*graph.exper_edges, *graph.required_edges, *graph.forbidden_edges)
        for name in edge
    ]
    referenced.extend(name for tier in graph.tiers for name in tier)

    unknown = sorted({name for name in referenced if name not in graph.variables_dict})
    if unknown:
        raise ValueError(f"Graph references unknown variable(s): {', '.join(unknown)}")


def description_parser(path: str) -> GraphData:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Invalid path: {path}")

    with open(path, "r") as f:
        json_data = json.load(f)

    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    else:
        data = json_data

    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON: {data}")

    # Check Required fields
    required_fields = ["variables", "expert_edges", "required_edges", "forbidden_edges", "tiers"]
    for key in required_fields:
        if key not in data.keys():
            raise ValueError(f"Missing required field: {key}")

    # Check Possible fields
    possible_fields = ["meta", *required_fields]
    for key in data.keys():
        if key not in possible_fields:
            raise ValueError(f"Field {key} is invalid")

    parsed_variables_dict = parse_variables_dict(data["variables"])

    # Parsing Edges and Tiers into variable names
    expert = parse_edges_list(data["expert_edges"], parsed_variables_dict)
    required = parse_edges_list(data["required_edges"], parsed_variables_dict)
    forbidden = parse_edges_list(data["forbidden_edges"], parsed_variables_dict)

    # Check for cycles (expert edges only)
    if check_for_cycles(expert):
        raise ValueError("Cycle detected in expert_edges")

    tiers = parse_tiers(data["tiers"], parsed_variables_dict)

    graph = GraphData(
        variables_dict=parsed_variables_dict,
        exper_edges=expert,
        required_edges=required,
        forbidden_edges=forbidden,
        tiers=tiers,
    )
    _validate_graph_references(graph)

    return graph

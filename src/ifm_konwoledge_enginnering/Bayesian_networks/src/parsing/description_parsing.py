import json
from typing import Any, List
import os

from models.graph import GraphData
from models.variable import Variable
from parsing.util.check_for_cycles import check_for_cycles
from parsing.parse_variable import parse_variable, parse_variables_dict


def parse_edge(edge:List[str], variables_dict:dict[str, Variable]) -> tuple[Variable, Variable]:

    if not isinstance(edge, list):
        raise ValueError(f"Invalid edge format: {edge}")

    if len(edge) != 2:
        raise ValueError(f"Invalid edge: {edge}")

    for name in edge:
        if name not in variables_dict.keys():
            raise ValueError(f"Edge {edge} is not a variable")

    return variables_dict[edge[0]], variables_dict[edge[1]]

def parse_edges_list(edges_list:List[List[str]], variables_dict:dict[str, Variable]) -> list[tuple[Variable, Variable]]:
    if not isinstance(edges_list, list):
        raise ValueError(f"Invalid edges format: {edges_list}")

    edges = []
    for edge in edges_list:
        edges.append(parse_edge(edge, variables_dict))

    return edges

def parse_tiers(tiers_list:List[List[str]], variables_dict:dict[str, Variable]) -> list[List[Variable]]:

    if not isinstance(tiers_list, list):
        raise ValueError(f"Invalid tiers format: {tiers_list}")

    tiers = []
    for names in tiers_list:
        tier = []
        for name in names:
            if name not in variables_dict.keys():
                raise ValueError(f"Tier {name} is not a variable")
            tier.append(variables_dict[name])

        tiers.append(tier)

    return tiers

def description_parser(path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Invalid path: {path}")

    with open(path, "r") as f:
        json_data = json.load(f)

    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    elif isinstance(json_data, dict):
        try:
            data = json_data
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    else:
        raise ValueError(f"Invalid JSON: {json_data}")

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

    parsed_variables_dict = parse_variables_dict(data['variables'])

    # Parsing Edges
    # Check for cycles

    expert =  parse_edges_list(data["expert_edges"], parsed_variables_dict)
    required = parse_edges_list(data["required_edges"], parsed_variables_dict)
    forbidden = parse_edges_list(data["forbidden_edges"], parsed_variables_dict)

    if check_for_cycles(data["expert_edges"]):
        raise ValueError("Cycle detected in expert_edges")

    tiers = parse_tiers(data["tiers"], parsed_variables_dict)

    return GraphData(
        exper_edges=expert,
        required_edges=required,
        forbidden_edges=forbidden,
        tiers=tiers
    )



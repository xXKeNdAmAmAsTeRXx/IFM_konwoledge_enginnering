import json
from typing import Any, List

from models.graph import GraphData
from models.variable import Variable
from parsing.check_for_cycles import check_for_cycles


def parse_variable(name:str, variable_dict:dict[str, Any]) -> Variable:

    if variable_dict.get('state') is None:
        raise ValueError(f"Missing required field: {name}")

    states = variable_dict["states"]
    if not isinstance(states, List):
        raise ValueError(f"Invalid states: {states}")

    counter : int = 0
    for state in states:
        if isinstance(state, str):
           counter += 1
        else:
            raise ValueError(f"Invalid state: {state}")

    if counter < 2:
        raise ValueError(f"Variables should contain at least two states, Invalid States: {states}")

    return Variable(
        name=name,
        description=variable_dict.get('description', "not description provided"),
        states=variable_dict["states"],
    )

def parse_edge(edge:List[str], variables_dict:dict[str, Variable]) -> tuple[Variable, Variable]:
    if len(edge) != 2:
        raise ValueError(f"Invalid edge: {edge}")

    return variables_dict[edge[0]], variables_dict[edge[1]]

def parse_edges_list(edges_list:List[List[str]], variables_dict:dict[str, Variable]) -> list[tuple[Variable, Variable]]:
    edges = []
    for edge in edges_list:
        edges.append(parse_edge(edge, variables_dict))

    return edges

def parse_tiers(tiers_list:List[List[str]], variables_dict:dict[str, Variable]) -> list[List[Variable]]:
    tiers = []
    for names in tiers_list:
        tiers.append([variables_dict[name] for name in names])

    return tiers

def description_parser(path: str):
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

    not_parsed_variables_dict = data["variables"]
    parsed_variables_dict = {}
    for name, variable in not_parsed_variables_dict.items():
        parsed_variables_dict[name] = parse_variable(name, variable)

    # Parsing Edges

    # Check for cycles
    if check_for_cycles(data["expert_edges"]):
        raise ValueError("Cycle detected in expert_edges")

    expert =  parse_edges_list(data["expert_edges"], parsed_variables_dict)

    required = parse_edges_list(data["required_edges"], parsed_variables_dict)
    forbbiden = parse_edges_list(data["forbidden_edges"], parsed_variables_dict)

    tiers = parse_tiers(data["tiers"], parsed_variables_dict)

    return GraphData(
        exper_edges=expert,
        required_edges=required,
        forbidden_edges=forbbiden,
        tiers=tiers
    )



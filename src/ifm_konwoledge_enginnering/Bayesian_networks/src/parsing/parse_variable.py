from typing import Any, List, Dict

from models.variable import Variable

def parse_variable(name:str, variable_dict:dict[str, Any]) -> Variable:

    if 'states' not in variable_dict:
        raise ValueError(f"Variable {name} is missing states")

    if not isinstance(variable_dict['states'], list):
        raise ValueError(f"Invalid states: {variable_dict['states']}")

    states = variable_dict["states"]
    if not isinstance(states, List):
        raise ValueError(f"Invalid states: {states}")

    if len(states) < 2:
        raise ValueError(f"Variables should contain at least two states, Invalid States: {states}")

    state_occurrence = []
    for state in states:
        if isinstance(state, str):
           if state in state_occurrence: raise ValueError(f"State {state} is duplicated")
        else:
            raise ValueError(f"Invalid state: {state}")
        state_occurrence.append(state)

    return Variable(
        name=name,
        description=variable_dict.get('description', "not description provided"),
        states=variable_dict["states"],
    )

def parse_variables_dict(not_parsed_var_dict:Dict[str, Any]) -> Dict[str, Variable]:

    if not isinstance(not_parsed_var_dict, dict):
        raise ValueError(f"Invalid variables: {not_parsed_var_dict}")

    output = {}
    for name, variable in not_parsed_var_dict.items():
        output[name] = parse_variable(name, variable)

    return output


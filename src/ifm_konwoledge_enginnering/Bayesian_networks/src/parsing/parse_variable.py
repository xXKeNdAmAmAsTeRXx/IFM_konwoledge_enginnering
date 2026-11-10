from typing import Any, List, Dict

from models.variable import Variable

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

def parse_variables_dict(not_parsed_var_dict:Dict[str, Any]) -> Dict[str, Variable]:
    output = {}
    for name, variable in not_parsed_var_dict.items():
        output[name] = parse_variable(variable)

    return output


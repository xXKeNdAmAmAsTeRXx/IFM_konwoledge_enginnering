import re
from typing import Dict, List

from models.queries import Query, QueryType
from models.variable import Variable

QUERY_PATTERN = re.compile(r"^(P|MAP)\((.*)\)$")


def _split_names(value: str, section: str) -> List[str]:
    names = [name.strip() for name in value.split(",")]

    if not names or any(not name for name in names):
        raise ValueError(f"Invalid {section}: empty variable name")

    return names


def _resolve_variable(name: str, variables_dict: dict[str, Variable]) -> Variable:
    if name not in variables_dict:
        raise ValueError(f"Unknown variable: {name}")

    return variables_dict[name]


def _parse_targets(target_line: str, variables_dict: dict[str, Variable]) -> List[Variable]:
    target_names = _split_names(target_line, "query variables")
    if len(set(target_names)) != len(target_names):
        raise ValueError(f"Duplicate query variable: {target_line}")

    return [_resolve_variable(name, variables_dict) for name in target_names]


def _parse_evidence(
    evidence_line: str,
    target_names: set[str],
    variables_dict: dict[str, Variable],
) -> Dict[str, str]:
    evidence: Dict[str, str] = {}

    for assignment in evidence_line.split(","):
        assignment = assignment.strip()
        if not assignment:
            raise ValueError("Invalid evidence: empty assignment")

        if assignment.count("==") != 1:
            raise ValueError(f"Invalid evidence assignment: {assignment}")

        name, state = (part.strip() for part in assignment.split("=="))
        if not name or not state:
            raise ValueError(f"Invalid evidence assignment: {assignment}")

        variable = _resolve_variable(name, variables_dict)

        if state not in variable.states:
            raise ValueError(
                f"Invalid state: {state} for variable {name}; "
                f"expected one of {variable.states}"
            )

        if name in target_names:
            raise ValueError(
                f"Variable {name} cannot be both a query variable and evidence"
            )

        if name in evidence:
            raise ValueError(f"Duplicate evidence variable: {name}")

        evidence[name] = state

    return evidence


def parse_query(line: str, variables_dict: dict[str, Variable]) -> Query:
    if not isinstance(line, str):
        raise ValueError("Query must be a string")

    match = QUERY_PATTERN.fullmatch(line.strip())
    if match is None:
        raise ValueError(f"Invalid query: {line}")

    query_type_text, body = match.groups()
    if not body.strip():
        raise ValueError(f"Invalid query: {line}")

    sections = body.split("|")
    if len(sections) > 2:
        raise ValueError(f"Invalid query, multiple evidence separators: {line}")

    target_line = sections[0].strip()
    evidence_line = sections[1].strip() if len(sections) == 2 else ""

    if not target_line:
        raise ValueError(f"Invalid query, missing query variables: {line}")
    if len(sections) == 2 and not evidence_line:
        raise ValueError(f"Invalid query, missing evidence: {line}")

    query_type = QueryType.P if query_type_text == "P" else QueryType.MAP
    variables = _parse_targets(target_line, variables_dict)

    target_names = {variable.name for variable in variables}
    evidence = (
        _parse_evidence(evidence_line, target_names, variables_dict)
        if evidence_line
        else {}
    )

    return Query(
        query_type=query_type,
        variables=variables,
        evidence=evidence,
    )


def query_parser(path: str, variables_dict: dict[str, Variable]) -> List[Query]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    queries = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.split("#", 1)[0].strip()

        if not line:
            continue

        try:
            queries.append(parse_query(line, variables_dict))
        except ValueError as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error

    return queries

from typing import List

from models.queries import QueryType, Query
from models.variable import Variable
from parsing.parse_variable import parse_variable

def parse_query(line:str) -> Query:
    #TODO: Parse One Query
    type_and_line = line.strip(')').split("(")


    if type_and_line[0] == "P":
        query_type = QueryType.P
    elif type_and_line[0] == "MAP":
        query_type = QueryType.MAP
    else:
        raise Exception(f"Unknown query type: {type_and_line[0]}")

    var_line = type_and_line[1].split(' | ')[0]
    #TODO: Parse Variable

    evidence_line = type_and_line[1].split(' | ')[1]
    #TODO: Parse Evidence

    return Query(
        query_type=query_type,
        variables= None,
        evidence= None,
    )

def query_parser(path:str, variables_dict:dict[str, Variable]) -> List[Query]:
    with open(path, "r") as f:
        lines = f.readlines()

    queries = []
    for line in lines:
        line = line.strip()

        if line[0] == "#" or not line:
            continue

        queries.append(parse_query(line))

    return queries
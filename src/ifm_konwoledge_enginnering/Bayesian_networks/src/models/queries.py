from dataclasses import dataclass
from enum import Enum
from typing import List

from .variable import Variable

class QueryType(Enum):
    P = 1
    MAP = 1

@dataclass
class Query:
    query_type: QueryType
    variables: List[Variable]
    evidence: List[Variable]

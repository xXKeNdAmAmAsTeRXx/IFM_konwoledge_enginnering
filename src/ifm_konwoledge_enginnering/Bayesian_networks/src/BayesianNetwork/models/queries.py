from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from .variable import Variable

class QueryType(Enum):
    P = 1
    MAP = 2

@dataclass
class Query:
    query_type: QueryType
    variables: List[Variable]
    evidence: Dict[str, str]

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

class QueryType(Enum):
    P = 1
    MAP = 2

@dataclass
class Query:
    query_type: QueryType
    variables: List[str]
    evidence: Dict[str, str]

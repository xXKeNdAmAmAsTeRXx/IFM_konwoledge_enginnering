from dataclasses import dataclass
from typing import List, Dict
from .variable import Variable

@dataclass
class GraphData:
    variables_dict: Dict[str, Variable]
    exper_edges: List[tuple[str, str]]
    required_edges: List[tuple[str, str]]
    forbidden_edges: List[tuple[str, str]]
    tiers: List[List[str]]
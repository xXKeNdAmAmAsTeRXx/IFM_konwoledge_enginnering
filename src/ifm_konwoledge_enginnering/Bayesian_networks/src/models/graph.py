from dataclasses import dataclass
from typing import List
from .variable import Variable

@dataclass
class GraphData:
    exper_edges: List[tuple[Variable, Variable]]
    required_edges: List[tuple[Variable, Variable]]
    forbidden_edges: List[tuple[Variable, Variable]]
    tiers: List[List[Variable]]
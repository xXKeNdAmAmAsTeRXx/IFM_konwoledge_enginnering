from dataclasses import dataclass
from typing import List
from .variable import Variable


@dataclass
class GraphData:
    exper_edges: List[tuple[Variable]]
    required_edges: List[tuple[Variable]]
    forbidden_edges: List[tuple[Variable]]
    tiers: List[List[Variable]]
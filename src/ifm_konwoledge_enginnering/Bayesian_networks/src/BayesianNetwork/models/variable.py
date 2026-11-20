from dataclasses import dataclass
from typing import List

@dataclass
class Variable:
    name: str
    description: str
    states: List[str]

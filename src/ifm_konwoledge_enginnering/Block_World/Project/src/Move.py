import numpy as np
from dataclasses import dataclass

@dataclass
class Move:
    moving: int
    destination: int


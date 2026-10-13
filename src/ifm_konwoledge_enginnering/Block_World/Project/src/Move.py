import numpy as np
from dataclasses import dataclass

@dataclass
class Move:
    """Describe moving one block to a destination.

    Attributes:
        moving: ID of the block being moved.
        destination: ID of the destination block, or 0 for the table.
    """

    moving: int
    destination: int

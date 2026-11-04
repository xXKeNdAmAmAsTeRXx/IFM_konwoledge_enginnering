from typing import List

from ..Move import Move
from ..BlockState import BlockState
from ..World import World

def check_path(start:World, moves:List[Move]) -> bool:
    """
    Function to check if path is sequence of legal moves.
    """
    current = start
    for move in moves:
        try:
            current.update(move)
        except AssertionError:
            return False

    return True
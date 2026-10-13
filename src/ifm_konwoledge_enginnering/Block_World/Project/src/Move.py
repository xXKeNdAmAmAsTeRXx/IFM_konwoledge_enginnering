from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .BlockState import BlockState

@dataclass
class Move:
        """Describe moving one block to a destination.

            Attributes:
                moving: ID of the block being moved.
                destination: ID of the destination block, or 0 for the table.
            """

        moving: int
        destination: int


class PossibleMoves:
    """Describe possible moves.
        Attributes:
        """
    # Block from table (n,n)
    # Block to table (n,0)
    # Block to Block (n,n)

    @staticmethod
    def calculate_block_to_table(states:list[BlockState]) -> list[Move]:
        moves = []
        for state in states:
            if not state.on_table and state.clear:
               moves.append(Move(state.id, 0))

        return moves
    @staticmethod
    def calculate_block_from_table(states:list[BlockState]) -> list[Move]:
        moves = []
        for state in states:
            if state.on_table and state.clear:
                for destination in states:
                    if destination.id == state.id:
                        continue

                    if destination.clear:
                        moves.append(Move(state.id, destination.id))
        return moves
    
    #TODO: Drugi Warinat
    # @staticmethod
    # def calculate_block_to_block(States):
    #     pass


def calculate_all_possible_moves(states: list[BlockState]) -> list[Move]:
    return [*PossibleMoves.calculate_block_to_table(states), *PossibleMoves.calculate_block_from_table(states)]

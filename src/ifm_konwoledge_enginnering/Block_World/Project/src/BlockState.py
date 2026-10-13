from dataclasses import dataclass

from .Move import Move


@dataclass()
class BlockState():
    """Store the placement and status of a single block.

    Attributes:
        id: Block's ID.
        clear: Whether no other block is on this block.
        on: ID of the support block, or 0 for the table.
        on_table: Whether the block rests on the table.
    """

    id: int = -1
    clear: bool = False
    on: int = 0
    on_table: bool = False

    def update(self, move: Move):
        """Update this block's status using a move."""
        if self.id == move.moving:
            self.on = move.destination
            self.on_table = True if self.on == 0 else False
        elif self.id == move.destination:
            self.clear = False
        else:
            print("Move is not affecting this Block")

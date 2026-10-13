from dataclasses import dataclass

from .Move import Move


@dataclass()
class BlockState():
    id: int = -1
    clear: bool = False
    on: int = 0
    on_table: bool = False

    def update(self, move: Move):
        if self.id == move.moving:
            self.on = move.destination
            self.on_table = True if self.on == 0 else False
        elif self.id == move.destination:
            self.clear = False
        else:
            print("Move is not affecting this Block")
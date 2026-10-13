from dataclasses import dataclass


@dataclass()
class BlockState():
    id: int = -1
    clear: bool = False
    on: int = 0
    on_table: bool = False


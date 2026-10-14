# Block World Project

This project represents block arrangements, moves, and start/goal layouts.

## Placement format

A placement has one integer per block. The value at index `i` is the ID of the
block supporting block `i + 1`. `0` means the block rests on the table. For
example, `[0, 1, 0]` means block 1 and block 3 are on the table, and block 2 is
on block 1.

## Classes

### `Move`

Describes a block move.

- `moving`: ID of the block being moved.
- `destination`: ID of the block to move onto; `0` means the table.

### `BlockState`

Stores the placement and status of one block.

- `id`: Block ID.
- `clear`: Whether another block is on top of this block.
- `on`: Supporting block ID, or `0` for the table.
- `on_table`: Whether this block rests on the table.
- `update(move)`: Updates this block's state for a move.

### `World`

Stores a complete placement and the state of each block.

- `placement`: Array of support-block IDs, using `0` for the table.
- `states`: `BlockState` objects for the blocks in the placement.
- `__init__(placement)`: Validates a placement and builds its block states.
- `_check_if_placement_is_legal(placement)`: Checks block IDs, shared supports,
  and cycles; raises `ValueError` for an illegal arrangement.
- `_set_BlockState(placement, block_id)`: Builds one block's state from a
  placement.
- `update(move)`: Applies a move and refreshes the block states.

### `LoadStartAndGoal`

Loads the initial and target arrangements and stores each as a `World`.

- `start`: World for the initial arrangement.
- `goal`: World for the target arrangement.
- `__init__(start, goal)`: Creates the start and goal worlds from placements.
- `load_from_txt(path)`: Reads two placements from a text file and returns a
  `LoadStartAndGoal` object. Blank lines and lines beginning with `#` are
  ignored; each placement is a whitespace-separated list of integers.

## Tests

Run the project tests from the repository root:

```bash
uv run pytest src/ifm_konwoledge_enginnering/Block_World/Project/test
```

import numpy as np

from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World


def test_legal_moves_between_table_and_blocks():
    # Block 2 is on block 1; block 3 is on the table. Blocks 2 and 3 are clear.
    world = World(np.array([0, 1, 0], dtype=np.int32))
    original_placement = world.placement.copy()

    moves = world.legal_moves()

    assert all(isinstance(move, Move) for move in moves)
    assert {(move.moving, move.destination) for move in moves} == {
        (2, 0),  # Move block 2 to the table.
        (3, 2),  # Move block 3 onto clear block 2.
    }
    np.testing.assert_array_equal(world.placement, original_placement)

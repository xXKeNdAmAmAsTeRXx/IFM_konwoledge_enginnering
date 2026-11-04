import numpy as np

from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World
from ifm_konwoledge_enginnering.Block_World.Project.src.search_path.bfs import bfs


def make_world(placement):
    return World(np.asarray(placement, dtype=np.int32))


def test_bfs_returns_shortest_path_and_respects_extended_moves():
    start = make_world([0, 1, 0])
    goal = make_world([0, 3, 0])
    original_start = start.placement.copy()
    original_goal = goal.placement.copy()

    regular_path = bfs(start, goal)
    extended_path = bfs(start, goal, extended=True)

    # Without direct block-to-block moves, block 2 must be moved via the table.
    assert len(regular_path) == 2
    # The extended rules permit moving block 2 directly onto block 3.
    assert extended_path == [Move(moving=2, destination=3)]

    current = make_world(original_start)
    for move in extended_path:
        assert move in current.legal_moves(extended=True)
        current.update(move)

    np.testing.assert_array_equal(current.placement, original_goal)
    np.testing.assert_array_equal(start.placement, original_start)
    np.testing.assert_array_equal(goal.placement, original_goal)

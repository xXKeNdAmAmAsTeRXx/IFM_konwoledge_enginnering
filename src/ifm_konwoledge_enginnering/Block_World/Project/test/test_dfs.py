import numpy as np
import pytest

from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World
from ifm_konwoledge_enginnering.Block_World.Project.src.search_path.dfs import dfs


def make_world(placement):
    return World(np.asarray(placement, dtype=np.int32))


def test_dfs_returns_empty_path_when_start_equals_goal():
    start = make_world([0, 1, 0])
    goal = make_world([0, 1, 0])

    assert dfs(start, goal) == []


def test_dfs_finds_a_legal_path_to_goal_without_mutating_inputs():
    start = make_world([0, 1, 0])
    goal = make_world([0, 0, 1])
    original_start = start.placement.copy()
    original_goal = goal.placement.copy()

    path = dfs(start, goal)

    assert isinstance(path, list)
    assert path
    assert all(isinstance(move, Move) for move in path)

    current = make_world(original_start)
    seen_placements = {tuple(current.placement.tolist())}
    for move in path:
        assert move in current.legal_moves()
        current.update(move)
        placement_key = tuple(current.placement.tolist())
        assert placement_key not in seen_placements
        seen_placements.add(placement_key)

    np.testing.assert_array_equal(current.placement, original_goal)
    np.testing.assert_array_equal(start.placement, original_start)
    np.testing.assert_array_equal(goal.placement, original_goal)


def test_dfs_rejects_start_and_goal_with_different_block_counts():
    start = make_world([0, 0])
    goal = make_world([0, 0, 0])

    with pytest.raises(ValueError, match="same number|same size|different sizes"):
        dfs(start, goal)


def test_dfs_reports_search_limit_exceeded():
    start = make_world([0, 1, 0])
    goal = make_world([0, 0, 1])

    with pytest.raises(RuntimeError, match="limit"):
        dfs(start, goal, max_visited_notes=0)

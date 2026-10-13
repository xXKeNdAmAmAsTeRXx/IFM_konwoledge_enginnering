import numpy as np
from ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState

def test_all_possible_movements_returns_numpy_arrays():
    current = np.array([0, 0, 1])
    goal = np.array([0, 1, 2])
    state = BlockState(current, goal)

    movements = state.all_possible_movements()

    assert isinstance(movements, list)
    assert len(movements) > 0
    assert all(isinstance(move, np.ndarray) for move in movements)


def test_all_possible_movements_does_not_modify_current_state():
    current = np.array([0, 0, 1])
    goal = np.array([0, 1, 2])
    state = BlockState(current, goal)
    original = state.start.copy()

    state.all_possible_movements()

    np.testing.assert_array_equal(state.start, original)


def test_all_possible_movements_returns_legal_states():
    current = np.array([0, 0, 1])
    goal = np.array([0, 1, 2])
    state = BlockState(current, goal)

    movements = state.all_possible_movements()

    for movement in movements:
        assert BlockState._check_if_placement_is_legal(movement) is True

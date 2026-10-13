import numpy as np
import pytest

from ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState
from ifm_konwoledge_enginnering.Block_World.Project.src.dfs import dfs


def make_state(current, goal):
    """Pomocniczo tworzy obiekt BlockState z list wejściowych."""
    return BlockState(
        current=np.array(current, dtype=np.int32),
        goal=np.array(goal, dtype=np.int32),
    )


def assert_valid_path(path, start, goal):
    """
    Sprawdza, czy ścieżka:
    - zaczyna się w stanie początkowym,
    - kończy się w stanie docelowym,
    - zawiera wyłącznie legalne stany.
    """
    assert path is not None
    assert len(path) >= 1

    np.testing.assert_array_equal(path[0], start)
    np.testing.assert_array_equal(path[-1], goal)

    for state in path:
        assert BlockState._check_if_placement_is_legal(state)


# --------------------------------------------------
# 1. Stan początkowy jest stanem docelowym
# --------------------------------------------------

def test_dfs_when_start_equals_goal():
    state = make_state(
        current=[0, 1, 2],
        goal=[0, 1, 2],
    )

    path = dfs(state)

    assert path is not None
    assert len(path) == 1
    np.testing.assert_array_equal(path[0], state.start)


# --------------------------------------------------
# 2. DFS znajduje rozwiązanie
# --------------------------------------------------

def test_dfs_finds_solution():
    state = make_state(
        current=[0, 0],
        goal=[0, 1],
    )

    path = dfs(state)

    assert_valid_path(path, state.start, state.goal)


# --------------------------------------------------
# 3. Każdy kolejny stan wynika z legalnego ruchu
# --------------------------------------------------

def test_dfs_returns_path_with_legal_transitions():
    state = make_state(
        current=[0, 0, 0],
        goal=[0, 1, 2],
    )

    path = dfs(state)

    assert_valid_path(path, state.start, state.goal)

    for current_state, next_state in zip(path, path[1:]):
        possible_movements = BlockState(
            current=current_state.copy(),
            goal=state.goal.copy(),
        ).all_possible_movements()

        assert any(
            np.array_equal(next_state, movement)
            for movement in possible_movements
        ), (
            f"Nielegalne przejście: "
            f"{current_state} -> {next_state}"
        )


# --------------------------------------------------
# 4. Ścieżka nie zawiera powtórzonych stanów
# --------------------------------------------------

def test_dfs_path_does_not_repeat_states():
    state = make_state(
        current=[0, 0, 0],
        goal=[0, 1, 2],
    )

    path = dfs(state)

    assert path is not None

    path_as_tuples = [tuple(map(int, s)) for s in path]

    assert len(path_as_tuples) == len(set(path_as_tuples))


# --------------------------------------------------
# 5. DFS nie modyfikuje stanu wejściowego
# --------------------------------------------------

def test_dfs_does_not_modify_input_state():
    state = make_state(
        current=[0, 0, 0],
        goal=[0, 1, 2],
    )

    original_current = state.start.copy()
    original_goal = state.goal.copy()

    dfs(state)

    np.testing.assert_array_equal(state.start, original_current)
    np.testing.assert_array_equal(state.goal, original_goal)


# --------------------------------------------------
# 6. DFS zwraca listę tablic NumPy
# --------------------------------------------------

def test_dfs_returns_list_of_numpy_arrays():
    state = make_state(
        current=[0, 0],
        goal=[0, 1],
    )

    path = dfs(state)

    assert isinstance(path, list)

    for element in path:
        assert isinstance(element, np.ndarray)


# --------------------------------------------------
# 7. Rozwiązanie zawiera stan początkowy i docelowy
# --------------------------------------------------

def test_dfs_path_includes_start_and_goal():
    state = make_state(
        current=[0, 0, 0],
        goal=[0, 1, 2],
    )

    path = dfs(state)

    assert path is not None
    np.testing.assert_array_equal(path[0], state.start)
    np.testing.assert_array_equal(path[-1], state.goal)


# --------------------------------------------------
# 8. Niepoprawny stan nie powinien zostać zaakceptowany
# --------------------------------------------------

def test_dfs_rejects_illegal_initial_state():
    # Pierwszy klocek leży na samym sobie.
    state = BlockState.__new__(BlockState)
    state.start = np.array([1, 0], dtype=np.int32)
    state.goal = np.array([0, 1], dtype=np.int32)

    with pytest.raises(ValueError):
        dfs(state)


def test_dfs_rejects_illegal_goal_state():
    # Stan docelowy zawiera samopodparcie.
    state = BlockState.__new__(BlockState)
    state.start = np.array([0, 1], dtype=np.int32)
    state.goal = np.array([1, 0], dtype=np.int32)

    with pytest.raises(ValueError):
        dfs(state)


# --------------------------------------------------
# 9. Stany o różnych rozmiarach są odrzucane
# --------------------------------------------------

def test_dfs_rejects_different_state_sizes():
    state = BlockState.__new__(BlockState)
    state.start = np.array([0, 0], dtype=np.int32)
    state.goal = np.array([0, 1, 2], dtype=np.int32)

    with pytest.raises(ValueError):
        dfs(state)

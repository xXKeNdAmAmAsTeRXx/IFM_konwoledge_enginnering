import numpy as np
import pytest
from src.ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState

def test_valid_state():
    """Poprawny układ powinien zostać zaakceptowany."""
    state = np.array([0, 1, 0, 2, 3], dtype=np.int32)

    assert BlockState._check_if_state_is_legal(state) is True


def test_block_cannot_rest_on_itself():
    """Klocek nie może leżeć sam na sobie."""
    state = np.array([1, 0], dtype=np.int32)

    with pytest.raises(ValueError):
        BlockState._check_if_state_is_legal(state)


def test_block_cannot_rest_on_nonexistent_block():
    """Klocek nie może leżeć na nieistniejącym klocku."""
    state_1 = np.array([0, 3], dtype=np.int32)
    state_2 = np.array([-1, 0], dtype=np.int32)

    with pytest.raises(ValueError):
        BlockState._check_if_state_is_legal(state_1)

    with pytest.raises(ValueError):
        BlockState._check_if_state_is_legal(state_2)

def test_only_one_block_can_rest_on_another():
    """Na jednym klocku nie mogą leżeć dwa inne klocki."""
    state = np.array([0, 1, 1], dtype=np.int32)

    with pytest.raises(ValueError):
        BlockState._check_if_state_is_legal(state)

def test_state_cannot_contain_cycle():
    """Układ nie może zawierać cyklu."""
    state = np.array([0,3,2], dtype=np.int32)

    with pytest.raises(ValueError):
        BlockState._check_if_state_is_legal(state)
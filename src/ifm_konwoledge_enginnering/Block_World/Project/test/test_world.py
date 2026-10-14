import numpy as np
import pytest

from ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState
from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World


def test_valid_placement_is_accepted():
    placement = np.array([0, 1, 0], dtype=np.int32)

    assert World._check_if_placement_is_legal(placement) is True


@pytest.mark.parametrize(
    "placement",
    [
        np.array([1, 0]),       # A block cannot support itself.
        np.array([0, 3]),       # Block 3 does not exist.
        np.array([0, 1, 1]),    # Two blocks cannot share the same support.
        np.array([2, 1]),       # Cyclic support.
    ],
)
def test_illegal_placements_are_rejected(placement):
    with pytest.raises(ValueError):
        World._check_if_placement_is_legal(placement)


def test_constructor_builds_one_state_per_block():
    world = World(np.array([0, 1, 0], dtype=np.int32))

    assert world.placement.tolist() == [0, 1, 0]
    assert len(world.states) == 3
    assert all(isinstance(state, BlockState) for state in world.states)
    assert [(state.id, state.on, state.on_table, state.clear) for state in world.states] == [
        (1, 0, True, False),
        (2, 1, False, True),
        (3, 0, True, True),
    ]


def test_update_moves_a_clear_block_and_updates_world_states():
    world = World(np.array([0, 1, 0], dtype=np.int32))

    world.update(Move(moving=2, destination=3))

    assert world.placement.tolist() == [0, 3, 0]
    assert world.states[1].on == 3
    assert world.states[1].on_table is False
    assert world.states[0].clear is True
    assert world.states[2].clear is False


def test_illegal_move_does_not_change_world():
    world = World(np.array([0, 0, 1], dtype=np.int32))
    original_placement = world.placement.copy()

    with pytest.raises((AssertionError, ValueError)):
        world.update(Move(moving=2, destination=1))

    np.testing.assert_array_equal(world.placement, original_placement)

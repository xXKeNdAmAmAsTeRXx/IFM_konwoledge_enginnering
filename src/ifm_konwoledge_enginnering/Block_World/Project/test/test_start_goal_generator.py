import numpy as np
import pytest

from ifm_konwoledge_enginnering.Block_World.Project.src.LoadStartAndGoal import (
    LoadStartAndGoal,
)
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World
from ifm_konwoledge_enginnering.Block_World.Project.src.state_generator import (
    start_goal_generator,
)


@pytest.mark.parametrize("n_blocks", [3, 7, 15])
def test_generates_start_and_goal_worlds_with_requested_size(n_blocks):
    result = start_goal_generator(n_blocks, seed=123)

    assert isinstance(result, LoadStartAndGoal)
    assert isinstance(result.start, World)
    assert isinstance(result.goal, World)
    assert len(result.start.placement) == n_blocks
    assert len(result.goal.placement) == n_blocks


@pytest.mark.parametrize("n_blocks", [3, 7, 15])
def test_generated_start_and_goal_placements_are_legal(n_blocks):
    result = start_goal_generator(n_blocks, seed=123)

    assert World._check_if_placement_is_legal(result.start.placement)
    assert World._check_if_placement_is_legal(result.goal.placement)


def test_generator_is_reproducible_for_a_given_seed():
    first = start_goal_generator(8, seed=2026)
    second = start_goal_generator(8, seed=2026)

    np.testing.assert_array_equal(first.start.placement, second.start.placement)
    np.testing.assert_array_equal(first.goal.placement, second.goal.placement)


@pytest.mark.parametrize("n_blocks", [0, -1])
def test_generator_rejects_nonpositive_block_counts(n_blocks):
    with pytest.raises(ValueError, match="block|positive|N"):
        start_goal_generator(n_blocks, seed=123)

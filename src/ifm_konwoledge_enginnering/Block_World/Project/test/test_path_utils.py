import numpy as np

from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move
from ifm_konwoledge_enginnering.Block_World.Project.src.World import World
from ifm_konwoledge_enginnering.Block_World.Project.src.utils.path_utils import check_path


def make_world(placement):
    return World(np.asarray(placement, dtype=np.int32))


def test_check_path_returns_true_for_legal_moves():
    start = make_world([0, 1])

    assert check_path(start, [Move(moving=2, destination=0)]) is True


def test_check_path_returns_false_for_illegal_move():
    start = make_world([0, 1])

    # Block 1 is not clear because block 2 is on it.
    assert check_path(start, [Move(moving=1, destination=0)]) is False
